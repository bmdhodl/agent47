# Dogfood run 15 - 2026-05-23

## Goal

Keep the recurring AgentGuard dogfood proof running against the public SDK checkout and leave durable repo/GitHub evidence.

## Commands run

- `agentguard doctor`
- `PYTHONPATH=./sdk python -m agentguard.cli doctor`
- `PYTHONPATH=./sdk python -m agentguard.cli demo`
- `PYTHONPATH=./sdk python examples/coding_agent_review_loop.py`
- `PYTHONPATH=./sdk python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `PYTHONPATH=./sdk python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard behavior observed

The proof is valid because raw trace files contained real guard events, not just successful command exits.

Demo trace:

- `guard.budget_warning`: 1
- `guard.budget_exceeded`: 1 at `$1.0800 > $1.0000`
- `guard.loop_detected`: 1 for repeated `tool.search`
- `guard.retry_limit_exceeded`: 1 for `fetch_docs`

Coding-agent review loop trace:

- `guard.budget_exceeded`: 1 at `$0.0510 > $0.0450` on review attempt 3
- `guard.retry_limit_exceeded`: 1 for `apply_patch` attempt 4

## Validation

- Focused dogfood test slice passed: `35 passed in 1.60s`
- Release guard passed: `python scripts/sdk_release_guard.py --check-mcp-npm`
- Review-thread sweep found `0` active unresolved non-outdated threads across open PRs

## Repo health notes

- Roadmap staleness remains: `ops/03-ROADMAP_NOW_NEXT_LATER.md` last changed 2 weeks ago.
- Architecture staleness remains: `ops/02-ARCHITECTURE.md` last changed 3 weeks ago.
- Latest GitHub release, PyPI, and local SDK remain aligned at `1.2.10`.
- npm and local MCP metadata remain aligned at `0.2.2`.
- External distribution drift remains: Glama did not provide indexed tools from this host, and MCP Registry search still needs follow-up evidence.

## Files in this proof bundle

- `agentguard_demo_traces.jsonl` - raw demo trace
- `coding_agent_review_loop_traces.jsonl` - raw review-loop trace
- `agentguard_doctor_trace.jsonl` - raw doctor trace when emitted
- `guard-events.txt` - extracted guard events
- `guard-event-summary.json` - guard event counts
- `demo-report.md` - CLI report output
- `review-loop-incident.md` - CLI incident output
- `open-prs.json`, `open-issues.json`, `review-thread-summary.json` - GitHub repo-health snapshots
- `github-release.json`, `local-sdk-version.json`, `local-mcp-version.json`, `npm-mcp-version.txt`, `pypi-agentguard47-versions.txt` - release/package snapshots
