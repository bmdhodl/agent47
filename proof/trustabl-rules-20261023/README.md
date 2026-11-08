# Trustabl rules-tag guard

The workflow now refuses to scan unless `v0.2.0` resolves to inspected commit
`97918c43909166334a2df941cff64d9f63acb115`. The verifier uses the renamed
`trustabl/agent-reliability-rules` repository, dereferences an annotated tag,
and fails on API errors, invalid objects or mismatches. A mismatch prints the
tag, expected commit and resolved commit.

The action SHA, scanner v0.1.6, rules v0.2.0, permissions, telemetry setting,
advisory findings and required nonempty scan outputs stay unchanged. This is a
check before the scanner fetches its rules; it does not make the downstream
mutable-tag fetch atomic. No release or deployment is part of this change.

`baseline-regression.json` records the workflow assertion failing against base
`2afad9cde06926da785e7d6657cc465d03df5503` before implementation. The initial
new-test run also failed because the verifier did not exist.
`local-checks.json` retains commands, exit codes and outputs with host paths
replaced by placeholders. Full SDK coverage, structural checks, native guards,
lint, security, generated README parity and MCP tests passed. Three optional
Agents SDK tests are skipped because that extra is absent; the hosted floor
job separately tests its declared real dependencies. Windows pytest emitted a
post-success temporary-directory cleanup PermissionError after exit 0.

Independent correctness/security and house-style reviewers passed both
evidence-first and plan-review phases, without findings. Correctness review
independently passed the 12 focused tests and 12 additional malformed-response
and input probes; its fixture token did not appear in diagnostics.

Live workflow runs and final-head hosted checks are recorded on the PR after
push. Local test success alone does not establish that evidence.

API contract: [Git references](https://docs.github.com/en/rest/git/refs#get-a-reference)
and [annotated tags](https://docs.github.com/en/rest/git/tags#get-a-tag).

Sign-off: OpenAI | gpt-6.1-sol | xhigh.
