# Per-Token Budget Spike Proof

This folder contains proof for the per-token pricing onboarding PR.

- `example-output.txt`: console output from running `examples/per_token_budget_spike.py`
- `per_token_budget_spike_traces.jsonl`: local trace emitted by the example
- `report.txt`: `agentguard report` output for the saved trace
- `preflight.txt`: `python scripts/sdk_preflight.py`
- `tests.txt`: targeted example + PyPI README sync tests
- `check.txt`: full SDK pytest + coverage run
- `lint.txt`: targeted `ruff` output for the touched files
- `release-guard.txt`: `python scripts/sdk_release_guard.py`
- `security.txt`: `bandit` output; empty file means no findings were emitted
