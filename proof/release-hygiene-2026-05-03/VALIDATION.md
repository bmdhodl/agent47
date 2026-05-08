# Release Hygiene Validation - 2026-05-03

## Scope

Post-release hygiene only. No SDK runtime code, MCP runtime code, package
versions, dependencies, or hosted dashboard contracts changed.

Changed:

- `README.md`
- `sdk/README.md`
- `sdk/PYPI_README.md`
- `docs/guides/getting-started.md`
- `docs/cost-guardrails.md`
- `docs/competitive/vercel-ai-gateway.md`
- `docs/blog/002-budget-enforcement-patterns-devto.md`
- `docs/blog/003-ci-cost-gates-devto.md`
- `docs/discussions/02_budget_enforcement_patterns.md`
- `docs/discussions/03_limit_openai_spend.md`
- `examples/openai_agents_with_guards.py`
- `examples/crewai_with_guards.py`
- `sdk/examples/openai_agent.py`
- `ops/03-ROADMAP_NOW_NEXT_LATER.md`
- `memory/state.md`
- `memory/blockers.md`
- `AGENTS.md`
- `SKILL.md`

## Live Package Evidence

```text
python -m pip index versions agentguard47
agentguard47 (1.2.10)
Available versions: 1.2.10, 1.2.9, 1.2.8, 1.2.6, 1.2.5, 1.2.4, 1.2.3, 1.2.2, 1.2.1, 1.2.0, 1.0.0, 0.8.0, 0.7.0, 0.6.0, 0.5.0, 0.4.0, 0.3.0, 0.2.0
  INSTALLED: 1.2.10
  LATEST:    1.2.10

gh release view v1.2.10 --repo bmdhodl/agent47 --json tagName,name,publishedAt,url,isDraft,isPrerelease,targetCommitish
{"isDraft":false,"isPrerelease":false,"name":"AgentGuard v1.2.10","publishedAt":"2026-05-02T15:48:03Z","tagName":"v1.2.10","targetCommitish":"main","url":"https://github.com/bmdhodl/agent47/releases/tag/v1.2.10"}

node -p "require('./mcp-server/package.json').version"
0.2.2

npm view @agentguard47/mcp-server version
0.2.1
```

## npm MCP Drift

Repo metadata targets `@agentguard47/mcp-server@0.2.2`, but npm still serves
`0.2.1`. This is a publish blocker, not a source drift blocker. Prior proof in
`proof/mcp-release-consistency-2026-05-02/VALIDATION.md` records the OTP-blocked
publish attempt and the required manual command.

## Doc Accuracy Fix

High-visibility docs now show budget enforcement through either:

- explicit `BudgetGuard.consume(...)` at the point usage is known, or
- provider patching with `patch_openai(..., budget_guard=budget)` /
  `patch_anthropic(..., budget_guard=budget)`.

This avoids implying that `BudgetGuard` enforces budgets merely by being present
inside `Tracer(guards=[...])`.

## Validation

```text
python -m py_compile examples\openai_agents_with_guards.py examples\crewai_with_guards.py sdk\examples\openai_agent.py
PASS

python scripts\sdk_release_guard.py
PASS

python scripts\sdk_preflight.py
PASS

python -m ruff check sdk\agentguard\ scripts\generate_pypi_readme.py scripts\sdk_preflight.py scripts\sdk_release_guard.py
PASS

python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80
702 passed, coverage 92.98%

python -m pytest sdk/tests/test_architecture.py -v
9 passed

python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q
PASS

npm --prefix mcp-server ci
PASS

npm --prefix mcp-server test
5 passed
```

Notes:

- `make` is not installed in this Windows shell, so documented `make` targets
  were executed through their underlying Python/npm commands.
- `ruff` is not on PATH as a console script, but `python -m ruff` is available
  and passed.
