# v2.0.0 release prep proof (2026-10-05)

Patrick authorized the 2.0.0 release on 2026-10-05, to go live on
2026-10-06. The source was already 2.0.0. This change moves the public text
from "candidate" to release wording:

- `CHANGELOG.md`: the 2.0.0 section no longer says "Unreleased candidate".
- `README.md` and the generated `sdk/PYPI_README.md`: the Python 3.11 note,
  and the `receipt`, `hook` and `run` sections say "new in 2.0.0".
- Docs: getting started, Python 3.11 migration, try-release (now pins
  `agentguard47==2.0.0` and Python 3.11+), free local clients, OpenAI
  Responses (installs `agentguard47==2.0.0`, not a local wheel),
  enforcement boundary, compatibility, Vercel comparison, three discussion
  drafts and the docs index.
- Site: the index labels, the receipt note, the hosted-tools rule, the
  enforcement table row and two blog lines.
- `examples/openai_agents_sdk_budget.py` docstring.
- `memory/state.md`, `memory/decisions.md` and the roadmap row record the
  approval and the timing.

Dated receipts for the unpublished 1.4.1 candidate in `docs/compatibility.md`
keep their wording. The `install-intent-candidate` metric name on the site
does not change, because activation tests and reports use it.

Merge this PR on 2026-10-06, just before the `v2.0.0` tag. If it merges
earlier, GitHub and the site say "new in 2.0.0" while PyPI still serves 1.4.0.

## Checks

Platform: Windows 11, Python 3.13.2 (suite), Python 3.11 (clean venv),
Git Bash 5.2.37. `make` is not installed, so each command ran directly.

| File | Command | Result |
|---|---|---|
| `00-before-browser.txt` | `browser_check.py` on the `origin/main` site | 0 of 12 pass; every page shows "2.0.0 candidate" |
| `01-preflight.txt` | `python scripts/sdk_preflight.py` | exit 0 |
| `02-review-readiness.txt` | `python scripts/review_readiness_guard.py` | exit 0 |
| `03-ci-tools-guard.txt` | `python scripts/ci_tools_requirements_guard.py` | exit 0 |
| `04-release-guard.txt` | `python scripts/sdk_release_guard.py --check-price-table-age` | passed |
| `05-lint.txt` | `ruff check` (the `publish.yml` set plus the changed example) | exit 0 |
| `06-security.txt` | `bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q` (the `publish.yml` gate) | exit 0 |
| `07-structural.txt` | `pytest sdk/tests/test_architecture.py` | 9 passed |
| `08-docs-tests.txt` | PyPI README sync, release guard, release example, activation, first-run tests | 94 passed |
| `09-test.txt` | `pytest sdk/tests/ --cov=agentguard --cov-fail-under=80` | 1592 passed, 3 skipped; coverage 93% |
| `10-clean-install.txt` | `bash proof/v2.0.0/clean_install.sh <work>` | see below |
| `11-browser.txt` | `python proof/v2.0.0/browser_check.py` | 12 of 12 pass |

The price-table age check passes today. OpenAI and Google rows were checked
on 2026-07-15, so the `publish.yml` gate fails from 2026-10-14 (more than 90
days). Tag before then, or re-check those prices first. `publish.yml` runs
the check before it builds, so a late tag stops before any PyPI upload. On
tag day, run `python scripts/sdk_release_guard.py --check-price-table-age`
before you push the tag.

`09-test.txt` ends with the `PermissionError` from pytest's `atexit` temp-dir
cleanup, after the summary. Python ignores it, and pytest exited 0.

### Clean install

`clean_install.sh` builds the package like `publish.yml`
(`SOURCE_DATE_EPOCH=315532800 python -m build ./sdk`). Local hashes:

| File | SHA-256 |
|---|---|
| `agentguard47-2.0.0-py3-none-any.whl` | `a434b30181ec3a48eda1253f7e53a286271aded8b80cc83c871139189f5cc341` |
| `agentguard47-2.0.0.tar.gz` | `23706a7f104da57e7dbe103c4867b74fbc45ad9c2011cf712f5c9a8711303d3b` |

The CI build makes the files that go to PyPI. Compare its hashes in
`PUBLICATION.md` after the release; this local build is not the upload.

A new Python 3.11 venv installed the wheel with `--no-deps --no-index`. In an
empty directory these commands exited 0: `--version` (prints
`agentguard 2.0.0`), `doctor`, `demo`, `report`, `receipt`,
`quickstart --framework raw --write`, the raw starter, the starter `report`,
`hook claude-code --help` and `run --help`. The demo stopped a budget
($1.08 over $1.00), a loop (`search` three times) and a retry storm
(`fetch_docs`, limit 2). A Python 3.10 venv refused the wheel:
`requires a different Python: 3.10.11 not in '>=3.11'`.

### Pages

`browser_check.py` opens `index.html`, `enforcement.html` and the two
changed blog posts in Chromium at 375, 768 and 1440 px. Each page must show
its new label as rendered, must not show "2.0.0 candidate" or "unpublished
2.0.0" in any case, and must have no horizontal overflow.
`browser-index-375.png` and `browser-index-1440.png` show the index labels.

## Not done here

- Tag `v2.0.0`, PyPI upload, GitHub Release, attestations and the published
  wheel run. They follow the merge on 2026-10-06 and go in `PUBLICATION.md`.
- `actionlint` and `shellcheck` are not installed on this host. No workflow
  changed.

## Re-check

`python proof/v2.0.0/verify.py` checks the changelog, searches the public
docs, site and examples for candidate wording, reruns the release guard and
the PyPI README sync test, and reads the saved install, browser and suite
results. It prints `Verified v2.0.0 release prep`.
