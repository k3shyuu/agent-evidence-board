# Agent Instructions

This repository is public-safe. Do not add secrets, cookies, private chat exports, bot tokens, private SSH paths, production configs, or real user data.

## Project Goal

Agent Evidence Board gives AI research agents a structured evidence ledger and publication gate. The goal is to reduce unsupported public claims, stale source citations, preview-only X/Twitter mistakes, secret leakage, and unsafe guarantee/trading wording.

## Workflows

Run checks before reporting a change:

```bash
python -m compileall src tests
python -m unittest discover -s tests
```

For CLI smoke tests:

```bash
PYTHONPATH=src python -m agent_evidence_board.cli demo --db work/demo.db
PYTHONPATH=src python -m agent_evidence_board.cli gate-card examples/sample_intelligence_card.json --allow-warnings
```

On Windows PowerShell:

```powershell
$env:PYTHONPATH="src"
python -m agent_evidence_board.cli demo --db work\demo.db
```

## Contribution Rules

- Keep examples synthetic or explicitly public.
- Add negative tests for new gate rules.
- Prefer deterministic validation over model-only judgment.
- Mark weak assumptions and unknowns explicitly.
- Do not claim the project eliminates hallucinations; say it helps reduce publication risk.
- Keep source capture bounded and respectful. Do not add login bypasses, paywall bypasses, spam automation, or scraping that violates source boundaries.

## Evidence Card Rules

Every publishable card should separate:

- facts;
- weak signals;
- assumptions;
- risks;
- unknowns;
- concrete source references.

The gate should block when the source text is missing, preview-only, stale, contradictory, or secret-like.
