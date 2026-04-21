# Gitleaks Issue 376 Proof

Issue `#376` reported two P0 `generic-api-key` findings in git history.

Classification:
- Both findings point to historical docs/example usage of the placeholder
  `ag_live_abc123` in `sdk/agentguard/guards.py`.
- Current source/docs paths do not contain that placeholder.
- This is not a real provider credential, so no rotation is available or needed.
- History rewrite is not justified because it would disrupt the public repo for
  a non-secret placeholder.

Remediation:
- Added `.gitleaksignore` entries scoped to the two exact historical
  fingerprints.
- Kept redacted before/after scan reports in this proof folder.

Validation:
- Before classification, `gitleaks detect --source . --redact --report-format
  json --report-path
  proof\gitleaks-376-2026-04-21\gitleaks-redacted-before.json --exit-code 0`
  was run intentionally with `--exit-code 0` so the redacted report could be
  captured without stopping automation. The report contains the two expected
  placeholder findings from issue `#376`.
- After classification, `gitleaks detect --source . --redact --no-color
  --no-banner --report-format json --report-path
  proof\gitleaks-376-2026-04-21\gitleaks-redacted-after.json --exit-code 1`
  exited `0`, and the after report is `[]`.
- `git grep -n "ag_live_abc123" -- sdk mcp-server site docs examples ops
  memory` returned no current source/docs matches.
