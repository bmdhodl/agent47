# Follow-up

- Recheck the Glama rendered listing and the "no recent usage" checklist item
  with the read key. The public API still returned `tools: []` on 2026-08-15;
  do not change SDK or MCP runtime code solely to chase that directory signal.
- Apply [docs/guides/bmdpat-measurement-contract.md](../docs/guides/bmdpat-measurement-contract.md)
  in the bmdpat classifier so landing-page hits stop arriving as `install_intent`.
- 1.4.0 candidate is the merged AG-01 through AG-05 slice. Do not tag it
  from this prep branch until `make release-guard` is green and the owner
  chooses the tag. AG-06 stays open: it needs an approved public API, and
  the week-four gate has no external repeat user, so later adapters stay held.
- AG-05 / #734 reserves store-backed streams on the AG-04 ledger. Windows was not executed for the stream spawn
  race; Linux was. The AG-04 non-stream race has the same Windows gap.
- Claude PR review truncates `gh pr diff` at 200k bytes and `.showwork`
  sorts first. Keep `.showwork/snapshots/*.json` as `text eol=lf -diff` so
  SDK patches stay visible. Workflow changes on a PR do not apply until
  merge (`pull_request_target` uses the base workflow).
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
