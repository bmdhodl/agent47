# Releasing

AgentGuard SDK releases are tag-triggered. Push a `vX.Y.Z` tag and three workflows fire in parallel:

| Workflow | What it does |
| --- | --- |
| [release.yml](../.github/workflows/release.yml) | Validates tag matches `sdk/pyproject.toml`, creates the GitHub Release with categorized notes. |
| [publish.yml](../.github/workflows/publish.yml) | Runs lint/bandit/pytest, builds the wheel, publishes to PyPI as `agentguard47`. |
| [release-content.yml](../.github/workflows/release-content.yml) | Posts a GitHub Discussion announcement and triggers X / LinkedIn posts via the dashboard repo. |

The three workflows are independent: PyPI publish, Discussion announcement, and social posts all reference `https://github.com/bmdhodl/agent47/releases/tag/$TAG`, which works as soon as the GitHub Release exists.

## Cut a release

1. Land all PRs intended for the release on `main`.
2. Bump `version` in [sdk/pyproject.toml](../sdk/pyproject.toml). Follow [semver](https://semver.org):
   - **patch** (`1.2.10` → `1.2.11`) — bug fixes, internal refactors, security patches.
   - **minor** (`1.2.10` → `1.3.0`) — new user-visible behavior, non-breaking SDK additions.
   - **major** (`1.2.10` → `2.0.0`) — breaking API changes.
3. Update [CHANGELOG.md](../CHANGELOG.md) with the human-curated entry. Refresh any release markers `scripts/sdk_release_guard.py` checks (`AGENTS.md`, `CLAUDE.md`, etc.).
4. Open a PR titled `Release v<NEW_VERSION>` containing the version bump, the CHANGELOG entry, and any marker updates. Merge it.
5. Tag the merge commit and push:
   ```bash
   git checkout main && git pull
   VERSION=$(python -c "import tomllib; print(tomllib.load(open('sdk/pyproject.toml','rb'))['project']['version'])")
   git tag "v$VERSION"
   git push origin "v$VERSION"
   ```
6. Watch the three workflows. If `release.yml` fails the tag-version check, `sdk/pyproject.toml` and the tag disagree — fix the bump (or push the missing version commit) and re-tag.

## Pre-releases

Use `vX.Y.Z-rc.N` (or any `vX.Y.Z-*` suffix). `release.yml` marks them as pre-releases automatically. PyPI publish runs the same gates; the package version still has to match.

## Categorization

GitHub's `--generate-notes` groups PRs into the categories defined in [.github/release.yml](../.github/release.yml):

- 🔒 Security — label `security`
- ✨ Features — label `feature` or `enhancement`
- 🐛 Fixes — label `bug` or `fix`
- 🏗️ Reliability & Infra — label `infra`, `reliability`, or `performance`
- 📝 Docs — label `documentation` or `docs`
- 🧹 Other changes — anything else

Add the matching label to a PR before merge to get it sorted correctly. `skip-changelog` and `dependencies` labels omit a PR from the notes entirely.

## Release-note copy hygiene

The GitHub Release page is public. Release notes are read by prospects, search engines, and red-teamers. Same rules as the rest of the public surface:

- **No customer-status leaks.** Don't reference customer count, "first client", or revenue stage.
- **No security admissions.** Describe capabilities ("Hardened request validation"), not gaps ("Fixed SSRF in X"). Specific security-fix detail belongs in [SECURITY.md](../SECURITY.md), a private advisory, or [CHANGELOG.md](../CHANGELOG.md) — not the marketing surface.
- **No internal jargon.** Rewrite "release-surface cleanup" as "improved release tooling"; nobody outside the team knows what a release-surface is.

If `--generate-notes` produces a PR title that violates these, edit the PR title before merging or override the generated notes when cutting that specific release.

## What goes in CHANGELOG.md vs the GitHub Release

| Surface | Audience | Detail level |
| --- | --- | --- |
| GitHub Release notes | Public, search engines, integrators | Categorized capability statements. |
| CHANGELOG.md | Developers integrating against the SDK | More detail than the release notes; still follows the copy hygiene rules. |
| Internal notes / Linear | Patrick + AI agents | Full detail. Specific security fixes by name. Why-we-bumped context. |
