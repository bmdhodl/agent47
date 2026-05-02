# Activation Improvements Validation

## Scope

Docs and proof assets only:

- README first-run activation path
- Getting-started copy-paste setup flow
- Coding-agent review-loop sample incident
- PyPI README sync for the README changes

## Commands run

```text
python scripts\generate_pypi_readme.py --check
passed

python -m pytest sdk\tests\test_pypi_readme_sync.py sdk\tests\test_example_starters.py sdk\tests\test_quickstart.py -v
22 passed

python scripts\sdk_preflight.py
All checks passed

python scripts\sdk_release_guard.py
Release guard passed

python -m ruff check scripts\generate_pypi_readme.py
All checks passed

python -m pytest sdk\tests\test_sdk_release_guard.py -v
6 passed

git diff --check
passed
```

## Manual activation proof

Executed in a temporary directory with `PYTHONPATH` pointed at this checkout.
On Windows PowerShell:

```text
$env:PYTHONPATH="C:\Users\patri\.codex\worktrees\3c4e\agent47\sdk"
python -m agentguard.cli doctor --trace-file doctor.jsonl
python -m agentguard.cli demo --trace-file demo.jsonl
python -m agentguard.cli quickstart --framework raw --write --output agentguard_raw_quickstart.py
python agentguard_raw_quickstart.py
python -m agentguard.cli report .agentguard\traces.jsonl
```

Observed:

- `doctor` completed and printed safe local next steps.
- `demo` showed BudgetGuard, LoopGuard, and RetryGuard stops without network calls.
- `quickstart --write` created a runnable raw starter.
- The starter wrote `.agentguard/traces.jsonl`.
- `report` rendered a local trace summary.

## Generated proof asset

`docs/examples/coding-agent-review-loop-incident.md` was generated from a clean
run of:

```text
$env:PYTHONPATH="C:\Users\patri\.codex\worktrees\3c4e\agent47\sdk"
python examples\coding_agent_review_loop.py
python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl --format markdown
```

## Review follow-up validation

Copilot review comments were addressed with targeted checks for reproducibility,
README clarity, PyPI README link handling, and checked-in sample incident drift.

```text
python -m pytest sdk\tests\test_pypi_readme_sync.py sdk\tests\test_example_starters.py sdk\tests\test_reporting.py -v
19 passed

python -m ruff check sdk/agentguard/reporting.py sdk/tests/test_pypi_readme_sync.py sdk/tests/test_example_starters.py scripts/generate_pypi_readme.py
All checks passed

python scripts\generate_pypi_readme.py --check
passed

python scripts\sdk_preflight.py
All checks passed

python scripts\sdk_release_guard.py
Release guard passed

git diff --check
passed
```
