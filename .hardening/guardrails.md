# Hardening Guardrails

## ag47-ci-tools-py39-pins

- Failure class: `ci-tools-python-floor-drift`
- Rule: direct pins in `.github/requirements/ci-tools.in` must support the SDK CI floor, currently Python 3.9.
- Enforcement: `scripts/ci_tools_requirements_guard.py`
- Wiring: `make ci-tools-guard`, `make check`, and the CI `lint` job.
- Regression test: `sdk/tests/test_ci_tools_requirements_guard.py`
