# Ops-cadence price check proof (2026-10-05)

The weekday `ops-cadence.yml` run warns when the price table is more than 90
days old. It read the date with a `sed` for a literal
`LAST_UPDATED = "YYYY-MM-DD"` line in `sdk/agentguard/cost.py`. Since #792
that line is `LAST_UPDATED = DEFAULT_PRICE_TABLE["last_updated"]`, so the
`sed` printed nothing and every run would post a false "missing or
unparseable" warning.

The `sed` now reads `"last_updated"` from `sdk/agentguard/price_table.py`,
where the date lives. The warning and reminder text name that file and the
`DEFAULT_PRICE_TABLE` markers. The date-shape check, the three failure modes,
the trigger, permissions and the `gh` calls do not change.

`test_ops_cadence_reads_the_price_table_date` in
`sdk/tests/test_ci_guardrails.py` takes the `sed` pattern and file from the
workflow and checks that it extracts exactly `DEFAULT_PRICE_TABLE["last_updated"]`.
If the date moves again, this test fails in CI.

`ops-cadence.yml` has been disabled since 2026-06-11. This change does not
turn it on. That stays the owner's call.

## Checks

Platform: Windows 11, Python 3.13.2, Git Bash 5.2.37. `make` is not installed,
so each command ran directly. Outputs are next to this README.

| File | Command | Result |
|---|---|---|
| `00-before-fix.txt` | new test and `verify.py` on the unchanged workflow | both fail; the `sed` finds `[]` |
| `01-workflow-step.txt` | run block of `ops-cadence.yml`, `gh` stubbed, Monday forced | today: `price_date=2026-09-26`, no warning; +100 days: re-verify reminder; renamed key: warning and "missing or unparseable" |
| `02-preflight.txt` | `python scripts/sdk_preflight.py` | exit 0 |
| `03-review-readiness.txt` | `python scripts/review_readiness_guard.py` | exit 0 |
| `04-ci-tools-guard.txt` | `python scripts/ci_tools_requirements_guard.py` | exit 0 |
| `05-structural.txt` | `pytest sdk/tests/test_architecture.py` | 9 passed |
| `06-guardrail-tests.txt` | `pytest sdk/tests/test_ci_guardrails.py sdk/tests/test_cost.py` | 37 passed |
| `07-lint.txt` | `ruff check` on `sdk/agentguard/` and the changed test | exit 0 |
| `08-release-guard.txt` | `python scripts/sdk_release_guard.py` | Release guard passed |
| `09-test.txt` | `pytest sdk/tests/ --cov=agentguard --cov-fail-under=80` | 1592 passed, 3 skipped; coverage 93% |

Not run here: `actionlint` and `shellcheck` are not installed on this host.
The Actionlint workflow runs both on this PR.

`09-test.txt` keeps the last 25 lines of the run, so it ends with the
`PermissionError` from pytest's `atexit` temp-dir cleanup, after the summary.
Python ignores it, and pytest exited 0. The coverage total comes from the
same run's `.coverage` data.

`price_step.py` writes the three test copies of the run block. It changes
only `DOW`, `now`, or the file the `sed` reads, and stops if a change does
not apply. It needs PyYAML (`pip install pyyaml`), which is not an SDK
dependency. Run it as `python price_step.py <repo> <out-dir>`, then run each
`step-*.sh` in Git Bash with `gh` stubbed and `BROKEN_TABLE` set to the
`broken_price_table.py` it writes. Convert the stub folder with `cygpath -u`
before you add it to `PATH`, and stop if `command -v gh` does not print the
stub path.

## Re-check

`python proof/ops-cadence-price-check/verify.py` checks the workflow text and
the FOLLOWUP entry, runs the regression test and the review guard, and reads
the saved step output. It prints `Verified ops-cadence price check`.
