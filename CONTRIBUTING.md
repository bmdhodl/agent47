# Contributing to AgentGuard

Thanks for your interest in AgentGuard. This guide covers everything you need to set up, test, and submit a PR.

## Repo Structure

```
agent47/
├── sdk/           # Python SDK (agentguard47) — MIT licensed
│   ├── agentguard/    # Source code
│   └── tests/         # Test suite (unittest)
├── mcp-server/    # MCP server for AI agent access
├── site/          # Landing page
├── scripts/       # Automation and deploy scripts
├── docs/          # Examples and guides
└── .github/       # CI/CD workflows
```

## Dev Setup

### Prerequisites

- Python 3.9+ (we test 3.9, 3.10, 3.11, 3.12)
- Git

### Clone and install

```bash
git clone https://github.com/bmdhodl/agent47.git
cd agent47

# Create a virtualenv (recommended)
python3 -m venv .venv
source .venv/bin/activate

# Install the SDK in editable mode
pip install -e ./sdk

# Install dev tools
pip install pytest pytest-cov ruff
```

Verify the install:

```bash
python -c "import agentguard; print(agentguard.__version__)"
```

### Optional extras

If you're working on an integration, install its dependencies:

```bash
pip install -e "./sdk[langchain]"    # LangChain
pip install -e "./sdk[langgraph]"    # LangGraph
pip install -e "./sdk[crewai]"       # CrewAI
pip install -e "./sdk[otel]"         # OpenTelemetry
```

## Running Tests

```bash
# Full test suite with coverage
python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing

# Single test file
python -m pytest sdk/tests/test_guards.py -v

# Single test case
python -m pytest sdk/tests/test_guards.py::TestLoopGuard::test_loop_detected -v

# Coverage with fail-under (matches CI)
python -m pytest sdk/tests/ -v \
  --cov=agentguard \
  --cov-report=term-missing \
  --cov-fail-under=80
```

CI runs tests across Python 3.9–3.12 and enforces 80% minimum coverage.

## Linting

We use [ruff](https://docs.astral.sh/ruff/) for linting.

```bash
# Lint the SDK source (not tests or examples)
ruff check sdk/agentguard/

# Auto-fix what ruff can
ruff check sdk/agentguard/ --fix
```

CI runs `ruff check sdk/agentguard/` — your PR must pass this.

## Code Style

### Zero dependencies

The core SDK uses **Python stdlib only**. No third-party imports in `sdk/agentguard/` outside of optional integration modules. Optional extras (like `langchain-core`, `opentelemetry-api`) are fine in `integrations/` and `sinks/otel.py`, guarded by try/except ImportError.

### Import patterns

```python
# Optional dependency — guard at module level
try:
    from opentelemetry.trace import StatusCode
    _HAS_OTEL = True
except ImportError:
    _HAS_OTEL = False

# Lazy import inside methods when needed
def _start_span(self, ...):
    from opentelemetry.trace import set_span_in_context
    ...
```

### Python version

Target Python 3.9+. Use `from __future__ import annotations` for type hint forward references. Avoid 3.10+ syntax like `X | Y` unions.

### Public API

All public exports go through `sdk/agentguard/__init__.py`. If you add a new class or function that users should import, add it there.

### Guards

Guards raise specific exceptions: `LoopDetected`, `BudgetExceeded`, `TimeoutExceeded`, `RateLimitExceeded`. Guard checks should happen **inside** trace spans so rejections appear in traces.

### Thread safety

Use `threading.Lock` for shared mutable state in sinks and guards. The `HttpSink` and `OtelTraceSink` are examples.

## Branch Naming

```
feature/<short-description>    # New feature
fix/<short-description>        # Bug fix
docs/<short-description>       # Documentation
refactor/<short-description>   # Refactoring
```

Examples: `feature/redis-sink`, `fix/loop-guard-window`, `docs/readme-rewrite`

## PR Guidelines

1. **One feature or fix per PR.** Keep changes focused.
2. **Branch from `main`**, push your branch, open a PR.
3. **Include tests** for any new SDK functionality.
4. **Run lint and tests locally** before pushing:
   ```bash
   ruff check sdk/agentguard/
   python -m pytest sdk/tests/ -v --cov=agentguard --cov-fail-under=80
   ```
5. **Reference the GitHub issue** in your PR description (e.g., "Closes #42").
6. **CI must pass** — tests on Python 3.9–3.12 + lint.

## Commit Messages

Use clear, imperative messages:

```
Add FuzzyLoopGuard for alternation detection
Fix BudgetGuard warning callback not firing at threshold
Update README with LangGraph integration example
```

## CI

CI runs on every push and PR via GitHub Actions (`.github/workflows/ci.yml`):

- **Tests**: `pytest` across Python 3.9, 3.10, 3.11, 3.12 with `--cov-fail-under=80`
- **Lint**: `ruff check sdk/agentguard/`
- **Coverage**: uploaded as artifact on Python 3.12 runs

## Issue Labels

| Prefix | Values |
|--------|--------|
| `component:` | sdk, dashboard, api, infra |
| `type:` | feature, bug, refactor, docs, test, ci, security, perf |
| `priority:` | critical, high, medium, low |

## Project Board

Track issues and progress: https://github.com/users/bmdhodl/projects/4

## License

SDK is MIT licensed (BMD PAT LLC). By contributing, you agree your contributions are licensed under MIT.
