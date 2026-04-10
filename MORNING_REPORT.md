# Morning Report

## Mission
Create a root architecture guide that explains the public SDK repo clearly enough for future nightshift work and PR review.

## What shipped
- added `ARCHITECTURE.md` at the repo root
- documented the public repo boundary versus the private dashboard
- mapped the main data flow from runtime guards to local proof surfaces, hosted ingest, and MCP clients
- documented key abstractions, feature-placement rules, and known technical debt

## Why it matters
- the repo is easy to drift in because SDK, MCP, site, and private-dashboard references all exist nearby
- a single current architecture doc reduces repeated recon work and lowers the chance of scope mistakes
- future PRs now have a concrete place to update when the repo shape changes

## Validation
- `python scripts/sdk_preflight.py` passed with docs-only output
- local proof files saved under `proof/architecture-doc/`

## Notes
- this is a docs-only PR
- `ops/02-ARCHITECTURE.md` still exists, so architectural guidance is intentionally duplicated until one source is retired
