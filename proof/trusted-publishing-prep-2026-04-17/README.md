Trusted Publishing prep proof for issue #282.

Scope:
- prepare the GitHub workflow side for a future Trusted Publishing cutover
- prove the current release path is still token-based
- narrow the remaining blocker to the PyPI project settings for `agentguard47`

Artifacts:
- `publish-run-annotations.txt`: GitHub Actions annotations from the latest publish run showing:
  - a Trusted Publisher can still be created for this workflow
  - explicit `password` disables Trusted Publishing and attestations
- `github-environment-pypi.json`: the new GitHub environment created for the publish job
- `repo-secrets.txt`: current repo secrets still include `PYPI_TOKEN`
- `pypi-json-api.json`: current public project metadata snapshot for `agentguard47`

Current blocker:
- PyPI Trusted Publisher is not configured yet for:
  - owner: `bmdhodl`
  - repo: `agent47`
  - workflow: `.github/workflows/publish.yml`
  - environment: `pypi`

Safe repo-side change shipped in this branch:
- `publish.yml` now targets the `pypi` GitHub environment so the workflow tuple matches the planned PyPI publisher configuration.
- token auth remains in place until the PyPI-side publisher is added, to avoid breaking the next release.
