CI failure triage from the dogfood operator run:

- Failing test: `sdk/tests/test_ci_guardrails.py::test_actionlint_workflow_is_wired`.
- Cause shown in the failed job log: the test still expects `actions/setup-go@40f1582b2485089dde7abd97c1529aa768e1baff # v5`, while this Dependabot PR updates `.github/workflows/actionlint.yml` to `actions/setup-go@4a3601121dd01d1626a1e23e37211e3254c1c06c # v6.4.0`.
- Next action: update the CI guardrail expectation to the new pinned v6.4.0 action string, then rerun CI.

No SDK runtime change appears needed for this PR.
