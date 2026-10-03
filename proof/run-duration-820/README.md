> **Superseded:** this initial proof predates the oversized timing fix.
> Use [final review proof](review-r2/README.md) for the current candidate.

# Elapsed span timeline: issue #820

Windows, 2026-10-02, unpublished AgentGuard 1.4.1 candidate. `report`,
`summarize_trace` and `incident` now use the earliest span start through the
latest span end in the supplied trace, reporting the elapsed timeline. Sequential gaps count; overlapping and
nested spans are not summed. Duration-only legacy traces retain the longest
span fallback. The existing `EvalSuite.assert_completes_within` assertion
continues testing the longest individual span; no exports or JSON keys change.
Validation finished on 2026-10-02; this proof was prepared on 2026-10-03.

## Verification

- Previous #822 wheel: 18 expected regression failures / 17 passes, 0 errors
  or skips. Fixed wheel: all 35 cases pass on Windows/Python 3.9.6 and 3.13.2,
  0 skips or warnings. Cases independently cover summary, CLI JSON/text, and
  incident JSON/Markdown with sequential, overlapping, nested, unordered,
  timestamp-only, legacy/end-only, backward-clock and incomplete traces.
  Non-span events and invalid/nonfinite timing do not distort the timeline.
- Actual installed CLI commands against sample.jsonl reproduce the issue:
  previous `report` and `incident` show **153.0 ms**; both fixed profiles show
  **446.6 ms**. All commands exit zero. Each profile retains JSON and text
  output. The fixture reproduces the issue's timestamps, not new inference.
- Clean virtual environments install the wheel without dependencies; copied
  tests run outside the checkout, without its conftest, using isolated Python
  with plugin autoload off and owner-provider credentials scrubbed. Optional
  provider packages are absent. All 49 installed package files and metadata
  match the wheel; archive CRC and all 49 candidate source files also match.
  Python 3.9's pip leaves archive_info empty: the receipt records that missing
  installer digest. Archive SHA and installed-byte comparisons still ran.
- Full SDK: **1,473 passed / 3 optional Agents skips / 92.37% coverage**,
  0 warnings. Configured Ruff, Bandit, docs, CI-tools/review-readiness/release
  guards and generated PyPI README pass; MCP 11 tests pass. Logs and exit
  results are under checks/.

Fixed wheel SHA-256: `f864b1e9b79ac2fb55a031275d6d49cda2eb768795266c0d3c811f83e955ae8f`.
Previous #822 wheel SHA-256:
`193d5d5cd5ff75222d89e6d29953d510608f44acd499b3e4a8ea96512eb38188`.
Executed Windows regression bytes SHA-256: `0413cd0b8a17c55280cd0626b33a50a4786c312613afb6e652db5eb5596063bd`. Repository
line-ending conversion can change archived test bytes. The manifest hashes
repository LF bytes; public logs use UTF-8 and neutral path labels. Original
local logs are retained privately. An initial build hit a Windows file lock
in existing build output; the final wheel was built from a fresh copy of the
49 SDK files plus packaging inputs, without reusing that output directory.
The baseline failure log was rerun with explicit UTF-8 after its Windows
code-page output could not be decoded as UTF-8; the original bytes remain private.
Showwork checks certify saved artifacts, not a behavioral rerun.

## Limits

Duration is an approximation from recorded wall-clock timestamps. It includes
gaps between separate runs if they share the supplied file, and cannot recover
time outside recorded spans. If start/end timestamps are absent or unusable,
the longest valid recorded span is the fallback. Without either, CLI JSON
keeps null and omits the time line; trace/incident summaries retain zero.
No runtime guard, public API, dependency, workflow, inference, telemetry or
release tag is added. No outside-user adoption is claimed. #817 and the
Responses-floor workflow proposal remain separate owner gates.
