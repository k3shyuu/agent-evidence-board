from __future__ import annotations

import datetime as dt
import email.utils
import json
import re
from pathlib import Path
from typing import Any


TRADE_RE = re.compile(
    r"\b(buy now|sell now|guaranteed|risk[- ]?free|100x|must buy|sure profit|"
    r"без риска|гарант|точно выраст|иксы гарант)\b",
    re.I,
)
SECRET_RE = re.compile(
    r"(?:bearer\s+[a-z0-9._-]{20,}|"
    r"(?:api[_-]?key|token|secret|private[_-]?key|telegram[_-]?bot[_-]?token)\s*[:=]\s*[a-z0-9_./:+-]{16,}|"
    r"\b[A-Za-z0-9_-]{32,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b)",
    re.I,
)


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def source_ids(card: dict[str, Any]) -> set[str]:
    sources = card.get("sources_checked")
    if not isinstance(sources, list):
        return set()
    return {str(src.get("source_id")) for src in sources if isinstance(src, dict) and src.get("source_id")}


def validate_card(card: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    if not card.get("title"):
        errors.append("missing title")
    if not isinstance(card.get("claims"), list) or not card["claims"]:
        errors.append("claims must be a non-empty list")
    if not isinstance(card.get("sources_checked"), list) or not card["sources_checked"]:
        errors.append("sources_checked must be a non-empty list")

    known_sources = source_ids(card)
    for index, claim in enumerate(card.get("claims") or [], start=1):
        if not isinstance(claim, dict):
            errors.append(f"claims[{index}] is not an object")
            continue
        if not claim.get("claim"):
            errors.append(f"claims[{index}] missing claim")
        claim_source = str(claim.get("source_id") or "")
        if not claim_source:
            errors.append(f"claims[{index}] missing source_id")
        elif claim_source not in known_sources:
            errors.append(f"claims[{index}] references unknown source_id={claim_source}")
        if str(claim.get("confidence") or "unknown") == "unknown":
            warnings.append(f"claims[{index}] confidence is unknown")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def parse_date(value: Any) -> dt.datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = email.utils.parsedate_to_datetime(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.UTC)
        return parsed.astimezone(dt.UTC)
    except Exception:
        pass
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=dt.UTC)
        return parsed.astimezone(dt.UTC)
    except Exception:
        return None


def gate_card(card: dict[str, Any], allow_warnings: bool = False, max_x_age_days: int = 7) -> dict[str, Any]:
    validation = validate_card(card)
    blockers = list(validation["errors"])
    warnings = list(validation["warnings"])
    blob = json.dumps(card, ensure_ascii=False)

    if SECRET_RE.search(blob):
        blockers.append("secret-like value detected")
    if TRADE_RE.search(blob):
        blockers.append("guarantee/trading command wording detected")

    for source in card.get("sources_checked") or []:
        if not isinstance(source, dict):
            continue
        source_type = str(source.get("type") or "").lower()
        access = str(source.get("access") or "").lower()
        if source_type in {"x", "twitter"} and access not in {"full", "text", "retrieved", "provided_by_user"}:
            blockers.append(f"X source is not full-access: {source.get('url') or source.get('source_id')}")
        created_at = parse_date(source.get("created_at"))
        if source_type in {"x", "twitter"} and created_at is not None and max_x_age_days > 0:
            age_days = (dt.datetime.now(dt.UTC) - created_at).total_seconds() / 86400
            if age_days > max_x_age_days:
                blockers.append(f"stale X source: {source.get('url') or source.get('source_id')} is {age_days:.1f} days old")

    for review in card.get("reviews") or []:
        if isinstance(review, dict) and str(review.get("verdict") or "").lower() in {"block", "reject"}:
            blockers.append(f"reviewer blocked publication: {review.get('reviewer') or 'unknown'}")

    ok = not blockers and (allow_warnings or not warnings)
    return {
        "ok": ok,
        "decision": "allow_publish" if ok else "block_publish",
        "blockers": blockers,
        "warnings": warnings,
        "validation": validation,
    }


def gate_file(path: str | Path, allow_warnings: bool = False, max_x_age_days: int = 7) -> dict[str, Any]:
    return gate_card(load_json(path), allow_warnings=allow_warnings, max_x_age_days=max_x_age_days)
