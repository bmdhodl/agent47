# PR Draft

## Title
Add repo-root architecture guide for SDK nightshift and PR work

## Summary
- add a new root `ARCHITECTURE.md` that explains the current public repo in one place
- make the repo boundary explicit: public SDK, MCP server, public site, and private dashboard split
- document the main data flow, core abstractions, technical debt, and feature-placement rules for future work

## Scope
- new `ARCHITECTURE.md` at the repo root
- no SDK runtime code changes
- no MCP behavior changes
- no dashboard or landing-page work

## Non-goals
- no feature work
- no architecture refactor
- no packaging or release changes
- no private dashboard documentation

## Proof
- `python scripts/sdk_preflight.py`
- manual inspection of `ARCHITECTURE.md`
- proof files:
  - `proof/architecture-doc/preflight.txt`
  - `proof/architecture-doc/status.txt`

## Why now
- the repo had architecture knowledge split across `ops/` notes and agent instructions
- queue guidance explicitly called for a real `ARCHITECTURE.md`
- future PRs need a stable repo-level reference to reduce boundary mistakes and duplicated rediscovery
