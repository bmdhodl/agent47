# Dogfood proof run 9 - 2026-05-24

## Scope

SDK-only recurring dogfood pass for the public AgentGuard repo. No runtime,
dashboard, auth, billing, deployment, dependency, or release changes were made.

## Repo state

- Repo: `bmdhodl/agent47`
- Proof branch/PR: `codex/dogfood-proof-2026-05-22-run11` / PR `#506`
- Checkout mode: detached at PR `#506` head
- Roadmap freshness: `ops/03-ROADMAP_NOW_NEXT_LATER.md` last changed 2 weeks ago
- Architecture freshness: `ops/02-ARCHITECTURE.md` last changed 3 weeks ago
- Existing tracker for freshness drift: issue `#473`

## Commands run

Installed CLI smoke checks:

```powershell
agentguard doctor --trace-file proof/dogfood/2026-05-24/run9/installed_agentguard_doctor_trace.jsonl
agentguard demo --trace-file proof/dogfood/2026-05-24/run9/installed_agentguard_demo_traces.jsonl
```

Canonical checkout proof:

```powershell
$env:PYTHONPATH = './sdk'
python -m agentguard.cli doctor --trace-file proof/dogfood/2026-05-24/run9/repo_agentguard_doctor_trace.jsonl
python -m agentguard.cli demo --trace-file proof/dogfood/2026-05-24/run9/repo_agentguard_demo_traces.jsonl
python examples/coding_agent_review_loop.py
python -m agentguard.cli report proof/dogfood/2026-05-24/run9/repo_agentguard_demo_traces.jsonl
python -m agentguard.cli incident proof/dogfood/2026-05-24/run9/repo_coding_agent_review_loop_traces.jsonl
```

Validation and health checks:

```powershell
python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q
python scripts/sdk_release_guard.py --check-mcp-npm
gh pr list --state open --limit 50 --json ...
gh issue list --state open --limit 50 --json ...
gh release view --json tagName,publishedAt,url,isPrerelease,isDraft,name
python -m pip index versions agentguard47
npm view @agentguard47/mcp-server version --json
Invoke-RestMethod https://glama.ai/api/mcp/v1/servers/bmdhodl/agent47
```

## Guard behavior observed

Real enforcement was observed in raw trace files:

- `installed_agentguard_doctor_trace.jsonl`: `doctor.verify` start/end events.
- `repo_agentguard_doctor_trace.jsonl`: `doctor.verify` start/end events.
- `repo_agentguard_demo_traces.jsonl`: `guard.budget_warning` at `$0.8400 / $1.0000`.
- `repo_agentguard_demo_traces.jsonl`: `guard.budget_exceeded` at `$1.0800 > $1.0000`.
- `repo_agentguard_demo_traces.jsonl`: `guard.loop_detected` for repeated `tool.search`.
- `repo_agentguard_demo_traces.jsonl`: `guard.retry_limit_exceeded` for `fetch_docs` attempt 3 with limit 2.
- `repo_coding_agent_review_loop_traces.jsonl`: `guard.budget_exceeded` at `$0.0510 > $0.0450`.
- `repo_coding_agent_review_loop_traces.jsonl`: `guard.retry_limit_exceeded` for `apply_patch` attempt 4 with limit 3.

The extracted event list is saved in `guard_events.json` and
`trace_inspection.txt`.

## Proof files

- `command_output.txt`
- `installed_doctor_output.txt`
- `installed_demo_output.txt`
- `installed_agentguard_doctor_trace.jsonl`
- `installed_agentguard_demo_traces.jsonl`
- `repo_doctor_output.txt`
- `repo_demo_output.txt`
- `repo_agentguard_doctor_trace.jsonl`
- `repo_agentguard_demo_traces.jsonl`
- `review_loop_output.txt`
- `repo_coding_agent_review_loop_traces.jsonl`
- `repo_demo_report.txt`
- `repo_review_loop_incident.md`
- `guard_events.json`
- `trace_inspection.txt`
- `pytest_focused.txt`
- `release_guard_check_mcp_npm.txt`
- `github_release.json`
- `pypi_versions.txt`
- `npm_mcp_version.json`
- `npm_mcp_metadata.json`
- `glama_api.json`
- `mcp_registry_api_error.txt`
- `open_prs.json`
- `open_issues.json`
- `pr506_snapshot.json`
- `pr506_checks_before_push.txt`
- `pr506_review_comments_before_push.json`
- `review_threads_before_push.json`
- `review_thread_summary_before_push.json`
- `issue490_comments.txt`
- `issue473_snapshot.txt`
- `issue511_snapshot.txt`
- `pr508_checks.txt`
- `pr509_checks.txt`
- `pr510_checks.txt`

## Validation result

- Focused pytest slice: 35 passed in 1.50s.
- MCP npm release guard: passed.
- Pre-push PR `#506` checks were green.
- Pre-push open-PR review sweep: 25 open PRs, 56 review threads, 0 active unresolved non-outdated threads.

## Release and distribution snapshot

- GitHub latest release: `v1.2.10`.
- PyPI latest `agentguard47`: `1.2.10`.
- npm latest `@agentguard47/mcp-server`: `0.2.2`.
- Glama API is reachable, but `tools` remains empty.
- MCP Registry direct API probe returned 404 for the attempted endpoint.

## Known proof-branch note

The review-loop incident renderer on this proof branch still reports estimated
cost `$0.1020`. The raw guard event and trace inspection prove enforcement at
`$0.0510 > $0.0450`; PR `#502` already carries the code fix for the reporting
double-counting behavior, so this proof run did not duplicate that fix.

## Repo health notes

- PR `#506` remains the consolidated rolling proof PR.
- PR `#508` still has failing Python checks from the setup-go Dependabot bump.
- PRs `#509` and `#510` have green checks and need human review.
- Issue `#473` already tracks stale roadmap/architecture docs.
- Issues `#507` and `#469` remain security/dependency audit sinks.
- Issue `#511` tracks the Claude-default-model audit.

## Next recommended task

Ship the small docs-freshness PR for `ops/03-ROADMAP_NOW_NEXT_LATER.md` and
`ops/02-ARCHITECTURE.md`, then continue MCP distribution hygiene from
`ops/FOLLOWUP.md`.
