# Contributing to AgentGuard

AgentGuard is a zero-dependency runtime-control SDK for Python agents. Good
contributions make the SDK easier to trust, install, test, or use in a real
agent repo.

## Best First Contributions

Start with one of these small scopes:

- improve an example without adding dependencies
- add a focused test for an existing guard, CLI command, or helper
- add a provider usage fixture ([Add A Compatibility Fixture](#add-a-compatibility-fixture))
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

## Add A Compatibility Fixture

If AgentGuard counts the wrong usage or cost for your provider response,
a fixture is the fastest way to prove it. Plan on one session. You need no
API key, and the test sends nothing over the network.

1. Copy only the `model` and `usage` fields from one real response. Drop
   prompts, outputs, request ids, and keys.
2. Add that payload to `sdk/tests/fixtures/usage_payloads.py`. Name the
   provider, SDK version, and date in a comment:

   ```python
   # Anthropic Messages, anthropic==<version>, <date>. No cache fields.
   ANTHROPIC_HAIKU_NO_CACHE: Dict[str, Any] = {
       "model": "claude-3-5-haiku-20241022",
       "usage": {"input_tokens": 300, "output_tokens": 120},
   }
   ```

3. Import it in `sdk/tests/test_precision_cost.py`, then assert what
   AgentGuard should record: the token buckets and the cost from the price
   table, not only the source.

   ```python
   def test_anthropic_haiku_without_cache_fields_is_computed(self) -> None:
       model = "claude-3-5-haiku-20241022"
       resolved = resolve_billable_cost(
           ANTHROPIC_HAIKU_NO_CACHE,
           model=model,
           provider="anthropic",
           prices=DEFAULT_PRICE_TABLE,
       )
       self.assertEqual(resolved["source"], SOURCE_COMPUTED)
       self.assertEqual(resolved["tokens"]["input"], 300)
       self.assertEqual(resolved["tokens"]["output"], 120)
       rates = DEFAULT_PRICE_TABLE["rates"][("anthropic", model)]
       expected = (300 * rates["input_per_1m"] + 120 * rates["output_per_1m"]) / 1_000_000
       self.assertAlmostEqual(resolved["cost_usd"], expected)
   ```

4. Run `python -m pytest sdk/tests/test_precision_cost.py -q`.

If the test passes, open a PR. The fixture keeps that shape covered. If it
fails because AgentGuard is wrong, open a bug report with the payload and
the failing assertion, or send the fix in the same PR. Do not weaken the
assertion to make it pass. If AgentGuard counted the call correctly and the
problem is elsewhere, say so in the issue. That still helps.

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

Open every PR ready for review. Do not open a draft.

`.showwork/snapshots/*.json` is marked `-diff`. The patch shows
`Binary files differ` instead of the JSON body, so a snapshot change is
visible but not readable in `gh pr diff`. The session JSONL hash chain is
the content check. This keeps the Claude review 200k cap from being filled
by tree snapshots before SDK code.

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
