# AgentGuard Dogfood Proof - 2026-05-21

## Scope

- Repo: `bmdhodl/agent47`
- Checkout: `C:\Users\patri\.codex\worktrees\8ac4\agent47`
- Source binding: `C:\Users\patri\.codex\worktrees\8ac4\agent47\sdk\agentguard\__init__.py`
- Runtime: Python 3.13.2

## Commands Run

```powershell
$env:PYTHONPATH = "C:\Users\patri\.codex\worktrees\8ac4\agent47\sdk"
python -c "import agentguard; print(agentguard.__file__)"
agentguard doctor
python -m agentguard.cli doctor
python -m agentguard.cli demo
python examples\coding_agent_review_loop.py
python -m agentguard.cli report agentguard_demo_traces.jsonl
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
python -m pytest sdk/tests/test_demo.py sdk/tests/test_doctor.py sdk/tests/test_cli_report.py sdk/tests/test_example_starters.py sdk/tests/test_mcp_registry_metadata.py -q
python scripts\sdk_release_guard.py --check-mcp-npm
```

## Guard Events Observed

`agentguard_demo_traces.jsonl`:

- `guard.budget_warning`: 1 event at `$0.84 / $1.00`.
- `guard.budget_exceeded`: 1 event at `$1.08 > $1.00`.
- `guard.loop_detected`: 1 event for repeated `tool.search({"query":"python asyncio"})`.
- `guard.retry_limit_exceeded`: 1 event for `fetch_docs` attempt 3 with limit 2.

`coding_agent_review_loop_traces.jsonl`:

- `guard.budget_exceeded`: 1 event on review attempt 3 at `$0.0510 > $0.0450`.
- `guard.retry_limit_exceeded`: 1 event on `apply_patch` attempt 4 with limit 3.

## Enforcement Verdict

Enforcement was real. This run does not count CLI success alone as proof. The raw JSONL traces contain guard events emitted by AgentGuard and the incident/report commands summarized those events from the trace files.

## Validation

- Focused proof tests: `35 passed in 1.70s`.
- Release guard: `Release guard passed.`
- GitHub release: `v1.2.10`, published `2026-05-02T15:48:03Z`.
- PyPI package: `agentguard47==1.2.10`.
- npm MCP package: `@agentguard47/mcp-server==0.2.2`.
- Local MCP package metadata: `mcp-server/package.json==0.2.2`, `mcp-server/server.json==0.2.2`.

## Files

- `agentguard_demo_traces.jsonl`: raw offline demo trace.
- `coding_agent_review_loop_traces.jsonl`: raw coding-agent review-loop trace.
- `agentguard-demo-report.txt`: local report output for the demo trace.
- `coding-agent-incident.md`: incident report output for the review-loop trace.
- `agentguard-doctor.txt`: installed CLI doctor smoke check.
- `python-m-agentguard-doctor.txt`: repo-bound doctor check.
- `python-m-agentguard-demo.txt`: repo-bound demo command output.
- `coding-agent-review-loop.txt`: repo-bound review-loop example output.
- `repo_import.txt`: repo-local import binding proof.
