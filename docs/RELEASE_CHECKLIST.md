# Release Checklist

Before tagging a release:

```bash
python -m compileall src tests
python -m unittest discover -s tests
PYTHONPATH=src python -m agent_evidence_board.cli demo --db work/release-smoke.db
PYTHONPATH=src python -m agent_evidence_board.cli gate-card examples/sample_intelligence_card.json --allow-warnings
```

Manual checks:

- README quickstart still works from a clean clone.
- No secrets, cookies, private exports, or generated databases are staged.
- `CHANGELOG.md` has an entry for the release.
- Examples use synthetic or public-safe data.
- New gate behavior has negative tests.
- `SECURITY.md` and threat model still describe current behavior.

Recommended tag format:

```bash
git tag v0.1.0
```
