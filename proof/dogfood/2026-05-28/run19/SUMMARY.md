# AgentGuard Dogfood Proof - 2026-05-28 run19

## Scope

- Repo: `bmdhodl/agent47`
- Branch updated: `dogfood-2026-05-28-run15-worker`
- SDK-only proof run. No dashboard, billing, secrets, deployment, or release work.
- Repo binding: `PYTHONPATH=<repo>\sdk`; import resolved to `<repo>\sdk\agentguard\__init__.py`.

## Commands Run

The generated command transcripts are stored beside this summary.

- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts/sdk_release_guard.py --check-mcp-npm`

## Guard Behavior Observed

Raw traces were saved without renaming the generated filenames:

- `agentguard_demo_traces.jsonl`
- `coding_agent_review_loop_traces.jsonl`

Trace-backed guard events:

- Demo trace: `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, `guard.retry_limit_exceeded`.
- Demo budget stop: `Cost budget exceeded: $1.0800 > $1.0000`.
- Demo loop stop: `tool.search({"query":"python asyncio"})` repeated 3 times.
- Demo retry stop: `fetch_docs` attempted 3 times with limit 2.
- Review-loop trace: `guard.budget_exceeded`, `guard.retry_limit_exceeded`.
- Review-loop budget stop: `$0.0510 > $0.0450` on attempt 3.
- Review-loop retry stop: `apply_patch` attempted 4 times with limit 3.

This counts as real enforcement because guard events were present in JSONL traces and incident output, not just console text.

## Artifacts

- `commands.json` - command list and exit codes.
- `repo-import.txt` - repo-local import proof.
- `path-agentguard-doctor.txt` - installed CLI smoke-check output.
- `repo-cli-doctor.txt` - repo-bound doctor output.
- `repo-cli-demo.txt` - repo-bound demo output.
- `review-loop-example.txt` - coding-agent review-loop output.
- `demo-report.txt` - demo report output.
- `demo-incident.txt` - demo incident report output.
- `review-loop-incident.txt` - review-loop incident report output.
- `trace-inspection.txt` - parsed guard-event counts and details.

## Validation

- Focused proof tests: `35 passed in 1.44s`.
- Release guard: `Release guard passed.`
- Release/package alignment checked:
  - GitHub release: `v1.2.10`, published `2026-05-02T15:48:03Z`.
  - PyPI latest: `1.2.10`, uploaded `2026-05-02T15:47:11.756969Z`.
  - Local SDK: `1.2.10`.
  - npm `@agentguard47/mcp-server`: `0.2.2`.
  - Local MCP metadata: `0.2.2`.

## Open Follow-Ups

- Roadmap is 3 weeks old and architecture is 4 weeks old; issue `#473` remains the active ops-freshness tracker.
- Official MCP Registry still reports `0.2.1` while npm/local metadata are `0.2.2`.
- Glama API still returns an empty `tools` array.
