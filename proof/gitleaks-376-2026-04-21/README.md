# Gitleaks Issue 376 Proof

Issue `#376` reported two P0 `generic-api-key` findings in git history.

Classification:
- Both findings point to historical docs/example usage of the placeholder
  `ag_live_abc123` in `sdk/agentguard/guards.py`.
- The current tree does not contain that placeholder.
- This is not a real provider credential, so no rotation is available or needed.
- History rewrite is not justified because it would disrupt the public repo for
  a non-secret placeholder.

Remediation:
- Added `.gitleaksignore` entries scoped to the two exact historical
  fingerprints.
- Kept redacted before/after scan reports in this proof folder.

