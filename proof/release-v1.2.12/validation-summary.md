# AgentGuard v1.2.12 Release Prep Validation

Date: 2026-05-29

## Release Context

- `v1.2.11` tag exists, but PyPI publish failed before a GitHub Release was created.
- `v1.2.12` is the next release candidate from current `main`.
- Release notes and release-content automation now start from the last published GitHub Release instead of the last raw git tag.

## Commands Run

```powershell
python -m pytest sdk/tests/test_ci_guardrails.py sdk/tests/test_pypi_readme_sync.py sdk/tests/test_sdk_release_guard.py -q
python scripts/sdk_release_guard.py --json
git diff --check
python -m ruff check sdk/tests/test_ci_guardrails.py scripts/generate_pypi_readme.py scripts/sdk_release_guard.py scripts/sdk_preflight.py
python scripts/ci_tools_requirements_guard.py
python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py scripts/ci_tools_requirements_guard.py
python scripts/sdk_preflight.py
python -m pytest sdk/tests/test_architecture.py -v
python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80
python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q
npm --prefix mcp-server ci
npm --prefix mcp-server test
npm --prefix mcp-server run build
python -m pip install -e ./agentguard-mcp
python -m ruff check agentguard_mcp tests
python -m pytest
python -m build ./sdk --wheel
python -m venv <temp-venv>
pip install --no-index --find-links <wheelhouse> agentguard47-1.2.12-py3-none-any.whl
agentguard doctor
agentguard demo
agentguard quickstart --framework raw --write
python agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl
agentguard report agentguard_demo_traces.jsonl
```

## Results

- Targeted release tests: 18 passed.
- Release guard: no findings.
- SDK preflight: passed.
- Direct `make check` equivalents: CI tools guard passed, Makefile lint target passed, full SDK test passed, MCP test passed.
- Structural tests: 9 passed.
- Security scan: passed.
- Full SDK suite: 772 passed, coverage 92.82% after the release-candidate wording review fix.
- TypeScript MCP server: `npm ci`, 10 tests, and `tsc` build passed.
- Python local-budget MCP: ruff passed, 15 tests passed.
- Clean venv wheel smoke:
  - `agentguard.__version__=1.2.12`
  - package metadata `1.2.12`
  - `doctor` verified local-only install.
  - `demo` visibly tripped budget, loop, and retry guards.
  - generated raw quickstart ran and tripped budget plus loop guards.
  - local reports showed guard events and non-zero local trace output.

## Notes

- Local `go` is not installed, so `go run actionlint` was not available. CI Actionlint remains the workflow syntax authority.
- Local `make` is not installed; direct Makefile command equivalents were run instead.
- The user-site Python install has stale/broken `~gentguard47` metadata. Clean venv proof above avoids that contamination.
