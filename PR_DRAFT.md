# PR Draft

## Title
Add coding-agent skillpack generation for local-first AgentGuard onboarding

## Summary
- add `agentguard skillpack` so developers and coding agents can generate repo-local `.agentguard.json` defaults plus instruction files for Codex, Claude Code, GitHub Copilot, and Cursor
- keep the generated flow aligned with the existing local-first proof path: `agentguard doctor`, `agentguard quickstart --framework raw --write`, local starter run, local report
- update onboarding docs so the skillpack flow becomes the primary way to materialize coding-agent instructions instead of copying long snippets by hand

## Scope
- new core SDK module: `sdk/agentguard/skillpack.py`
- CLI wiring in `sdk/agentguard/cli.py`
- tests in `sdk/tests/test_skillpack.py` and `sdk/tests/test_architecture.py`
- onboarding docs in `README.md`, `docs/guides/getting-started.md`, `docs/guides/coding-agents.md`, and `docs/guides/coding-agent-safety-pack.md`
- generated `sdk/PYPI_README.md`
- proof artifacts under `proof/skillpack/`

## Non-goals
- no dashboard work
- no hosted settings in generated files
- no new runtime dependencies
- no speculative agent integrations beyond Codex, Claude Code, Copilot, and Cursor

## Proof
- `python -m ruff check sdk/agentguard/skillpack.py sdk/agentguard/cli.py sdk/tests/test_skillpack.py sdk/tests/test_architecture.py`
- `python -m pytest sdk/tests/test_skillpack.py sdk/tests/test_quickstart.py sdk/tests/test_architecture.py -v`
- `python scripts/sdk_preflight.py`
- `python -m pytest sdk/tests -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`
- `python scripts/sdk_release_guard.py`
- `python -m bandit -r sdk/agentguard -s B101,B110,B112,B311 -q`
- proof files:
  - `proof/skillpack/write-output.txt`
  - `proof/skillpack/claude-output.txt`
  - `proof/skillpack/codex-write-output.txt`
  - generated pack under `proof/skillpack/all/`

## Operator note
- local validation pinned `PYTHONPATH=<repo>/sdk` because this machine has another editable `agentguard47` install that can shadow branch code
