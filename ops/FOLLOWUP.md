# Follow-up

- Recheck the Glama rendered listing and the "no recent usage" checklist item
  with the read key. The public API still returned `tools: []` on 2026-08-15;
  do not change SDK or MCP runtime code solely to chase that directory signal.
- Apply [docs/guides/bmdpat-measurement-contract.md](../docs/guides/bmdpat-measurement-contract.md)
  in the bmdpat classifier so landing-page hits stop arriving as `install_intent`.
- 1.4.0 shipped 2026-09-24 (AG-01 through AG-05). AG-06 stays open: it
  needs an approved public API, and the week-four gate has no external repeat
  user, so later adapters stay held.
- 1.4.1 adds `agentguard --version` (owner-approved 2026-09-25). After the
  tag, confirm the `published-wheel.yml` matrix and PyPI attestations and add
  `proof/v1.4.1/PUBLICATION.md`.
- Gemini thinking may be under-billed. `resolve_billable_cost` reads
  `usage_metadata.candidates_token_count` as output and never reads
  `thoughts_token_count`, which Google reports outside candidates and bills
  at the output rate. Confirm with a real payload fixture before changing
  `_extract_usage_object`.
- The v1.4.0 GitHub Release has an unsigned PNG asset
  (`agentguard-1.4.0.png`), which keeps Scorecard Signed-Releases at 0. Host
  release images outside release assets from now on.
- AG-05 / #734 reserves store-backed streams on the AG-04 ledger. Windows was not executed for the stream spawn
  race; Linux was. The AG-04 non-stream race has the same Windows gap.
- Claude PR review caps the diff at 200k bytes. The GitHub API diff ignores
  the `-diff` gitattribute, so `.github/claude-review/filter_diff.py` drops
  pip-compile locks, `.showwork` snapshots, and `package-lock.json` sections
  (and names them) before the cap. Add new bulk generated paths to its `OMIT`
  list. Workflow changes on a PR do not apply until merge
  (`pull_request_target` uses the base workflow).
- Keep the official MCP Registry readback in the weekly MCP train. It currently
  serves `0.2.2` as `isLatest: true`; the older `0.2.1` result is expected
  historical metadata.
- Record explicit external adoption evidence from three repeat users or design
  partners before broadening the SDK feature surface. Use issues, PRs, or
  user-provided proof; do not add telemetry to manufacture this signal.
- OpenSSF Scorecard remainder after the code-scanning workflow pass: Fuzzing
  (no ClusterFuzzLite on purpose), CII Best Practices still InProgress,
  Code-Review depends on human approvals, Signed-Releases is 0 because older
  GitHub Releases (`v1.3.0`, `v1.3.1`) attached unsigned proof png/zip files
  (`v1.3.2` is notes-only; PyPI attestations do not count), and the optional
  CrewAI extra still carries unresolved ChromaDB advisories tracked in `#644`.
  Do not add a fuzzer or a fake CrewAI bump to chase those scores. Do not
  upload more unsigned GitHub Release assets.
- Reviewed 2026-08-15: deferred issue `#686`'s optional OAA-signed local trace
  proposal. The external draft is not adopted yet, and its reference path uses
  `PyJWT` plus `cryptography`; adding it would require an explicit optional
  dependency and key-management contract. Revisit after spec adoption or an
  interoperability PR, not as a speculative core feature.
- Done 2026-08-15: built the current SDK candidate wheel and installed it into
  an isolated venv. `python -m agentguard`, `doctor`, `demo`, raw
  `quickstart --write`, generated-starter execution, `report`, and `badge` all
  completed without API keys or network. This is release-prep evidence only;
  the onboarding bundle remains unreleased until a new SDK tag is published.
- Done 2026-08-15: repeated the clean-wheel proof against candidate `1.2.14`.
  The isolated install reported `agentguard47==1.2.14` and completed the same
  local activation path without API keys or network. This remains a candidate
  proof until the release-prep PR lands and the tag workflow publishes it.
- Done 2026-08-15: `agentguard-mcp/agentguard_mcp/sync.py` validates opt-in
  `AGENTGUARD_SYNC_URL` values for an `http`/`https` scheme and hostname before
  starting the background executor. Private destinations remain allowed because
  this is an explicitly configured local hook; broad SSRF blocking remains a
  separate compatibility decision. Tests cover rejected schemes, missing hosts,
  and valid local HTTP URLs.
