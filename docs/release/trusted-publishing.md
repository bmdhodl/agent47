# PyPI Trusted Publishing

AgentGuard publishes `agentguard47` to PyPI from
`.github/workflows/publish.yml` when a `v*` tag is pushed.

The release job uses PyPI Trusted Publishing instead of a long-lived
`PYPI_TOKEN`. GitHub mints a short-lived OIDC token for the `pypi` environment,
and PyPI exchanges that identity for a temporary upload credential.

## PyPI Project Configuration

The PyPI project owner must configure this trusted publisher for
`agentguard47`:

```text
Owner: bmdhodl
Repository name: agent47
Workflow filename: publish.yml
Environment name: pypi
```

PyPI asks for the workflow filename, not the full path. The matching workflow
path in this repo is `.github/workflows/publish.yml`.

## GitHub Workflow Requirements

The publish job must keep:

```yaml
environment: pypi
permissions:
  contents: read
  id-token: write
  attestations: write
```

The `pypa/gh-action-pypi-publish` step must not include `username`,
`password`, or `api-token` inputs. Tokenless publishing is what causes the
action to use Trusted Publishing.

Current publish step:

```yaml
- name: Publish to PyPI
  uses: pypa/gh-action-pypi-publish@cef221092ed1bacb1cc03d23a2d87d1d172e277b
  with:
    packages-dir: sdk/dist/
    attestations: true
```

## Release Verification

After the next release tag publishes:

1. Open the GitHub Actions run for `.github/workflows/publish.yml`.
2. Confirm the publish step did not warn that Trusted Publishing is disabled.
3. Open the new version on PyPI.
4. Confirm each release file shows Trusted Publishing provenance and
   attestations in PyPI file metadata.
5. Remove the old `PYPI_TOKEN` repository secret after a successful trusted
   publishing release.

## Rollback

If publishing fails because the PyPI trusted publisher is not configured yet,
configure the PyPI publisher tuple above and rerun the failed release workflow.
Do not restore `PYPI_TOKEN` unless a release is blocked and the owner explicitly
chooses a temporary token-based rollback.

## References

- [PyPI: Publishing with a Trusted Publisher](https://docs.pypi.org/trusted-publishers/using-a-publisher/)
- [PyPI: Adding a Trusted Publisher to an Existing Project](https://docs.pypi.org/trusted-publishers/adding-a-publisher/)
- [PyPI: Producing Attestations](https://docs.pypi.org/attestations/producing-attestations/)
- [pypa/gh-action-pypi-publish Trusted Publishing](https://github.com/pypa/gh-action-pypi-publish)
