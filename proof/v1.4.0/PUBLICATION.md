# AgentGuard 1.4.0 publication receipt

Published 2026-09-24 UTC. Read back on 2026-09-25 from this repository's
tools; nothing here was republished.

- Release: https://github.com/bmdhodl/agent47/releases/tag/v1.4.0 (published
  2026-09-24T21:30:35Z, not a prerelease)
- PyPI: https://pypi.org/project/agentguard47/1.4.0/ (`info.version` is 1.4.0)
- Release content / email workflow: runs 36061930651 (attempt 3), 36081292600,
  and 36094636237 on `main` all concluded `success`.

## Package files

| File | SHA-256 | Uploaded |
|---|---|---|
| `agentguard47-1.4.0-py3-none-any.whl` | `ca8efaacff03cc373a30610c7fa7d9797a87fe140f56ece344e782df8b0435fa` | 2026-09-24T21:30:21Z |
| `agentguard47-1.4.0.tar.gz` | `a80873bd1f4c06e7c1c3a58d91106e5cb80e62fa814985fddd7ba3c054102781` | 2026-09-24T21:30:23Z |

PyPI's integrity API returns a publish attestation for both files
(`https://docs.pypi.org/attestations/publish/v1`). The publisher is GitHub,
`bmdhodl/agent47`, workflow `publish.yml`.

## Clean install

A fresh Python 3.11 venv installed `agentguard47==1.4.0 --no-deps` from PyPI.
`pip show` reports `Requires:` empty and a site-packages location. In an
empty directory, `agentguard doctor`, `agentguard demo`,
`agentguard quickstart --framework raw`, and `agentguard report --help` all
exited 0. `agentguard --version` exits 2 because the flag does not exist; see
`ops/FOLLOWUP.md`.

## Published wheel on each OS

`published-wheel.yml` run 36190628659
(https://github.com/bmdhodl/agent47/actions/runs/36190628659) ran
`verify_release_example.py --tag v1.4.0 --wheel-only`. It installed the exact
PyPI wheel and ran the offline demo with sockets refused. All three stop
events appeared and `report` completed on:

- windows-latest, Python 3.12
- macos-latest, Python 3.12
- ubuntu-latest, Python 3.12
- ubuntu-latest, Python 3.9

## Not verified here

- Subscriber email delivery receipts. The workflow succeeded, but this
  environment cannot read the provider's delivered/bounced counts.
- The `agentguard-1.4.0.png` release asset is unsigned. See the Scorecard note
  in `ops/FOLLOWUP.md`.
