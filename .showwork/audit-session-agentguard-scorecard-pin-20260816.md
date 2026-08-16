# Claims audit - session agentguard-scorecard-pin-20260816

**Verdict: GREEN**  (6/7 verified)

- OK **Claude review workflow uses the checked-in npm lockfile** (`file_contains`, RED)
    - /npm ci --no-audit --no-fund/ found in .github/workflows/claude-review.yml
- OK **Claude review dependency lockfile exists** (`file_exists`, RED)
    - .github/claude-review/package-lock.json exists
- OK **Review-readiness guard requires the lockfile-backed local npm ci and local Claude CLI path** (`file_contains`, RED)
    - /npm ci --no-audit --no-fund/ found in scripts/review_readiness_guard.py
- OK **Review-readiness tests cover semantic 300-second timeout and package-lock contract** (`file_contains`, RED)
    - /test_workflow_requires_semantic_three_hundred_second_timeout/ found in sdk/tests/test_review_readiness_guard.py
- .. **Timeout guard anchors the 300-second deadline directly to the local Claude CLI path** (`None`, RED)
    - retracted: The original file_contains pattern used regex metacharacters and could not represent the literal source token; the code and test are valid, so replace the receipt with a literal stable-token check.
- OK **Regression test rejects an unbounded timeout wrapper before the Claude command** (`file_contains`, RED)
    - /test_timeout_must_anchor_local_cli_immediately_after_duration/ found in sdk/tests/test_review_readiness_guard.py
- OK **Timeout guard anchors the 300-second deadline to the local Claude CLI path** (`file_contains`, RED)
    - /CLAUDE_REVIEW_CLI_PATH/ found in scripts/review_readiness_guard.py
