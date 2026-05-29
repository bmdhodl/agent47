# Releasing

AgentGuard SDK publishing is tag-triggered. Push a `vX.Y.Z` tag after the
release-prep PR lands on `main`. Release announcements run only after the
package publishes and the GitHub Release exists.

| Workflow | What it does |
| --- | --- |
| [`publish.yml`](../.github/workflows/publish.yml) | Verifies the tag matches `sdk/pyproject.toml`, runs lint, Bandit, pytest, builds the wheel, publishes `agentguard47` to PyPI, then creates or verifies the GitHub Release in a separate post-publish job. |
| [`release-content.yml`](../.github/workflows/release-content.yml) | Runs from explicit `workflow_dispatch` after publish, or from a manual `release.published` event, and posts optional release announcements. It skips safely when Discussions or dashboard credentials are unavailable. |

## Cut A Release

1. Land all intended release PRs on `main`.
2. Bump `sdk/pyproject.toml`.
3. Move `CHANGELOG.md` entries from `Unreleased` into `X.Y.Z`.
4. Update release markers checked by `scripts/sdk_release_guard.py`.
5. Regenerate the package README:

   ```bash
   python scripts/generate_pypi_readme.py --write
   ```

6. Run the local gates:

   ```bash
   make release-guard
   make check
   make structural
   make security
   ```

7. Merge the release-prep PR.
8. Tag the merge commit:

   ```bash
   git checkout main
   git pull --ff-only
   VERSION=$(python -c "import tomllib; print(tomllib.load(open('sdk/pyproject.toml','rb'))['project']['version'])")
   git tag "v$VERSION"
   git push origin "v$VERSION"
   ```

9. Watch the tag workflow. The GitHub Release job starts only after PyPI
   publish succeeds. If the post-publish GitHub Release or announcement step
   fails, rerun that failed job instead of republishing the package.

## Verification

After the workflows finish:

- Confirm `gh release view vX.Y.Z --repo bmdhodl/agent47` succeeds.
- Confirm `python -m pip index versions agentguard47` reports the new version.
- Install the published wheel in a clean venv and run `agentguard doctor`,
  `agentguard demo`, `agentguard quickstart --framework raw --write`, the
  generated file, and `agentguard report`.
- Confirm PyPI files show Trusted Publishing provenance and attestations.
- Confirm the `Release Content - Auto-generate announcements` workflow ran for
  the same tag, or skipped only optional destinations because Discussions or
  dashboard credentials were unavailable.

## Release Notes

GitHub release notes are public. Keep PR titles and generated categories clear:

- No customer, revenue, or private roadmap claims.
- No internal-only incident language.
- No security admissions beyond what is already public.
- Use labels from `.github/release.yml` before merging PRs.
