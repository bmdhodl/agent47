# Claude Code native retry-wait boundary (#876)

Author: Codex, OpenAI `gpt-6.1-sol`, reasoning `xhigh`. Checked 2026-10-20.

## Change and source

The hook guide and enforcement map now name the native Claude Code API retry
and usage-limit waiting boundary. AgentGuard only receives installed tool-hook
events or instrumented Python usage/checks. It cannot interrupt a native host
wait, infer account quota or supply a process watchdog.

Primary source: [Anthropic's Claude Code v2.1.301 release](https://github.com/anthropics/claude-code/releases/tag/v2.1.301),
published 2026-10-15. Its release body confirms
`CLAUDE_CODE_RETRY_WATCHDOG_MAX_USAGE_LIMIT_WAIT_MS` in unattended retry mode
(`CLAUDE_CODE_RETRY_WATCHDOG`). The docs describe that request wait limit without
inventing activation values, defaults or retry counts. A total session deadline
requires host/process supervision outside this hook.

## Reproduction and verification

Before the docs changed:

```text
python -m pytest sdk/tests/test_enforcement_boundary.py::test_regression_claude_native_retry_wait_boundary -q
1 failed: the native wait-limit variable was missing from the hook guide
```

Afterward, the same regression and existing offline cooperative guard/background
checks pass: **30 passed**. These tests demonstrate the existing SDK boundary;
they do not activate or time Claude Code's real native retry mode.

Full SDK suite: **1688 passed / 3 skipped**, **92.65% coverage** (80% floor).
The skips are the existing optional OpenAI Agents package checks because that
extra is absent locally. Structural: **9 passed**. MCP build and tests:
**11 passed**. Native Ruff, Bandit, CI-tool pins, review-readiness, release
metadata, generated PyPI README sync and whitespace checks all pass.

Commands follow the Makefile `check`, `structural`, `security` and
`release-guard` targets, using direct Python/npm equivalents on Windows. The
canonical runner removes inherited `AGENTGUARD_*` settings and uses an isolated
pytest basetemp. The existing npm dependency audit findings remain tracked in
[#878](https://github.com/bmdhodl/agent47/issues/878); this documentation change
does not remediate them.

Two independent review sessions passed correctness and style/scope lenses.
The correctness reviewer independently reran all 30 focused tests. No actionable
findings or edits resulted. No runtime code, host settings, dependencies, package
metadata, release or site files change. No provider requests are required.

Showwork artifact acceptance and the committed receipt are separate from test
behavior and remote CI. Independent QA/merge and accepted-source verification
remain required after this PR is prepared.
