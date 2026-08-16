# Claims audit - session agentguard-scorecard-pin-20260816

**Verdict: GREEN**  (4/4 verified)

- OK **Claude review workflow uses the checked-in npm lockfile** (`file_contains`, RED)
    - /npm ci --no-audit --no-fund/ found in .github/workflows/claude-review.yml
- OK **Claude review dependency lockfile exists** (`file_exists`, RED)
    - .github/claude-review/package-lock.json exists
- OK **Review-readiness guard requires the lockfile-backed local npm ci and local Claude CLI path** (`file_contains`, RED)
    - /npm ci --no-audit --no-fund/ found in scripts/review_readiness_guard.py
- OK **Review-readiness tests cover semantic 300-second timeout and package-lock contract** (`file_contains`, RED)
    - /test_workflow_requires_semantic_three_hundred_second_timeout/ found in sdk/tests/test_review_readiness_guard.py
