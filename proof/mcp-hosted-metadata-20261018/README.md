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

Author sign-off: Codex agent, OpenAI | gpt-6.1-sol | xhigh. This identifies the implementation session, not an independent reviewer.

## Review correction, 2026-10-19

The prior closeout missed two Claude issue comments. The README contract now
fails explicitly when the `npx` install command is absent. The 100-character
schema limit applies only to the Registry description. A missing API-key
declaration now produces a descriptive assertion instead of `StopIteration`.

Three mutation probes against the pre-fix test file reproduced all three
findings (3 failed). After the correction, those probes plus the eight metadata
tests passed (11 passed). The probes substitute temporary README/metadata
fixtures; they do not modify the real package or README.

The earlier session receipt contains three append-only finish events after
additional claims. These are separate re-verifications, not rewritten history.
Its artifact-only requirements do not prove live-account or publication
acceptance. The correction uses a fresh session,
`qw-20261019-mcp-metadata-review`, with all requirements and claims before one
gated finish. Prior ledger files remain unchanged. The first close attempt was
refused because SDK validation changed an ignored local `traces.jsonl` file.
A shell sequence incorrectly continued to commit without the finish event;
the corrective receipt commit records that generated artifact and includes the
successful gate. The refusal was not bypassed or represented as a pass.

The rendered README and package metadata are unchanged by this correction.
Publication and existing-account smoke remain unfinished as described above.

Correction validation: full SDK suite **1687 passed, 3 optional Agents SDK
skips**; structural **9 passed**; MCP build/tests **11 passed**. CI-tool pins,
review-readiness guard, Ruff, Bandit, release guard and whitespace checks passed.
The full suite enforced the existing 80% coverage floor on Python 3.13.2.
Independent correctness/security and house-style/scope lenses passed. Exact
pushed-head CI and remote review results belong to the PR timeline.
