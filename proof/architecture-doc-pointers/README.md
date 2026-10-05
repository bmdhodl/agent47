# Architecture reminder targets proof (2026-10-05)

The root `ARCHITECTURE.md` owns module boundaries and data flow, and it says
so at `ARCHITECTURE.md:116`. `AGENTS.md` and `CLAUDE.md` check its age. The
weekly reminder in `ops-cadence.yml` still measured `ops/02-ARCHITECTURE.md`
and asked about "boundary changes" there. This change points the reminder at
the root file.

The PR template does not change. `ops/02-ARCHITECTURE.md` holds the table of
the 52 exports from `sdk/agentguard/__init__.py`, so API and export changes
still go there.

`ops-cadence.yml` has been disabled since 2026-06-11. This change takes
effect when it is turned on again. `ops/FOLLOWUP.md` records a separate price
check defect to fix before that.

## Checks

Platform: Windows 11, Python 3.13.2, Git Bash 5.2.37. `make` is not installed,
so each command ran directly. Outputs are next to this README.

| File | Command | Result |
|---|---|---|
| `01-workflow-step.txt` | run block of `ops-cadence.yml`, `gh` stubbed, Monday forced | exit 0; `arch_age=8` today; at +30 days the reminder names `ARCHITECTURE.md` |
| `02-preflight.txt` | `python scripts/sdk_preflight.py` | exit 0 (no SDK-relevant changes) |
| `03-review-readiness.txt` | `python scripts/review_readiness_guard.py` | exit 0 |
| `04-ci-tools-guard.txt` | `python scripts/ci_tools_requirements_guard.py` | exit 0 |
| `05-structural.txt` | `pytest sdk/tests/test_architecture.py` | 9 passed |
| `06-review-guard-tests.txt` | `pytest sdk/tests/test_review_readiness_guard.py` | 14 passed |
| `07-release-guard.txt` | `python scripts/sdk_release_guard.py` | Release guard passed |
| `08-verify.txt` | `python proof/architecture-doc-pointers/verify.py` | Verified architecture reminder targets |

`verify.py` failed on the unchanged tree ("ops-cadence.yml does not measure
the age of the root ARCHITECTURE.md") and passes after the change.

The first workflow-step run did not use the `gh` stub: a Windows path in
`PATH` hid it, and the real `gh` opened issues #844 and #845. Both are closed
as not planned with a note. The saved run uses a POSIX stub path, stops if
`gh` does not resolve to the stub, and sets an invalid `GH_TOKEN`.
