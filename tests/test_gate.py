from __future__ import annotations

import json
import unittest
from pathlib import Path

from agent_evidence_board.gate import gate_card, validate_card


ROOT = Path(__file__).resolve().parents[1]


class GateTests(unittest.TestCase):
    def test_sample_card_passes_with_warnings_allowed(self) -> None:
        card = json.loads((ROOT / "examples" / "sample_intelligence_card.json").read_text(encoding="utf-8"))
        result = gate_card(card, allow_warnings=True)
        self.assertTrue(result["ok"], result)

    def test_missing_source_blocks(self) -> None:
        card = json.loads((ROOT / "examples" / "blocked_card_missing_source.json").read_text(encoding="utf-8"))
        result = gate_card(card, allow_warnings=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("unknown source_id" in item for item in result["blockers"]))
        self.assertTrue(any("X source is not full-access" in item for item in result["blockers"]))

    def test_secret_like_value_blocks(self) -> None:
        card = json.loads((ROOT / "examples" / "sample_intelligence_card.json").read_text(encoding="utf-8"))
        card["claims"][0]["claim"] = "Leaked token: api_key=abcdefghijklmnopqrstuvwxyz123456"
        result = gate_card(card, allow_warnings=True)
        self.assertFalse(result["ok"])
        self.assertIn("secret-like value detected", result["blockers"])

    def test_guarantee_language_blocks(self) -> None:
        card = json.loads((ROOT / "examples" / "sample_intelligence_card.json").read_text(encoding="utf-8"))
        card["claims"][0]["claim"] = "This is a guaranteed 100x buy now setup."
        result = gate_card(card, allow_warnings=True)
        self.assertFalse(result["ok"])
        self.assertIn("guarantee/trading command wording detected", result["blockers"])

    def test_preview_x_source_blocks_even_with_matching_source(self) -> None:
        card = json.loads((ROOT / "examples" / "sample_intelligence_card.json").read_text(encoding="utf-8"))
        card["sources_checked"][0]["type"] = "x"
        card["sources_checked"][0]["url"] = "https://x.com/example/status/123"
        card["sources_checked"][0]["access"] = "preview"
        result = gate_card(card, allow_warnings=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("X source is not full-access" in item for item in result["blockers"]))

    def test_stale_x_source_blocks(self) -> None:
        card = json.loads((ROOT / "examples" / "sample_intelligence_card.json").read_text(encoding="utf-8"))
        card["sources_checked"][0]["type"] = "x"
        card["sources_checked"][0]["url"] = "https://x.com/example/status/123"
        card["sources_checked"][0]["access"] = "full"
        card["sources_checked"][0]["created_at"] = "2020-01-01T00:00:00Z"
        result = gate_card(card, allow_warnings=True, max_x_age_days=7)
        self.assertFalse(result["ok"])
        self.assertTrue(any("stale X source" in item for item in result["blockers"]))

    def test_reviewer_block_blocks(self) -> None:
        card = json.loads((ROOT / "examples" / "sample_intelligence_card.json").read_text(encoding="utf-8"))
        card["reviews"] = [{"reviewer": "red_team", "verdict": "block", "confidence": "high"}]
        result = gate_card(card, allow_warnings=True)
        self.assertFalse(result["ok"])
        self.assertTrue(any("reviewer blocked publication" in item for item in result["blockers"]))

    def test_validator_requires_claims(self) -> None:
        result = validate_card({"title": "x", "sources_checked": []})
        self.assertFalse(result["ok"])
        self.assertTrue(any("claims" in item for item in result["errors"]))


if __name__ == "__main__":
    unittest.main()
