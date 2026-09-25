# AgentGuard 1.4.1 candidate

Owner-approved patch on 2026-09-25: add `agentguard --version`.

Linux, Python 3.11, built from this branch:

```text
$ pip wheel --no-deps ./sdk            -> agentguard47-1.4.1-py3-none-any.whl
$ agentguard --version                 (fresh venv, wheel only)
agentguard 1.4.1
exit=0
$ python -m agentguard --version
agentguard 1.4.1
exit=0
```

Published 1.4.0 for comparison: `agentguard --version` exits 2
(`unrecognized arguments: --version`).

Checks on this branch: 1196 passed, 1 skipped, 91.64% coverage; ruff,
structural (9), bandit, review readiness, release guard, docs link check, and
MCP (11/11) pass. `test_version_flag_*` fails with `cli.py` reverted and
passes with the fix.

After the tag, record the PyPI files, attestations, and the
`published-wheel.yml` run in `proof/v1.4.1/PUBLICATION.md`.
