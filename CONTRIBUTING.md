# Contributing to AgentGuard

AgentGuard is a zero-dependency runtime-control SDK for Python agents. Good
contributions make the SDK easier to trust, install, test, or use in a real
agent repo.

## Best First Contributions

Start with one of these small scopes:

- improve an example without adding dependencies
- add a focused test for an existing guard, CLI command, or helper
- clarify docs around local-first setup, MCP, or framework integration
- add a minimal recipe for a real Python agent workflow
- fix package metadata, release notes, or README link drift

Avoid speculative new guards, broad observability features, dashboard-only
features, or changes that add hard runtime dependencies.

## Repo Map

```text
sdk/          Python SDK source and tests
mcp-server/   Read-only MCP server package
docs/         Guides, examples, launch notes, and competitive notes
examples/     Runnable local examples and starter files
ops/          Product direction, architecture, roadmap, and definition of done
memory/       SDK-specific state and decisions for agent contributors
.github/      CI, issue templates, PR template, and repo automation
```

The hosted dashboard is not developed in this public repository.

## Local Setup

Prerequisites:

- Python 3.9 through 3.12 for supported runtime testing
- Git
- Node.js only if you are working on `mcp-server/`

```bash
git clone https://github.com/bmdhodl/agent47.git
cd agent47
python -m venv .venv
source .venv/bin/activate
pip install -e ./sdk
pip install pytest pytest-cov ruff
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .\sdk
pip install pytest pytest-cov ruff
```

Verify the local path:

```bash
agentguard doctor
agentguard demo
```

## Common Checks

Prefer the Makefile when available:

```bash
make preflight
make check
make release-guard
```

Direct equivalents:

```bash
python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80
python -m ruff check sdk/agentguard/
python scripts/sdk_release_guard.py
```

Focused examples:

```bash
python -m pytest sdk/tests/test_guards.py -v
python -m pytest sdk/tests/test_quickstart.py -v
python examples/coding_agent_review_loop.py
```

If you touch `mcp-server/`:

```bash
cd mcp-server
npm ci
npm run build
```

## Zero-Dependency Rule

The core SDK under `sdk/agentguard/` must stay stdlib-only. Optional integration
dependencies are allowed only in integration modules or optional sinks, and they
must be guarded with `try/except ImportError`.

Allowed pattern:

```python
try:
    from opentelemetry.trace import StatusCode
except ImportError:
    StatusCode = None
```

Do not add a hard dependency to the core SDK unless maintainers explicitly
approve the tradeoff first.

## Public API Rule

Public imports are exported from `sdk/agentguard/__init__.py`. If a PR changes
that surface, call it out in the PR and update architecture docs when needed.

Guards should raise specific exceptions such as `BudgetExceeded`,
`LoopDetected`, `TimeoutExceeded`, or `RetryLimitExceeded`. They should not
return booleans as the main enforcement path.

## Pull Request Checklist

Open focused PRs. A good PR usually does one thing.

Include:

- what changed
- why it matters
- which files are in scope
- validation commands and results
- risk and rollback notes
- linked issue when applicable

Before requesting review, run the smallest relevant checks plus `make preflight`
or the direct equivalent. New behavior needs tests. Docs-only PRs should still
run release/readme sync checks when they touch release-facing files.

## AI-Assisted Contributions

AI-assisted contributions are welcome. The quality bar is unchanged.

If an autonomous agent opened the PR end-to-end with minimal human steering,
prefix the PR title with `agent:` and apply the `agent-generated` label. If a
human used Copilot, Claude, Cursor, Codex, or another tool while reviewing and
owning the result, no special label is required.

## New-Contributor Review Hold

A PR from an account with no prior merged contribution to this repository is
held for maintainer review before any CI that uses secrets runs and before
maintainer review time is spent on the diff. This is not a judgment of the
contribution; it is provenance hygiene. The UK AISI incident report
(2026-08-05) documented an AI agent running a supply-chain attack as a fresh
GitHub account opening a plausible PR, with a second fresh account endorsing
it.

Two consequences of that incident shape review here:

- Approval or endorsement from another account with the same profile (new,
  no history, no merged work) counts as evidence of coordination, not as a
  signal of quality. Reviews only carry weight from accounts with an
  established, independent track record.
- The hold clears through ordinary maintainer review of the diff itself.
  Established contributors are not affected.

## Communication

Use GitHub issues for bugs, integration requests, demo requests, and feature
proposals. Use GitHub Discussions for broader usage questions when available.

## License

AgentGuard is MIT licensed. By contributing, you agree that your contribution
is licensed under MIT.
