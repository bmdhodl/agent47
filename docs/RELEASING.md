# Releasing

AgentGuard SDK releases are tag-triggered. Push a `vX.Y.Z` tag and two workflows fire:

| Workflow | What it does |
| --- | --- |
| [publish.yml](../.github/workflows/publish.yml) | Verifies the tag matches `sdk/pyproject.toml`, runs lint/bandit/pytest, builds the wheel, publishes to PyPI as `agentguard47`, then creates the GitHub Release with categorized notes. The GitHub Release is the **last** step, so it never gets created for a tag whose PyPI publish failed. |
| [release-content.yml](../.github/workflows/release-content.yml) | Posts a GitHub Discussion announcement and triggers X / LinkedIn posts via the dashboard repo. |

## Cut a release

1. Land all PRs intended for the release on `main` with the correct `type:*` label (see [Categorization](#categorization)).
2. Bump `version` in [sdk/pyproject.toml](../sdk/pyproject.toml). Follow [semver](https://semver.org):
   - **patch** (`1.2.10` → `1.2.11`) — bug fixes, internal refactors, security patches.
   - **minor** (`1.2.10` → `1.3.0`) — new user-visible behavior, non-breaking SDK additions.
   - **major** (`1.2.10` → `2.0.0`) — breaking API changes.
3. Update [CHANGELOG.md](../CHANGELOG.md) and refresh any release markers `scripts/sdk_release_guard.py` checks (`AGENTS.md`, `CLAUDE.md`, etc.). Run `make release-guard` locally to confirm.
4. Open a PR titled `Release v<NEW_VERSION>` containing the version bump, the CHANGELOG entry, and any marker updates. Merge it.
5. Tag the merge commit and push:
   ```bash
   git checkout main && git pull
   VERSION=$(python -c "import tomllib; print(tomllib.load(open('sdk/pyproject.toml','rb'))['project']['version'])")
   git tag "v$VERSION"
   git push origin "v$VERSION"
   ```
6. Watch `publish.yml`. If the tag-version check fails, `sdk/pyproject.toml` and the tag disagree — fix the bump (or push the missing version commit) and re-tag. If anything later fails (lint, tests, release guard, PyPI upload), the GitHub Release is **not** created, so you can fix the issue and re-tag without an inconsistent public release record.

## Pre-releases

Not currently supported. `scripts/sdk_release_guard.py` only accepts stable `X.Y.Z` version markers in `CLAUDE.md` / `AGENTS.md`, so a `vX.Y.Z-rc.N` tag would fail the metadata-sync gate before PyPI upload. If pre-releases become useful, extend the regex in `RELEASE_MARKERS` to accept optional `-suffix` and update this section.

## Categorization

GitHub's `--generate-notes` (called from the final step of `publish.yml`) groups PRs into the categories defined in [.github/release.yml](../.github/release.yml), using the repo's existing `type:*` label scheme:

| Category | PR label |
| --- | --- |
| 🔒 Security | `type:security` |
| ✨ Features | `type:feature`, `enhancement` |
| 🐛 Fixes | `type:bug`, `bug` |
| 🏗️ Performance & Refactors | `type:perf`, `type:refactor` |
| 🧪 CI & Tests | `type:ci`, `type:test` |
| 📝 Docs | `type:docs`, `documentation` |
| 🧹 Other changes | anything else |

Add the matching `type:*` label to a PR before merge to get it sorted correctly. `skip-changelog` and `dependencies` labels omit a PR from the notes entirely.

The label scheme matches the issue templates in [.github/ISSUE_TEMPLATE/](../.github/ISSUE_TEMPLATE/) — bug reports auto-apply `type:bug`, feature requests auto-apply `type:feature`, etc. PRs should match.

## Release-note copy hygiene

The GitHub Release page is public. Release notes are read by prospects, search engines, and red-teamers. Same rules as the rest of the public surface:

- **No customer-status leaks.** Don't reference customer count, "first client", or revenue stage.
- **No security admissions.** Describe capabilities ("Hardened request validation"), not gaps ("Fixed SSRF in X"). Specific security-fix detail belongs in [SECURITY.md](../SECURITY.md), a private advisory, or [CHANGELOG.md](../CHANGELOG.md) — not the marketing surface.
- **No internal jargon.** Rewrite "release-surface cleanup" as "improved release tooling"; nobody outside the team knows what a release-surface is.

If `--generate-notes` produces a PR title that violates these, edit the PR title before merging, or rewrite the release notes after the workflow creates the release.

## What goes in CHANGELOG.md vs the GitHub Release

| Surface | Audience | Detail level |
| --- | --- | --- |
| GitHub Release notes | Public, search engines, integrators | Categorized capability statements. |
| CHANGELOG.md | Developers integrating against the SDK | More detail than the release notes; still follows the copy hygiene rules. |
| Internal notes / Linear | Patrick + AI agents | Full detail. Specific security fixes by name. Why-we-bumped context. |
