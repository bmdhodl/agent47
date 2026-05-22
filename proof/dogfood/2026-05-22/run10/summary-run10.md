# AgentGuard Dogfood Proof - 2026-05-22 Run 10

## Commands run

- `python -m pip install -e .\sdk`
- `python -c "import agentguard; print(agentguard.__file__)"`
- `agentguard doctor`
- `python -m agentguard.cli doctor`
- `python -m agentguard.cli demo`
- `python .\examples\coding_agent_review_loop.py`
- `python -m agentguard.cli report agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident agentguard_demo_traces.jsonl`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q`
- `python scripts\sdk_release_guard.py --check-mcp-npm`

## Guard behavior observed

Enforcement was real and trace-backed.

- `agentguard_demo_traces.jsonl` emitted `guard.budget_warning`, `guard.budget_exceeded`, `guard.loop_detected`, and `guard.retry_limit_exceeded`.
- Demo budget enforcement stopped at `$1.0800 > $1.0000`.
- Demo loop enforcement stopped repeated `tool.search({"query":"python asyncio"})`.
- Demo retry enforcement stopped `fetch_docs` after 3 attempts with a limit of 2.
- `coding_agent_review_loop_traces.jsonl` emitted `guard.budget_exceeded` and `guard.retry_limit_exceeded`.
- Review-loop budget enforcement stopped at `$0.0510 > $0.0450` on attempt 3.
- Review-loop retry enforcement stopped `apply_patch` on attempt 4 with a limit of 3.

## Artifacts

- `repo-import.txt` confirms the editable install was rebound to this checkout, sanitized to repo-relative path.
- `agentguard_doctor_trace_agentguard.jsonl` and `agentguard_doctor_trace_python_m.jsonl` are raw doctor traces.
- `agentguard_demo_traces.jsonl` is the raw offline demo trace.
- `coding_agent_review_loop_traces.jsonl` is the raw coding-agent review-loop trace.
- `agentguard_demo_report.txt` is the CLI report output for the demo trace.
- `agentguard_demo_incident.md` is the incident output for the demo trace.
- `coding_agent_review_loop_incident.md` is the incident output for the review-loop trace.
- `guard-events-run10.json` is the structured guard-event inspection.
- `focused-tests.txt` and `release-guard.txt` are validation outputs.

## Validation

- Focused dogfood regression slice: 35 passed.
- MCP npm release guard: passed.
- SDK version verified locally as `1.2.10`.
- GitHub release and PyPI latest verified as `1.2.10`.
- npm `@agentguard47/mcp-server` and local MCP metadata verified as `0.2.2`.

## Notes

- Roadmap and architecture freshness are still stale under `AGENTS.md`: roadmap was last touched `2 weeks ago`, architecture `3 weeks ago`.
- Glama API returned HTTP 403 from this environment, so tool indexing could not be rechecked live in this run.
