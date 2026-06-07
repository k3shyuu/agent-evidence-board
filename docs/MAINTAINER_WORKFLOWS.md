# Maintainer Workflows

Agent Evidence Board is useful in ordinary OSS maintenance work, not only in autonomous research bots.

## Pull Request Review

Use the gate when a pull request adds an agent-generated report, release note, security note, or research artifact.

Recommended review flow:

1. Ask the contributor to include an evidence card JSON file.
2. Run:

   ```bash
   aeb gate-card path/to/card.json --allow-warnings
   ```

3. If the gate blocks, ask for a source fix rather than editing the final prose directly.
4. Review the changed evidence card and the final publication artifact together.

This keeps review focused on verifiable claims: source access, freshness, missing checks, and unsafe wording.

## Issue Triage

Use issues to track failure modes that the gate should handle.

Good issue examples:

- unsourced claim passed when it should have blocked;
- X/Twitter preview-only source treated as full text;
- stale social post was not marked stale;
- secret-like value detector missed a realistic pattern;
- a valid card was blocked too aggressively.

Each issue should include a synthetic or public-safe card. Do not paste secrets, cookies, private exports, or private chat logs.

## Release Management

Before a release, run:

```bash
python -m compileall src tests
python -m unittest discover -s tests
PYTHONPATH=src python -m agent_evidence_board.cli demo --db work/release-smoke.db
PYTHONPATH=src python -m agent_evidence_board.cli gate-card examples/sample_intelligence_card.json --allow-warnings
PYTHONPATH=src python -m agent_evidence_board.cli export-jsonl evidence_cards --db work/release-smoke.db --out work/release-cards.jsonl
```

Then check:

- new gate rules have negative tests;
- docs describe new behavior;
- examples remain public-safe;
- `CHANGELOG.md` is updated;
- no generated databases or local `work/` artifacts are committed.

## Codex/API Credit Use

Credits should support maintenance, not vanity usage:

- generate tests for new failure modes;
- review pull requests that change gates or source capture;
- draft docs from code changes;
- build small reproducible fixtures;
- triage issues into cards, blockers, and tests;
- check release notes against merged changes.

Do not use credits for unrelated products, fake traffic, synthetic adoption metrics, or hidden private data processing.
