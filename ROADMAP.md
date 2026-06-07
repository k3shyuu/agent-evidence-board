# Roadmap

## v0.1

- Stabilize the CLI and evidence card schema.
- Add more negative tests for common agent failure modes.
- Publish a small set of synthetic examples.
- Keep the project dependency-light and easy to audit.

## v0.2

- Add recorded fixtures for public source capture.
- Add JSONL export/import for evidence cards and judge decisions.
- Add a GitHub Action example that blocks publication artifacts when `gate-card` fails.
- Add stricter schema validation using an optional dependency.

## v0.3

- Add a read-only MCP server for agent workflows.
- Add source adapter interface for newsletters, GitHub releases, RSS, and public web pages.
- Add a richer review object model for multi-agent critique.

## v0.4

- Add lightweight web UI or static HTML reports.
- Add evaluator suite with known false-positive and false-negative cases.
- Add signed/auditable publication reports.

## Non-goals

- Automated trading.
- Paywall or login bypasses.
- Private chat ingestion without explicit permission.
- Secret storage.
- Claims that the tool fully eliminates hallucinations.
