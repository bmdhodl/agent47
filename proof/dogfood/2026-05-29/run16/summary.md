# Dogfood operator run16 - 2026-05-29

## Goal and scope

Goal: keep a real AgentGuard workflow running against the public SDK repo and leave durable proof.

Scope: proof artifacts under `proof/dogfood/2026-05-29/run16/` only.

Non-goals: no SDK behavior changes, no dashboard/auth/billing/secrets/deployments, no paid features, no release cut, and no registry republish.

Done criteria: raw traces saved, commands captured, guard behavior verified from JSONL events, focused proof tests passed, release/package health checked, artifact hygiene checked, PR updated, and rolling issue updated.

## Commands run

- `agentguard doctor --trace-file proof/dogfood/2026-05-29/run16/installed_agentguard_doctor_trace.jsonl`
- `agentguard demo`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-29/run16/repo_agentguard_doctor_trace.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report proof/dogfood/2026-05-29/run16/repo_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident proof/dogfood/2026-05-29/run16/repo_agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident proof/dogfood/2026-05-29/run16/coding_agent_review_loop_traces.jsonl`
- `PYTHONPATH=./sdk python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `PYTHONPATH=./sdk python scripts/sdk_release_guard.py --check-mcp-npm`

## Concrete guard behavior observed

AgentGuard enforcement was real and trace-backed, not just command success.

Installed and repo-local `doctor` traces:

- `doctor.verify` emitted start and end spans.

Installed and repo-local `demo` traces:

- `guard.budget_warning` emitted at USD 0.8400 / USD 1.0000.
- `guard.budget_exceeded` emitted at USD 1.0800 > USD 1.0000.
- `guard.loop_detected` emitted for repeated `tool.search({"query":"python asyncio"})` calls.
- `guard.retry_limit_exceeded` emitted for `fetch_docs` attempt 3 with limit 2.

Repo-local coding-agent review loop trace:

- `guard.budget_exceeded` emitted on attempt 3 at USD 0.0510 > USD 0.0450.
- `guard.retry_limit_exceeded` emitted for `apply_patch` attempt 4 with limit 3.

See `trace-inspection.txt` and `trace-inspection.json` for the parsed event evidence.

## Validation

- Focused proof/CLI/metadata tests: 35 passed in 1.44s.
- Release guard: `Release guard passed.`
- GitHub release: `v1.2.10`, published 2026-05-02T15:48:03Z.
- PyPI `agentguard47`: latest and installed `1.2.10`.
- Local SDK: `1.2.10`.
- npm `@agentguard47/mcp-server`: `0.2.2`.
- Local MCP metadata: `0.2.2` in `mcp-server/package.json` and `mcp-server/server.json`.

## Repo health snapshot

- Roadmap freshness warning remains: `ops/03-ROADMAP_NOW_NEXT_LATER.md` is 3 weeks old.
- Architecture freshness warning remains: `ops/02-ARCHITECTURE.md` is 4 weeks old.
- Release/package alignment is good for GitHub/PyPI/local SDK `1.2.10` and npm/local MCP `0.2.2`.
- Distribution drift remains: official MCP Registry search still reports `0.2.1`; Glama API still returns zero indexed tools.
- First 50 open PRs are review-blocked; PR `#508` still has failing/cancelled Python checks.

## PRs needing action

- `#520` has 6 active unresolved review threads around release workflow ordering, prerelease docs, and release-note label config. This is the highest-value fix candidate.
- `#518` has 1 active unresolved review thread about the known review-loop cost proof drift.
- `#508` still has failing/cancelled Python checks on the `actions/setup-go` Dependabot bump.
- `#544` is the current same-day dogfood proof PR and remains review-required after this run.

## Issues needing action

- `#473` continues to track stale ops docs.
- `#507` / `#469` remain security scan items that need clean SDK-only reproduction before escalation.
- `#512` - `#515` still look like tech-debt scanner noise from docs/proof artifacts and need triage.
- `#418` weekly dependency drift remains open.

## Recommended next task

Fix PR `#520` review feedback first: make GitHub Release creation depend on successful publish/release guard behavior, then align release-note label docs with the repo's `type:*` labels.