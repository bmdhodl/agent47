# PyPI Trusted Publishing Validation

## Scope

Release-infrastructure and release-docs only.

Changed:

- `.github/workflows/publish.yml`
- `docs/release/trusted-publishing.md`
- `ops/04-DEFINITION_OF_DONE.md`
- `CHANGELOG.md`
- `README.md`
- generated `sdk/PYPI_README.md`
- `scripts/generate_pypi_readme.py`

No SDK runtime behavior, public Python API, package version, or dependency
metadata changed.

## External References Checked

- PyPI Trusted Publishing docs require `id-token: write`, no explicit username
  or password, and a matching publisher config for owner, repo, workflow, and
  environment.
- PyPI attestation docs state `pypa/gh-action-pypi-publish` can upload
  attestations when publishing with a trusted publisher.

## Commands

```text
python scripts\generate_pypi_readme.py --write

python scripts\generate_pypi_readme.py --check
passed

python scripts\sdk_release_guard.py
Release guard passed.

python -m pytest sdk\tests\test_pypi_readme_sync.py sdk\tests\test_sdk_release_guard.py -v
10 passed

python -m ruff check scripts/generate_pypi_readme.py scripts/sdk_release_guard.py
All checks passed.

python scripts\sdk_preflight.py
passed

git diff --check
passed

$env:SOURCE_DATE_EPOCH="315532800"; python -m build .\sdk
Successfully built agentguard47-1.2.10.tar.gz and agentguard47-1.2.10-py3-none-any.whl
```

## Workflow Contract Check

```text
publish.yml has:
- environment: pypi
- permissions.id-token: write
- permissions.attestations: write
- pypa/gh-action-pypi-publish with packages-dir: sdk/dist/
- attestations: true

publish.yml no longer has:
- password: ${{ secrets.PYPI_TOKEN }}
```

## Remaining External Prerequisite

The PyPI project owner must configure the trusted publisher for `agentguard47`
before the next release tag:

```text
Owner: bmdhodl
Repository name: agent47
Workflow filename: publish.yml
Environment name: pypi
```

After the next release publishes, verify PyPI file metadata shows Trusted
Publishing provenance and attestations. Then remove the old `PYPI_TOKEN`
repository secret.
