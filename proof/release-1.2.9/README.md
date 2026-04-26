# Release 1.2.9 Proof

Release candidate for SDK `v1.2.9`.

## Validation Captured

- `make-command.txt` - confirms `make` is unavailable in this PowerShell environment and direct equivalents were used.
- `pypi-readme-check.txt` - generated PyPI README is in sync.
- `release-guard.txt` - release metadata, changelog, markers, MCP metadata, and generated PyPI README are aligned.
- `ruff.txt` - lint passed for SDK and release scripts.
- `structural.txt` - architecture invariant tests passed.
- `security.txt` - bandit passed with no findings.
- `gitleaks.txt` - gitleaks scanned 339 commits and found no leaks.
- `mcp-test.txt` - MCP TypeScript build and node tests passed.
- `pytest-full.txt` - full SDK pytest suite passed with coverage above the 80% floor.
- `preflight.txt` - changed-file preflight passed.
- `build.txt` - local sdist and wheel build succeeded for `agentguard47-1.2.9`.
