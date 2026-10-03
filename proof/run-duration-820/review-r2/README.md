# Final review proof for issue #820

Windows, 2026-10-03. Supersedes the initial proof above after Copilot found
that `math.isfinite` raises OverflowError for an unrepresentable JSON integer.
The new conversion catches that specific representability failure for both
timestamps and durations, then ignores unusable timing. Booleans, strings,
NaN and infinity are also excluded. Usable timing still gives the elapsed span
timeline or the existing duration-only fallback. Timestamp units are now explicit.

## Verification

- Before this review fix: the original #823 wheel produces **6 expected
  failures / 35 passes** in the updated 41-case regression. Both actual CLI
  commands fail with OverflowError on oversized-sample.jsonl (exit 1).
- After: clean Windows/Python **3.9.6 and 3.13.2** installed wheels each pass
  **41 cases**, 0 skips/errors/warnings. Both actual CLI commands exit zero
  and report **400 ms** on the oversized fixture. The original sequential
  fixture remains **446.6 ms** in both JSON outputs. Fixtures are offline.
- The candidate is installed without dependencies and tested outside the
  checkout without its conftest, using isolated Python, explicit UTF-8 and
  plugin autoload off. Owner-provider credentials are scrubbed; optional
  providers are absent. All 49 source/installed package files and metadata
  equal the exact candidate archive, and archive CRC passes. Python 3.9's pip
  does not record a digest in direct_url; this is flagged in its receipt.
- Full SDK: **1,479 passed / 3 optional Agents skips / 92.38% coverage**,
  0 warnings. All configured Ruff/Bandit/docs/CI-tools/review-readiness/release
  and generated-README checks pass; MCP 11 tests pass.

Final candidate wheel SHA-256:
`3671cd33312a4c8dcffec8db8a4459a175ebe5cc9b16c0074c23d1c1aa3ba009`.
Original #823 wheel SHA-256:
`f864b1e9b79ac2fb55a031275d6d49cda2eb768795266c0d3c811f83e955ae8f`.
Executed test-file bytes SHA-256: `80bcb4aa2149a36c2722abdd484391eb8c1d5f160ea5bf86dad31c2e239625f2`. Repository line-ending
conversion can change archived test bytes. The manifest hashes repository LF
text bytes and exact gzip bytes. Gzip retains the path-normalized full-suite
and failing-run logs without crowding the automated review diff; decompress
with Python gzip.open(path, 'rt', encoding='utf-8'). Gzip CRC and decompressed
bytes were checked against the normalized original logs. Raw local logs remain
private. Showwork certifies saved artifacts, not a behavioral rerun.

No new public API, JSON keys, runtime guard, dependency, workflow, inference,
telemetry or release is added. Multi-run files include gaps; missing timing
keeps the documented fallback/unknown behavior. The longest-span evaluation
assertion is unchanged. Outside adoption and #817 remain separate gates.
