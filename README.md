# Agent Evidence Board

Agent Evidence Board is a small, public-safe toolkit for building research agents that do not publish claims until the evidence is structured and checked.

It is meant for teams building autonomous research systems, monitoring bots, OSS maintainer workflows, or crypto/AI intelligence pipelines where an LLM may collect signals but a deterministic gate should decide whether the output is ready to publish.

## What it does

- stores topics, sources, raw events, evidence cards, reviews, judge decisions, and publications in SQLite;
- captures public URL text from ordinary pages and concrete X/Twitter post URLs through public endpoints where available;
- validates evidence cards before publication;
- blocks common failure modes: unsourced claims, stale X posts, missing X source text, guarantee/trading language, and secret-like values;
- keeps examples and tests small enough to audit.

## What it does not do

- It does not include private Telegram bots, cookies, SSH bridges, API keys, or production configs.
- It does not trade, recommend buys/sells, or promise market outcomes.
- It does not bypass paywalls, login walls, or platform restrictions.
- It does not make an LLM trustworthy by itself. It gives agents a stricter evidence format and a gate.

## Quickstart

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -e .

aeb init-db
aeb demo --db work/demo.db
aeb gate-card examples/sample_intelligence_card.json
```

Expected result: the sample card is allowed because every claim references a known full-access source.

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

aeb init-db
aeb demo --db work/demo.db
aeb gate-card examples/sample_intelligence_card.json
```

## Core model

```text
source -> raw_event -> evidence_card -> review -> judge_decision -> publication
```

The important idea is that an agent should not publish a confident answer directly from a prompt. It should first produce structured claims, attach sources, mark weak assumptions, and pass a gate.

## Example card

```json
{
  "title": "Example project announced a new agent SDK",
  "topic": "ai_agents_web3_infra",
  "claims": [
    {
      "claim": "The project announced a public SDK release.",
      "source_id": "source_1",
      "confidence": "high"
    }
  ],
  "sources_checked": [
    {
      "source_id": "source_1",
      "type": "web",
      "url": "https://example.com/release",
      "access": "full"
    }
  ],
  "verdict": {
    "status": "watch",
    "summary": "Useful signal, but not enough for a high-confidence call."
  }
}
```

## CLI

```bash
aeb init-db --db work/board.db
aeb ingest-url https://example.com --db work/board.db
aeb validate-card examples/sample_intelligence_card.json
aeb gate-card examples/sample_intelligence_card.json
```

## Publication gate

The gate blocks by default when:

- any claim lacks a known `source_id`;
- an X/Twitter source is only a preview or missing text;
- a source is older than the configured freshness window;
- the card contains guarantee/buy-now language;
- the card contains secret-like values;
- a reviewer explicitly blocks publication.

Warnings are allowed only when you pass `--allow-warnings`.

## Why this exists

LLM research agents often produce useful summaries, but they also overfit snippets, miss images, confuse weak signals with facts, and sound too certain. This project gives those agents a shared evidence ledger and a deterministic publication boundary.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Use cases](docs/USE_CASES.md)
- [Roadmap](ROADMAP.md)
- [Release checklist](docs/RELEASE_CHECKLIST.md)
- [Codex for OSS application draft](docs/CODEX_FOR_OSS_APPLICATION_DRAFT.md)

## Security

Do not put secrets, cookies, private tokens, private repo contents, or customer data into evidence cards. See [SECURITY.md](SECURITY.md).
