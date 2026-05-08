# Morning Report - AgentGuard Skill Distribution

Date: 2026-05-08

## Outcome

AgentGuard skill distribution is ready for review. The stale skill version metadata was fixed, the skill now validates with GitHub's `gh skill publish --dry-run`, skills.sh discovery was verified, and the curated-list PR is open.

## What Changed

- Moved `SKILL.md` to `skills/agentguard/SKILL.md` because `gh skill publish --dry-run` requires skill names to match directory names. Root `SKILL.md` failed as directory `"."`.
- Updated skill metadata version from `1.2.7` to `1.2.10`.
- Added README and PyPI README install docs for:
  - `pip install agentguard47`
  - `npx skills add bmdhodl/agent47`
  - `gh skill install bmdhodl/agent47 agentguard`
- Updated `llms.txt` so its canonical skill link points to `skills/agentguard/SKILL.md`.
- Opened awesome-list PR: https://github.com/heilcheng/awesome-agent-skills/pull/225

## Verification

- Repo public: `gh repo view bmdhodl/agent47 --json visibility` -> `PUBLIC`
- Latest tag: `v1.2.10`
- PyPI package: `agentguard47` latest `1.2.10`
- `gh skill publish --dry-run` -> passed
- `llms.txt` stale root `SKILL.md` link check -> passed
- `npx skills add bmdhodl/agent47` in a clean temp folder -> installed `agentguard`
- `npx skills add <path-to-repo>` in a clean temp folder -> installed `agentguard` from `skills/agentguard/SKILL.md`
- Clean venv install + quickstart import + `agentguard doctor` -> passed
- Full repo validation:
  - ruff passed
  - pytest: `740 passed`, coverage `92.90%`
  - structural: `9 passed`
  - security: passed via `python -m bandit`
  - release guard passed
  - MCP server tests passed, `6` tests

## Notes

- No patch release was cut. The only package-facing correction was skill metadata to match the already shipped `v1.2.10` / PyPI `1.2.10` state.
- The local global `agentguard47` editable install originally pointed at another worktree, so validation reinstalled editable from this checkout before running repo tests.
- The awesome-list website build passed after `npm ci`; npm reported existing audit findings in that repo's dependency tree (`1 moderate`, `1 high`), unrelated to the README-only PR.
