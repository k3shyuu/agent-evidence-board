from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_evidence_board.board import add_evidence_card, connect, ensure_topic
from agent_evidence_board.cli import main
from agent_evidence_board.capture import CaptureResult


ROOT = Path(__file__).resolve().parents[1]


class BoardCliTests(unittest.TestCase):
    def test_export_jsonl_writes_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "board.db"
            out = Path(tmp) / "cards.jsonl"
            card = json.loads((ROOT / "examples" / "sample_intelligence_card.json").read_text(encoding="utf-8"))
            conn = connect(db)
            try:
                topic_id = ensure_topic(conn, "demo")
                add_evidence_card(conn, topic_id, card["title"], card, created_by="test")
            finally:
                conn.close()

            code = main(["export-jsonl", "evidence_cards", "--db", str(db), "--out", str(out)])
            self.assertEqual(code, 0)
            lines = out.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            exported = json.loads(lines[0])
            self.assertEqual(exported["title"], card["title"])
            self.assertIn("card_json", exported)

    def test_public_capture_fixture_shape(self) -> None:
        data = json.loads((ROOT / "tests" / "fixtures" / "example_dot_com_capture.json").read_text(encoding="utf-8"))
        result = CaptureResult(**data)
        self.assertEqual(result.url, "https://example.com")
        self.assertEqual(result.access_status, "full")
        self.assertIn("Example Domain", result.text)


if __name__ == "__main__":
    unittest.main()
