# PR Draft

## Title
Position AgentGuard inside the emerging agent security stack

## Summary
- add a new competitive doc that places AgentGuard in the runtime behavior and budget layer, distinct from identity, MCP governance, and sandboxing
- update the README's competitive-doc links so the public repo points to both the gateway comparison and the broader stack framing
- regenerate the PyPI README so package docs stay aligned with the repo README

## Scope
- `docs/competitive/agent-security-stack.md`
- `README.md`
- `CHANGELOG.md`
- `sdk/PYPI_README.md`
- `PR_DRAFT.md`
- `MORNING_REPORT.md`
- proof artifacts under `proof/agent-security-stack-positioning/`

## Non-goals
- no dashboard work
- no SDK runtime or MCP code changes
- no attempt to turn AgentGuard into the identity, governance, or sandbox layer
- no speculative vendor feature claims beyond clearly labeled layer framing

## Proof
- `python scripts/sdk_preflight.py`
- `python -m pytest sdk/tests/test_pypi_readme_sync.py -v`
- `python scripts/sdk_release_guard.py`

## Saved artifacts
- `proof/agent-security-stack-positioning/preflight.txt`
- `proof/agent-security-stack-positioning/pypi-sync.txt`
- `proof/agent-security-stack-positioning/release-guard.txt`
- `proof/agent-security-stack-positioning/git-diff.txt`
