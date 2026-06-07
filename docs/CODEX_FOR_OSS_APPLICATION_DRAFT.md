# Codex for OSS Application Draft

This is a draft. Do not submit it without replacing placeholders and verifying all metrics.

Official program framing: OpenAI says Codex for Open Source supports maintainers of active OSS projects and reviews signals such as repository usage, ecosystem importance, evidence of active maintenance, pull request review, issue triage, release management, and core maintainer responsibilities. API credits are meant for pull request review, maintainer automation, release workflows, and other core OSS work.

Source: https://openai.com/form/codex-for-oss/

## Repository

`https://github.com/<owner>/agent-evidence-board`

## Role

Primary maintainer.

## Why does this repository qualify? <= 500 chars

Agent Evidence Board is a public-safe evidence ledger and publication gate for AI research agents. It helps maintainers and agent builders block unsourced claims, preview-only social sources, stale evidence, secret-like values, and unsafe guarantee wording before public reports are published.

## How will API credits be used? <= 500 chars

We will use Codex for OSS maintenance workflows: reviewing PRs, expanding validator tests, hardening source-capture adapters, generating fixtures, improving docs, triaging issues, and building a GitHub Action/MCP workflow so other projects can gate agent-generated reports safely.

## Anything else? <= 500 chars

The project is intentionally dependency-light and public-safe: no cookies, bot tokens, private chat exports, or production bridges. The roadmap focuses on CI, recorded fixtures, GitHub Action integration, a read-only MCP server, and an evaluator suite for known agent failure modes.

## Evidence to collect before submitting

- GitHub stars/forks/watchers.
- Commits in the last 30/90 days.
- Releases and changelog.
- CI status.
- Test count and key failure modes covered.
- Issues/PRs showing active maintenance.
- Any external users, feedback, or integrations.
- Example workflows where the gate blocked a bad agent output.

## Maintainer workflows already documented

- Pull request review for agent-generated evidence cards.
- Issue triage for gate false positives and false negatives.
- Release management checklist with compile, test, demo, gate, and JSONL export smoke checks.
- Bounded Codex/API credit use for tests, docs, fixtures, PR review, issue triage, and release notes.
