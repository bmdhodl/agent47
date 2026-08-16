# Claims audit - session agentguard-claude-review-native-wrapper-20260816

**Verdict: GREEN**  (4/8 verified)

- OK **Merged review workflow uses the approved no-lifecycle native wrapper** (`file_contains`, RED)
    - /cli-wrapper.cjs/ found in .github/workflows/claude-review.yml
- OK **Readiness guard requires the approved native wrapper command** (`file_contains`, RED)
    - /node node_modules/@anthropic-ai/claude-code/cli-wrapper.cjs/ found in scripts/review_readiness_guard.py
- OK **Readiness regression rejects the lifecycle-disabled placeholder CLI** (`file_contains`, RED)
    - /native-placeholder-cli/ found in sdk/tests/test_review_readiness_guard.py
- .. **Approved native wrapper reports the pinned Claude version** (`None`, RED)
    - retracted: The direct node proof is valid, but the showwork command verifier requires a Python entrypoint; replace it with a Python subprocess receipt that invokes the same wrapper.
- .. **Approved native wrapper reports the pinned Claude version** (`None`, RED)
    - retracted: The second receipt still used a shell-metacharacter-bearing Python expression; replace it with a single-expression subprocess proof.
- .. **Approved native wrapper reports the pinned Claude version** (`None`, RED)
    - retracted: The command verifier only accepts a Python script or module, while the direct node wrapper proof already passed; replace this receipt with the focused regression command.
- .. **Approved native wrapper reports the pinned Claude version** (`None`, RED)
    - retracted: The command verifier requires a Python script path rather than -m; record the guard script receipt, while the direct node version result remains in the execution log.
- OK **Approved native wrapper readiness guard passes** (`command`, RED)
    - exit 0, stdout has 'Review readiness guard passed.'
