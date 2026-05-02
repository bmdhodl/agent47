# v1.2.10 Release Validation

## Scope

Release prep for `agentguard47` `v1.2.10`.

Changed:

- `sdk/pyproject.toml` version bumped to `1.2.10`
- `CHANGELOG.md` release notes added
- release markers updated in agent-facing docs
- `sdk/PYPI_README.md` regenerated
- `.github/workflows/publish.yml` build timestamp seed moved to the ZIP-safe reproducible epoch

No SDK runtime behavior, public API, or dependency changes were made.

## Commands

```text
python scripts\generate_pypi_readme.py --write
python scripts\sdk_release_guard.py
Release guard passed.

python scripts\generate_pypi_readme.py --check
passed

git diff --check
passed

make check
not run: make is not installed in this Windows shell

python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py
All checks passed.

python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q
passed

python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80
701 passed, coverage 92.97%

$env:SOURCE_DATE_EPOCH="0"; python -m build .\sdk
failed locally: Python ZIP tooling rejects timestamps before 1980

$env:SOURCE_DATE_EPOCH="315532800"; python -m build .\sdk
Successfully built agentguard47-1.2.10.tar.gz and agentguard47-1.2.10-py3-none-any.whl
```

## Release Notes

This is a patch release focused on activation and release hygiene:

- faster first-run proof path in README/PyPI docs
- coding-agent review-loop proof artifact
- sample incident and PyPI README drift tests
- opt-in activation metrics design doc
- release discussion fallback hardening
- ZIP-safe reproducible build timestamp

