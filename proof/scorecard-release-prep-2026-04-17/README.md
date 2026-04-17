Scorecard and release-prep proof for 2026-04-17.

Scope:
- reduce repo-owned OpenSSF Scorecard findings
- prepare the repo for the `1.2.8` SDK release candidate

Artifacts:
- `scorecard-alerts-before.json`: raw Scorecard code-scanning alerts before this branch
- `scorecard-open-summary-before.txt`: concise summary of the open alert set before remediation
- `branch-protection-before.json`: branch protection state before requiring 1 approval
- `branch-protection-after.json`: branch protection state after requiring 1 approval on `main`
- `ci-tools-install-py39.txt`: hashed toolchain install proof on Python 3.9
- `ci-tools-install-py311.txt`: hashed toolchain install proof on Python 3.11

Expected effect after merge:
- `PinnedDependenciesID` alerts for mutable `node:22-alpine` base images should clear
- `PinnedDependenciesID` alerts for unhashed workflow `pip install` commands should clear
- `CodeReviewID` should improve because `main` now requires 1 approving review

Known remainder after this branch:
- `FuzzingID` is still open; no fuzz target or ClusterFuzzLite setup has been added in this pass
- `CIIBestPracticesID` is still tied to the external OpenSSF badge/project state
- `MaintainedID` is still a repo-age / external timing signal
- Glama-related distribution work remains blocked by `memory/blockers.md` and is out of scope for this branch
