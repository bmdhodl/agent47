# Repo Health Snapshot - 2026-05-23 Run 9

## Staleness

- `ops/03-ROADMAP_NOW_NEXT_LATER.md`: 2 weeks ago.
- `ops/02-ARCHITECTURE.md`: 3 weeks ago.
- Existing tracker: issue `#473` docs freshness.

## PRs

- `#506` rolling dogfood proof PR: checks green, `REVIEW_REQUIRED`, `BLOCKED`, 0 active unresolved non-outdated review threads.
- `#510` `qs` Dependabot bump: checks green, `REVIEW_REQUIRED`, 0 active unresolved non-outdated review threads.
- `#509` CodeQL action Dependabot bump: checks green, `REVIEW_REQUIRED`, 0 active unresolved non-outdated review threads.
- `#508` `actions/setup-go` Dependabot bump: CI failing because `sdk/tests/test_ci_guardrails.py::test_actionlint_workflow_is_wired` still expects the v5 pinned action string while the PR updates `.github/workflows/actionlint.yml` to `actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c # v6.4.0`.
- All open PR review-thread sweep: 0 active unresolved non-outdated review threads.

## Issues

- `#507` new security scan issue: needs clean SDK-only reproduction before changing `sdk/pyproject.toml`; the SDK runtime remains zero-dependency.
- `#490` rolling dogfood proof log: active sink for this run.
- `#473` docs freshness: still valid because roadmap and architecture are stale.
- `#469` older security scan issue: same reproduce-before-escalating posture.
- `#468` release queue: hold state, not a release trigger.
- `#418` dependency drift report: still a maintenance bucket; verify stale version claims before acting.

## Release and Distribution

- GitHub release: `v1.2.10`, published `2026-05-02T15:48:03Z`.
- PyPI `agentguard47`: `1.2.10`.
- Local SDK `sdk/pyproject.toml`: `1.2.10`.
- npm `@agentguard47/mcp-server`: `0.2.2`.
- Local `mcp-server/package.json` and `mcp-server/server.json`: `0.2.2`.
- Official MCP Registry search still reports `io.github.bmdhodl/agentguard47` and package version `0.2.1`.
- Glama API currently reports `tools=0`.

## Recommended Next Task

Fix `#508` by updating the CI guardrail expectation for the new pinned `actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c # v6.4.0`, then rerun CI.
