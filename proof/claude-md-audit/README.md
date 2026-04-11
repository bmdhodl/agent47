# Claude MD Audit Proof

Artifacts in this folder support the `CLAUDE.md` audit PR.

- `check.txt`: full SDK pytest + coverage run on the branch head
- `preflight.txt`: output from `python scripts/sdk_preflight.py`
- `release-guard.txt`: output from `python scripts/sdk_release_guard.py`
- `token-counts.txt`: before/after size counts for `CLAUDE.md`
- `lint.txt`: full local `ruff` output; included to show current repo-wide lint debt outside this docs-only change
- `security.txt`: local bandit output captured during the audit pass; empty file means no findings were emitted

This PR is docs-only. The key proof is the audit document plus the prompt-size reduction captured in `token-counts.txt`.
