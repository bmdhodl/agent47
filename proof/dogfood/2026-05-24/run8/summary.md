# Dogfood proof run 8 - 2026-05-24

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

PATH-installed smoke checks, not counted as canonical checkout proof because
`agentguard.__file__` resolved to another local worktree:

```powershell
agentguard doctor
agentguard demo
```

Canonical checkout proof:

```powershell
$env:PYTHONPATH = './sdk'
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples/coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
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

Real enforcement was observed in repo-local trace files:

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
- `pr506_comments.txt`
- `pr506_after_wait.json`
- `pr506_review_comments_after_wait.json`
- `pr506_review_threads_after_wait.json`
- `review_thread_summary_after_wait.json`
- `issue490_comments.txt`
- `issue473_snapshot.txt`
- `issue511_snapshot.txt`
- `pr508_checks.txt`
- `pr509_checks.txt`
- `pr510_checks.txt`
- `artifact_hygiene.txt`

## Validation result

- Focused pytest slice: 35 passed.
- MCP npm release guard: passed.
- Artifact hygiene: UTF-8 without BOM, no NUL bytes, no local absolute paths.
- Refreshed PR `#506` checks on commit `91675d7`: all 14 checks completed successfully.
- Post-wait PR review sweep: 0 review comments and 0 active unresolved non-outdated review threads.

## Release and distribution snapshot

- GitHub latest release: `v1.2.10`.
- PyPI latest `agentguard47`: `1.2.10`.
- npm latest `@agentguard47/mcp-server`: `0.2.2`.
- Glama API reachable, but `tools` remains empty.
- MCP Registry direct API probe returned 404 for the attempted endpoint.

## Repo health notes

- PR `#506` was green before this proof commit and remains review-required.
- PR `#508` still has failing Python checks from the setup-go Dependabot bump.
- PRs `#509` and `#510` have green checks and still need human review.
- Issue `#473` already tracks stale roadmap/architecture docs.
- Issue `#511` is new and tracks a Claude-default-model audit.

## Next recommended task

Ship the small docs-freshness PR for `ops/03-ROADMAP_NOW_NEXT_LATER.md` and
`ops/02-ARCHITECTURE.md`, then continue MCP distribution hygiene from
`ops/FOLLOWUP.md`.
