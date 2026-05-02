# Release Discussion Skip Validation

Issue: `#392`

## What changed

- `.github/workflows/release-content.yml` now skips discussion creation when
  the Discussions categories endpoint is unavailable.
- `scripts/resolve_discussion_category.py` accepts only the expected GitHub
  category-list JSON shape and a non-empty `node_id`.
- `sdk/tests/test_release_discussion_category.py` covers valid category lookup,
  GitHub `404` error payloads, blank IDs, and CLI behavior.

## Commands run

```text
python -m pytest sdk\tests\test_release_discussion_category.py -v
5 passed

python scripts\sdk_preflight.py
All checks passed!

python scripts\sdk_release_guard.py
Release guard passed.

git diff --check
passed

python -m pytest sdk\tests --cov=agentguard --cov-report=term-missing --cov-fail-under=80
699 passed, coverage 92.88%

python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py scripts/resolve_discussion_category.py sdk/tests/test_release_discussion_category.py
All checks passed!

python -m pytest sdk\tests\test_architecture.py -v
9 passed

npm --prefix mcp-server test
5 passed

python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q
passed
```

## Manual probes

```text
'[{"name":"Announcements","node_id":"DIC_ok"}]' | python scripts\resolve_discussion_category.py
DIC_ok

'{"message":"Not Found","status":"404"}' | python scripts\resolve_discussion_category.py
skip path returned nonzero as expected
```

## Known validation note

`make` is not installed in this Windows shell, so the equivalent direct commands
were run instead.
