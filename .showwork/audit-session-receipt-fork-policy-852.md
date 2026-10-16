# Claims audit - session receipt-fork-policy-852

**Verdict: GREEN**  (2/3 verified)

- .. **Local CI refuses fork heads before checking out code and retains its failing summary for missing test groups.** (`None`, RED)
    - retracted: The direct 54-test command passed. Showwork only accepts repository scripts for command checks and treated -m as a missing script; replace this unsupported invocation with narrower supported checks.
- OK **The local CI summary declares its fork refusal before any checkout.** (`file_contains`, RED)
    - /name: Refuse fork code on local runners/ found in .github/workflows/ci.yml
- OK **The required CI gate rejects missing job outcomes.** (`command`, RED)
    - exit 1
