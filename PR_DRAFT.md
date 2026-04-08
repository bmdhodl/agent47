# Draft PR

## Title
`Add quickstart file-write flow for faster local onboarding`

## Summary
- add `agentguard quickstart --write` so the SDK can create a runnable starter file directly
- add `--output` and `--force` for safe local file creation and explicit overwrite behavior
- update onboarding docs so the install-to-first-run path can move from printed snippet to actual file in one command
- add proof artifacts under `proof/quickstart-write-flow/`

## Why This Matters
- reduces copy-paste friction in the highest-priority onboarding path
- gives coding agents and humans a deterministic way to materialize a starter file locally
- keeps the first-run flow local-first, auditable, and zero-dependency

## Scope
- `sdk/agentguard/quickstart.py`
- `sdk/agentguard/cli.py`
- `sdk/tests/test_quickstart.py`
- `README.md`
- `docs/guides/coding-agents.md`
- `examples/starters/README.md`
- `sdk/PYPI_README.md`
- `proof/quickstart-write-flow/*`

## Non-goals
- no dashboard changes
- no new dependencies
- no new frameworks or hosted features
- no release cut

## Proof
- `python -m ruff check sdk/agentguard/cli.py sdk/agentguard/quickstart.py sdk/tests/test_quickstart.py`
- `PYTHONPATH=<repo>/sdk python -m pytest sdk/tests/test_quickstart.py -v`
- `PYTHONPATH=<repo>/sdk python scripts/sdk_preflight.py`
- `PYTHONPATH=<repo>/sdk python -m pytest sdk/tests -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`
- `python -m bandit -r sdk/agentguard -s B101,B110,B112,B311 -q`

Saved artifacts:
- `proof/quickstart-write-flow/raw-output.txt`
- `proof/quickstart-write-flow/openai-output.txt`
- `proof/quickstart-write-flow/overwrite-refusal.txt`
- `proof/quickstart-write-flow/agentguard_raw_quickstart.py`
- `proof/quickstart-write-flow/openai/agentguard_openai_quickstart.py`

## Notes
- This machine has an editable `agentguard47` install outside this worktree, so local Python validation was run with `PYTHONPATH` pinned to `sdk/` in this branch to ensure the tests and CLI exercised the PR code.
