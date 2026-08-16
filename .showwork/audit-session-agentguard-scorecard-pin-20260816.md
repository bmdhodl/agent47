# Claims audit - session agentguard-scorecard-pin-20260816

**Verdict: RED**  (1/2 verified)

- XX **Claude review workflow uses the checked-in npm lockfile** (`file_contains`, RED)
    - /npm ci --no-audit --no-fund/ NOT in .github/workflows/claude-review.yml
- OK **Claude review dependency lockfile exists** (`file_exists`, RED)
    - .github/claude-review/package-lock.json exists

## 1 gap(s) - a claimed 'done' is not real

- [RED/fail] Claude review workflow uses the checked-in npm lockfile - /npm ci --no-audit --no-fund/ NOT in .github/workflows/claude-review.yml
