## Summary
- prepare the GitHub side for a future PyPI Trusted Publishing cutover
- keep the current token-based release path intact until PyPI project settings are updated
- capture proof showing why a full cutover is still externally blocked

## What changed
- add `environment: pypi` to the publish job in `.github/workflows/publish.yml`
- document the exact publisher tuple PyPI needs:
  - owner: `bmdhodl`
  - repo: `agent47`
  - workflow: `.github/workflows/publish.yml`
  - environment: `pypi`
- create the GitHub `pypi` environment
- add proof artifacts under `proof/trusted-publishing-prep-2026-04-17/`

## Why not remove `PYPI_TOKEN` yet?
Current public proof still shows the project is not using Trusted Publishing:
- the latest publish run emits `A new Trusted Publisher ... can be created`
- the same run emits `explicit password was also set, disabling Trusted Publishing`
- the current repo secret set still contains `PYPI_TOKEN`

Removing `password:` before PyPI is configured would break the next release.

## Validation
- `python scripts/sdk_release_guard.py`
- inspected current publish workflow + current publish run annotations
- created GitHub environment `pypi`

## Follow-up after merge
1. Add the Trusted Publisher on PyPI for `agentguard47`
2. Remove `password: ${{ secrets.PYPI_TOKEN }}`
3. Add `attestations: true`
4. Cut the next release and verify PyPI says `Uploaded using Trusted Publishing? Yes`

Related to #282