Run13 dogfood repo-health sweep rechecked this failure.

Current failure root cause: `sdk/tests/test_ci_guardrails.py::test_actionlint_workflow_is_wired` still asserts the old pinned setup-go v5 action:

`actions/setup-go@40f1582b2485089dde7abd97c1529aa768e1baff # v5`

This PR updates `.github/workflows/actionlint.yml` to:

`actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c # v6.4.0`

Next action: update the guardrail test expectation for the new pinned setup-go v6.4.0 SHA, then rerun CI. Failed-log proof is saved in PR #506 artifacts at `proof/dogfood/2026-05-23/run13/pr-508-failed-log.txt`.
