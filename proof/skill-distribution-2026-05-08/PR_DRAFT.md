## Summary

- Move the AgentGuard skill into the spec-native `skills/agentguard/SKILL.md` path so `gh skill publish --dry-run` validates it.
- Update skill metadata from `1.2.7` to the verified shipped package version `1.2.10`.
- Add README/PyPI README install docs for both `pip install agentguard47` and skills-based installs.
- Update `llms.txt` to link to the new canonical skill path.
- Open curated-list PR: https://github.com/heilcheng/awesome-agent-skills/pull/225

## Related Issues

N/A

## Proof

- `git tag --sort=-v:refname | Select-Object -First 3` -> `v1.2.10`, `v1.2.9`, `v1.2.8`
- `gh repo view bmdhodl/agent47 --json visibility` -> `PUBLIC`
- `python -m pip index versions agentguard47` -> latest and installed `1.2.10`
- `gh skill publish --dry-run` -> passed
- `rg -n "blob/main/SKILL\.md|SKILL\.md" -S llms.txt README.md sdk/PYPI_README.md skills/agentguard/SKILL.md PR_DRAFT.md MORNING_REPORT.md` -> no stale root `blob/main/SKILL.md` link remains
- `npx skills add bmdhodl/agent47 && npx skills list` -> public repo resolves and installs `agentguard`
- `npx skills add K:\agent47 && npx skills list` -> local spec-native path resolves and installs `agentguard`
- clean venv: `pip install agentguard47`, quickstart import, and `agentguard doctor` -> passed
- `python -m ruff check sdk/agentguard/ scripts/generate_pypi_readme.py scripts/sdk_preflight.py scripts/sdk_release_guard.py` -> passed
- `python -m pytest sdk/tests/ -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80` -> `740 passed`, coverage `92.90%`
- `python -m pytest sdk/tests/test_architecture.py -v` -> `9 passed`
- `python -m bandit -r sdk/agentguard/ -s B101,B110,B112,B311 -q` -> passed
- `python scripts/sdk_release_guard.py` -> passed
- `npm --prefix mcp-server test` -> passed, `6` node tests

## Risk And Rollback

Risk is limited to skill discovery path changes and install-copy accuracy. Roll back by restoring the root `SKILL.md` location and removing the README skill-install section. No SDK runtime behavior changes.

## Scope

- **Related ops/doc(s):** NORTHSTAR, ROADMAP, DEFINITION_OF_DONE
- **Does this change the public API?** No
- **Does this shift roadmap priority?** No

## Checklist

- [x] `make check` equivalent passes (ruff + pytest + MCP tests; `make` unavailable on this Windows host)
- [x] `make structural` equivalent passes
- [x] `make security` equivalent passes
- [x] New functionality has tests
- [x] No new hard dependencies in core SDK
- [x] No hardcoded absolute paths
- [x] If `__init__.py` exports changed, `ops/02-ARCHITECTURE.md` updated
