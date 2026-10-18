# Hosted MCP metadata correction proof

Observed 2026-10-18. This is repository and package-preparation evidence, not publication or live-account proof.

## Reproduction and local checks

Before the copy correction, `python -m pytest sdk/tests/test_mcp_registry_metadata.py -q` returned **3 failed, 5 passed**. The failures were the missing closed-account discovery descriptions, missing notice before `npx`, and missing existing-account key description. After correction the same command returned **8 passed**.

| Check | Result |
|---|---|
| Full SDK suite with coverage | 1681 passed, 3 skipped; 92.72% coverage, above the 80% floor |
| Structural suite | 9 passed |
| MCP `npm test` (includes TypeScript build) | 11 passed, zero skips |
| CI-tool pin guard | Passed |
| Review-readiness guard | Passed |
| Ruff, Makefile file inventory | Passed |
| Bandit, Makefile arguments | Passed |
| PyPI README synchronization | Passed |
| Release metadata guard | Passed |
| `git diff --check` | Passed |
| Official registry JSON Schema | Local `server.json` valid; description 94 of 100 allowed characters |
| Actual local `npm pack` archive | README notice precedes `npx`; package description includes the local SDK path |

Full-suite command: `python -m pytest sdk/tests/ -q --cov=agentguard --cov-report=term --cov-fail-under=80` with checkout-local SDK imports and an isolated temporary root. Local Python was 3.13.2. Three existing Agents SDK cases skipped because the optional `agents` package is absent. The required floor/current compatibility CI jobs remain separate gates.

The first dependency install failed on a shared npm cache collision. Repeating `npm ci` with an isolated cache passed. No dependency or lockfile changed.

Two independent correctness and house-style/scope reviews found no actionable issue. Both checked the diff before reading the implementation narrative.

The first-commit Codex review found no issue. Copilot and Bugbot reported quota skips. The rendered README was checked in headless Chrome on GitHub; the notice and local SDK command are visible before the server installation. The screenshot is [`readme-preview.png`](readme-preview.png).

Main advanced with #883 during review. Its guard-limit documentation and tests were synchronized without changing this PR's metadata diff. The showwork receipt explicitly acknowledges that imported document; the tracked session gate covers 7 checks and 5 declared metadata artifact requirements. The full-suite counts above precede this main synchronization; final-head focused checks and CI are recorded in the PR.

## Public readback and unfinished acceptance

[`readback.json`](readback.json) records primary-source npm and MCP Registry readback, official schema validation, and the local archive hash. Public npm remains 0.2.2 without the notice. The official registry has historical 0.2.1 and latest 0.2.2 entries. Neither was modified.

- No npm or Registry publication occurred; the account-admission notices still need public readback after an approved metadata release.
- No existing-account live smoke ran: this process has no configured `AGENTGUARD_API_KEY`. The passing bearer-auth client test uses a fixture, not a hosted account.
- Dependency audit reports the existing `@modelcontextprotocol/sdk` high and `proxy-addr` critical advisories. They are already tracked in [#878](https://github.com/bmdhodl/agent47/issues/878), with upgrade PRs [#865](https://github.com/bmdhodl/agent47/pull/865) and [#848](https://github.com/bmdhodl/agent47/pull/848). This metadata patch does not remediate them.
- SDK/runtime code, versions, dashboard, credentials and registry history stay unchanged.

Sign-off: OpenAI | GPT-6.1 Sol | xhigh
