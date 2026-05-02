# Repo Trust And Star Conversion Validation

## Scope

Docs and repository-health surfaces only.

Changed:

- root `LICENSE`
- `CONTRIBUTING.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/*.yml`
- `docs/examples/proof-gallery.md`
- `docs/assets/agentguard-social-preview.svg`
- `README.md`
- `examples/README.md`
- generated `sdk/PYPI_README.md`

No SDK runtime code, dashboard code, dependency metadata, or public Python API
changed.

## External Patterns Reviewed

- GitHub contributor guidance: contributing docs and issue/PR templates should
  be surfaced directly in repository workflows.
- pyOpenSci Python package guidance: root README should include install,
  badges, and a short useful code demo.
- 10up open-source best practices: README, code of conduct, contributing,
  license, security policy, issue templates, and PR template are baseline trust
  files.
- AgentOps and LangChain quickstarts: successful AI SDK repos make the first
  runnable proof and GitHub path obvious.

## Commands

```text
python scripts\generate_pypi_readme.py --write

python scripts\generate_pypi_readme.py --check
passed

python scripts\sdk_release_guard.py
Release guard passed.

python -m pytest sdk\tests\test_pypi_readme_sync.py sdk\tests\test_demo.py sdk\tests\test_quickstart.py -v
19 passed

python scripts\sdk_preflight.py
passed

make check
failed: make is not installed in this PowerShell environment.

make structural
failed: make is not installed in this PowerShell environment.

make security
failed: make is not installed in this PowerShell environment.

python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py
All checks passed.

python -m pytest sdk/tests/test_architecture.py -v
9 passed

python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q
passed

npm --prefix mcp-server test
5 passed

python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80
701 passed, coverage 92.97%

python -m ruff check scripts/generate_pypi_readme.py
All checks passed.

git diff --check
passed
```

## Local Proof Commands

Executed from a temporary directory so generated trace files did not dirty the
repo checkout:

```text
python -m agentguard.cli demo
Local proof complete.

python examples\coding_agent_review_loop.py
BudgetGuard stopped review loop on attempt 3.
RetryGuard stopped retry storm on attempt 4.

python -m agentguard.cli incident coding_agent_review_loop_traces.jsonl
Status: incident
Primary cause: retry_limit_exceeded

python examples\per_token_budget_spike.py
Budget spike caught on turn 3.

python -m agentguard.cli report per_token_budget_spike_traces.jsonl
AgentGuard report rendered.

python examples\decision_trace_workflow.py
Wrote decision_trace_workflow.jsonl.

python -m agentguard.cli decisions decision_trace_workflow.jsonl
decision events: 4
decision.proposed: 1
decision.edited: 1
decision.approved: 1
decision.bound: 1

python examples\budget_aware_escalation.py
Escalation reason: token_count 2430 exceeded 2000.
```

## Notes

- The root license is now the standard MIT text, matching `sdk/LICENSE` and
  `mcp-server/LICENSE`, so GitHub can detect the repository license cleanly
  after merge.
- The social preview SVG is a source asset. GitHub still requires uploading a
  rendered PNG/JPG in repository settings to enable a custom social preview.
- Repository topics were updated through GitHub: removed generic
  `observability`, `tracing`, `multi-agent`, and `llm`; added
  `runtime-control`, `coding-agents`, and `mcp-server`.
- Automated review flagged the generated PyPI README proof-gallery link because
  the new file does not exist in tag `v1.2.10`. `scripts/generate_pypi_readme.py`
  now treats `docs/examples/proof-gallery.md` as unreleased and links it to
  `main` until a future release tag includes it.
