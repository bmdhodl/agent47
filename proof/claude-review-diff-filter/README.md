# Claude review diff filter

Input: the squash diff of PR #777 (`git diff df1c552~1 df1c552`), Linux, Python 3.11.

```text
raw diff bytes: 249217
ci.yml inside the old 200k cap: False
filtered bytes: 31866
Generated files changed but omitted from this diff: .github/requirements/compat-floor.txt, .github/requirements/compat-latest.txt, .showwork/snapshots/ag-07-codex-p2.json, .showwork/snapshots/ag-07-compat-matrix.json
file sections kept: 17 (all code, tests, docs, workflow)
```

`python -m pytest sdk/tests/test_claude_review_filter.py -q`: 4 passed. The review-readiness guard and the CI guardrail tests pass.

The change takes effect after merge: `pull_request_target` runs the base branch workflow.
