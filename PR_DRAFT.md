# PR Draft

## Title
Add coding-agent review loop proof

## Summary
- add a deterministic local-only example that simulates a coding-agent review loop burning budget and a patch retry storm
- document the example from the README, getting-started guide, and examples index
- add focused regression coverage proving the example runs offline and emits guard events
- sync the generated PyPI README after root README changes

## Scope
- `examples/coding_agent_review_loop.py`
- README / getting-started / examples docs
- `sdk/tests/test_example_starters.py`
- generated `sdk/PYPI_README.md`
- proof artifacts under `proof/coding-agent-review-loop/`

## Non-goals
- no dashboard repo changes
- no auth, billing, database, deployment, secrets, or destructive script changes
- no new runtime dependencies
- no public SDK API changes

## Risk
- low: this is an additive local example, docs, and test coverage
- runtime behavior is unchanged
- rollback is a straight revert with no migration or package dependency impact

## Validation
- `python examples/coding_agent_review_loop.py`
- `python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl`
- `python -m pytest sdk/tests/test_example_starters.py::test_coding_agent_review_loop_example_runs_offline -q`
- `python scripts/sdk_preflight.py`
- `python scripts/sdk_release_guard.py`
- `git diff --check`
- `python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py`
- `python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`
- `npm --prefix mcp-server test`
- `python -m pytest sdk/tests/test_architecture.py -v`
- `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q`

`make` is unavailable in this Windows shell, so Makefile-equivalent commands
were run directly. Proof is saved in `proof/coding-agent-review-loop/`.
