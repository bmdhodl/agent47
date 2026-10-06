# AgentGuard 2.0.0 publication receipt

Published 2026-10-06 UTC. The `v2.0.0` tag points at `e4114e0`, the squash
merge of #849. Read back on 2026-10-06 from this repository's tools; nothing
here was republished.

- Release: https://github.com/bmdhodl/agent47/releases/tag/v2.0.0 (published
  2026-10-06T15:07:04Z, not a draft or a prerelease)
- PyPI: https://pypi.org/project/agentguard47/2.0.0/ (`info.version` is
  2.0.0, `requires_python` is `>=3.11`, no file is yanked)
- Publish workflow: run 37484497553
  (https://github.com/bmdhodl/agent47/actions/runs/37484497553). The `publish`
  job, which runs the price-table age gate before the build, and the
  `github-release` job both concluded `success`.

## Package files

| File | SHA-256 | Bytes | Uploaded |
|---|---|---|---|
| `agentguard47-2.0.0-py3-none-any.whl` | `7e4fb4b258399a9cdbe77f4b351ed715342442079a7a5855f7aed243590f2d3b` | 153,026 | 2026-10-06T15:06:52Z |
| `agentguard47-2.0.0.tar.gz` | `0686fee9646bb75d9900c4cb3ac2f3b6456575ec9d12a60dbba0c8ad2c3a66dc` | 311,765 | 2026-10-06T15:06:54Z |

PyPI's integrity API returns a publish attestation for both files
(`https://docs.pypi.org/attestations/publish/v1`). The publisher is GitHub,
`bmdhodl/agent47`, workflow `publish.yml`.

The PyPI wheel hash is not the local release-prep hash in `README.md`
(`a434b301...`). Both wheels have the same 57 members. 52 differ only in line
endings, because the local Windows checkout uses CRLF. `RECORD` differs
because it lists those file hashes. The other 4 are identical.

## Clean install

A new Python 3.11.9 venv downloaded the wheel from `https://pypi.org/simple`.
Its SHA-256 matched the table. It installed with `--no-deps --no-index`. In an
empty directory these commands exited 0: `agentguard --version` (prints
`agentguard 2.0.0`), `doctor`, `demo`, `quickstart --framework raw --write`,
the generated starter, and `report .agentguard/traces.jsonl`. The demo stopped
a budget ($1.08 over $1.00), a loop (`search` three times) and a retry storm
(`fetch_docs`, limit 2).

On Python 3.10.11, `pip install agentguard47` from PyPI installs 1.4.0.
`pip install agentguard47==2.0.0` fails with `Ignored the following versions
that require a different python version: 2.0.0 Requires-Python >=3.11`.

## Published wheel on each OS

`published-wheel.yml` run 37484673368
(https://github.com/bmdhodl/agent47/actions/runs/37484673368) ran
`verify_release_example.py --tag v2.0.0 --wheel-only`. It installed the exact
PyPI wheel and ran the offline demo. The budget, loop and retry stop events
appeared and `report` completed. Each job concluded `success`:

- windows-latest, Python 3.12
- macos-latest, Python 3.12
- ubuntu-latest, Python 3.12
- ubuntu-latest, Python 3.11

## Release content and email

`release-content.yml` run 37484669205
(https://github.com/bmdhodl/agent47/actions/runs/37484669205) concluded
`success`.

- `announce`: skipped the Discussion ("categories unavailable or Discussions
  disabled").
- `email`: installed the exact PyPI wheel, saw all three stop events, then
  sent the release email. In bmdpat, every send for the
  `agentguard-release:v2.0.0` campaign has a `delivered` record and no error.
  Subscriber counts stay in bmdpat.

## Release page

On 2026-10-06, with Patrick's approval, an overview went above the generated
notes. It passed the release-notes slop scan (score 0.0, no em dash). It has
no image and no attached files, because unsigned release assets keep
Scorecard Signed-Releases at 0 (see `ops/FOLLOWUP.md`). Its video link opens
the X post. Its CHANGELOG, migration guide and hook guide links returned 200
at the `v2.0.0` tag. The edit left the release published, not a draft and
marked latest; `release-content.yml` runs only on `published`, so it did not
run again.

## Not done here

- OpenAI and Google price rows were checked on 2026-07-15. The `publish.yml`
  age gate fails from 2026-10-14, so recheck those rows before the next tag.
  See `ops/FOLLOWUP.md`.
