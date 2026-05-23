# Dogfood run13 - 2026-05-23

## Goal
Keep the real coding-agent workflow running under AgentGuard and leave durable repo/GitHub artifacts without touching SDK feature code.

## Commands run
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`
- `git diff --check HEAD`
- GitHub PR/issue/review-thread/release/distribution checks via `gh`, plus package/distribution metadata checks.

## Guard behavior observed
- Demo trace emitted `guard.budget_warning=1`, `guard.budget_exceeded=1`, `guard.loop_detected=1`, and `guard.retry_limit_exceeded=1`.
- Demo budget enforcement stopped at `$1.0800 > $1.0000`; loop enforcement stopped repeated `tool.search`; retry enforcement stopped `fetch_docs` at attempt 3 with limit 2.
- Coding-agent review-loop trace emitted `guard.budget_exceeded=1` at `$0.0510 > $0.0450` on review attempt 3.
- Coding-agent review-loop trace emitted `guard.retry_limit_exceeded=1` for `apply_patch` attempt 4 with limit 3.
- Doctor trace emitted `doctor.verify` start/end events.

## Enforcement verdict
Real enforcement. This was not stdout-only proof: raw JSONL traces and incident/report outputs are saved in this directory.

## Validation
- Focused dogfood/CLI/metadata tests: `35 passed in 1.38s`.
- Release guard: passed.
- `git diff --check HEAD`: passed.
- Artifact scan: passed, no BOM/NUL bytes and JSON artifacts parse.

## Repo health
- Open PRs: 25.
- Active unresolved non-outdated review threads across open PRs: 0.
- PR #506 status: `REVIEW_REQUIRED` / `BLOCKED` on `c121f963968b72ca0bab3648c66aed019cab8762`.
- Failing/pending PR checks: [
  {
    "number": 508,
    "title": "chore(deps): bump actions/setup-go from 5.6.0 to 6.4.0",
    "failures": [
      [
        "test (3.9)",
        "CANCELLED"
      ],
      [
        "test (3.9)",
        "CANCELLED"
      ],
      [
        "test (3.12)",
        "FAILURE"
      ],
      [
        "test (3.10)",
        "CANCELLED"
      ],
      [
        "test (3.11)",
        "FAILURE"
      ],
      [
        "test (3.12)",
        "CANCELLED"
      ]
    ],
    "pending": []
  }
].
- Staleness warning remains: roadmap 2 weeks old; architecture 3 weeks old.

## Release/distribution
- GitHub release and PyPI latest remain `v1.2.10` / `1.2.10`.
- Local SDK version remains `1.2.10`.
- Local MCP package/server metadata remains `0.2.2`; npm view reports `0.2.2` when invoked via `npm.cmd`.
- Official MCP Registry direct endpoint returned 404 from this host; Glama API returned 403 from this host, so external indexing remains unresolved.

## Issues needing action
- #507: security: sdk pip-audit vulns (pypdf, pytest, requests, urllib3, etc.) (https://github.com/bmdhodl/agent47/issues/507)
- #490: Dogfood operator rolling proof log (https://github.com/bmdhodl/agent47/issues/490)
- #473: [ops-cadence] Docs need refresh (https://github.com/bmdhodl/agent47/issues/473)
- #469: security: sdk pip-audit findings (pypdf, python-multipart, urllib3, etc.) (https://github.com/bmdhodl/agent47/issues/469)
- #468: [release-cadence] Active release queue (https://github.com/bmdhodl/agent47/issues/468)
- #464: Track Managed Agents Dreaming cost surface (https://github.com/bmdhodl/agent47/issues/464)

## Recommended next task
Fix PR #508's Dependabot setup-go bump by updating `sdk/tests/test_ci_guardrails.py` to accept the new pinned `actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c # v6.4.0`, then rerun CI.
