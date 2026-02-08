# Contributing

Thanks for your interest in AgentGuard. This guide covers the monorepo setup and how to contribute.

## Repo Structure

```
agent47/
├── sdk/           # Python SDK (agentguard47) — MIT licensed
├── dashboard/     # Next.js 14 SaaS dashboard
├── mcp-server/    # MCP server for AI agent access
├── site/          # Landing page
├── scripts/       # Automation and deploy scripts
├── docs/          # Strategy, outreach, blog, examples
└── .github/       # CI/CD workflows
```

## Dev Setup

### SDK (Python)

```bash
pip install -e ./sdk
PYTHONPATH=sdk python3 -m unittest discover -s sdk/tests -v
ruff check sdk/agentguard/
```

### Dashboard (Next.js)

```bash
cd dashboard
npm ci
npm run dev     # localhost:3000
npm run build
npm run lint
```

### MCP Server

```bash
cd mcp-server
npm ci
npm run build
```

## Running Tests

```bash
# All SDK tests
PYTHONPATH=sdk python3 -m unittest discover -s sdk/tests -v

# Single test file
PYTHONPATH=sdk python3 -m unittest sdk.tests.test_guards -v

# Single test case
PYTHONPATH=sdk python3 -m unittest sdk.tests.test_guards.TestLoopGuard.test_loop_detected -v
```

## PR Guidelines

- Keep PRs small and focused — one feature or fix per PR.
- Include tests for new SDK functionality.
- Run `ruff check sdk/agentguard/` before submitting.
- Run the full test suite and confirm it passes.
- Reference the relevant GitHub issue number in the PR description.

## Issue Labels

| Prefix | Values |
|--------|--------|
| `component:` | sdk, dashboard, api, infra |
| `type:` | feature, bug, refactor, docs, test, ci, security, perf |
| `priority:` | critical, high, medium, low |
| `phase:` | v0.5.1 through v1.0.0 |

## SDK Conventions

- **Zero dependencies.** Python stdlib only. Optional extras (e.g., `langchain-core`) are fine.
- **Python 3.9+** compatibility required.
- **All tests use `unittest`** — no pytest.
- **Guards raise exceptions** (`LoopDetected`, `BudgetExceeded`, `TimeoutExceeded`).
- **Public API exports** go through `sdk/agentguard/__init__.py`.

## Project Board

Track issues and progress: https://github.com/users/bmdhodl/projects/4
