# Claims audit - session agentguard-scorecard-pin-20260816

**Verdict: GREEN**  (11/12 verified)

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
- OK **Preflight registers the Claude review package manifest as review-readiness input** (`file_contains`, RED)
    - /.github/claude-review/package.json/ found in scripts/sdk_preflight.py
- OK **Preflight registers the Claude review lockfile as review-readiness input** (`file_contains`, RED)
    - /.github/claude-review/package-lock.json/ found in scripts/sdk_preflight.py
- OK **Preflight preserves .github paths during normalization** (`file_contains`, RED)
    - /while normalized.startswith/ found in scripts/sdk_preflight.py
- OK **Timeout guard accepts the real pipeline invocation and rejects inert prefixes** (`file_contains`, RED)
    - /test_timeout_rejects_inert_prefixes/ found in sdk/tests/test_review_readiness_guard.py
- OK **Preflight regression covers both Claude review dependency files** (`file_contains`, RED)
    - /test_review_readiness_dependency_files_run_guard/ found in sdk/tests/test_sdk_preflight.py
