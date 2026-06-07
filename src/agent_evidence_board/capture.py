from __future__ import annotations

import html
import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any


X_STATUS_RE = re.compile(r"https?://(?:x|twitter)\.com/([^/\s]+)/status/(\d+)", re.I)


@dataclass
class CaptureResult:
    url: str
    access_status: str
    capture_method: str
    title: str
    text: str
    author: str = ""
    created_at: str = ""
    media_urls: list[str] | None = None
    failure_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["media_urls"] = self.media_urls or []
        return data


def fetch_text(url: str, timeout_sec: int = 15, accept: str = "text/plain,text/html,*/*") -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; agent-evidence-board/0.1)",
            "Accept": accept,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        return resp.read(2_000_000).decode("utf-8", errors="replace")


def fetch_json(url: str, timeout_sec: int = 15) -> dict[str, Any]:
    return json.loads(fetch_text(url, timeout_sec=timeout_sec, accept="application/json,*/*"))


def strip_html(value: str) -> str:
    value = re.sub(r"<script\b[^>]*>.*?</script>", "", value, flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", "", value, flags=re.I | re.S)
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"</p\s*>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return "\n".join(line.strip() for line in value.splitlines() if line.strip())


def unique(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def x_public_api_urls(url: str) -> list[tuple[str, str]]:
    match = X_STATUS_RE.search(url)
    if not match:
        return []
    status_id = match.group(2)
    return [
        ("api.fxtwitter.com", f"https://api.fxtwitter.com/status/{status_id}"),
        ("api.vxtwitter.com", f"https://api.vxtwitter.com/Twitter/status/{status_id}"),
    ]


def capture_fxtwitter(original_url: str, data: dict[str, Any]) -> CaptureResult | None:
    tweet = data.get("tweet") if isinstance(data.get("tweet"), dict) else None
    if not tweet:
        return None
    text = str(tweet.get("text") or "").strip()
    if not text:
        return None
    author = tweet.get("author") if isinstance(tweet.get("author"), dict) else {}
    media_urls: list[Any] = []
    media = tweet.get("media")
    if isinstance(media, dict):
        for key in ("all", "photos", "videos", "animated_gifs"):
            items = media.get(key)
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        media_urls.extend([item.get("url"), item.get("thumbnail_url"), item.get("media_url_https")])
    return CaptureResult(
        url=original_url,
        access_status="full",
        capture_method="api.fxtwitter.com",
        title=text.splitlines()[0][:120],
        text=text,
        author=str(author.get("screen_name") or author.get("name") or ""),
        created_at=str(tweet.get("created_at") or ""),
        media_urls=unique(media_urls),
    )


def capture_vxtwitter(original_url: str, data: dict[str, Any]) -> CaptureResult | None:
    text = str(data.get("text") or "").strip()
    if not text:
        return None
    media_urls: list[Any] = []
    if isinstance(data.get("mediaURLs"), list):
        media_urls.extend(data["mediaURLs"])
    if isinstance(data.get("media_extended"), list):
        for item in data["media_extended"]:
            if isinstance(item, dict):
                media_urls.extend([item.get("url"), item.get("thumbnail_url")])
    return CaptureResult(
        url=original_url,
        access_status="full",
        capture_method="api.vxtwitter.com",
        title=text.splitlines()[0][:120],
        text=text,
        author=str(data.get("user_screen_name") or data.get("user_name") or ""),
        created_at=str(data.get("date") or ""),
        media_urls=unique(media_urls),
    )


def jina_urls(url: str) -> list[str]:
    return [
        "https://r.jina.ai/http://r.jina.ai/http://" + url,
        "https://r.jina.ai/http://" + url,
    ]


def capture_jina(original_url: str, markdown: str) -> CaptureResult | None:
    text = markdown.strip()
    if not text or "JavaScript is not available" in text[:1000]:
        return None
    title = ""
    for line in text.splitlines():
        line = line.strip("# ").strip()
        if line:
            title = line[:120]
            break
    return CaptureResult(
        url=original_url,
        access_status="full",
        capture_method="jina_reader",
        title=title or original_url,
        text=text[:20000],
    )


def capture_url(url: str, timeout_sec: int = 15) -> CaptureResult:
    url = url.strip()
    if X_STATUS_RE.search(url):
        for method, api_url in x_public_api_urls(url):
            try:
                data = fetch_json(api_url, timeout_sec=timeout_sec)
                result = capture_fxtwitter(url, data) if method == "api.fxtwitter.com" else capture_vxtwitter(url, data)
                if result:
                    return result
            except Exception:
                continue
        for reader_url in jina_urls(url):
            try:
                result = capture_jina(url, fetch_text(reader_url, timeout_sec=timeout_sec))
                if result:
                    return result
            except Exception:
                continue
        return CaptureResult(
            url=url,
            access_status="needs_source_text",
            capture_method="x_public_capture_failed",
            title=url,
            text="",
            failure_reason="Could not retrieve full X post text through public endpoints.",
        )

    try:
        raw = fetch_text(url, timeout_sec=timeout_sec)
        text = strip_html(raw) if "<html" in raw[:1000].lower() else raw.strip()
        return CaptureResult(
            url=url,
            access_status="full" if text else "empty",
            capture_method="direct_http",
            title=url,
            text=text[:20000],
        )
    except Exception as exc:
        encoded = urllib.parse.quote(url, safe=":/?&=%#")
        try:
            result = capture_jina(url, fetch_text("https://r.jina.ai/http://" + encoded, timeout_sec=timeout_sec))
            if result:
                return result
        except Exception:
            pass
        return CaptureResult(
            url=url,
            access_status="inaccessible",
            capture_method="direct_http",
            title=url,
            text="",
            failure_reason=str(exc),
        )
