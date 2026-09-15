# Claims audit - session codex-agentguard-preflight-20260914

**Verdict: RED**  (13/14 verified)

- OK **Release 1.3.1 marker updated in AGENTS.md** (`file_contains`)
    - /1\.3\.1/ found in AGENTS.md
- OK **Release 1.3.1 marker updated in CLAUDE.md** (`file_contains`)
    - /1\.3\.1/ found in CLAUDE.md
- OK **Release 1.3.1 marker updated in .claude/agents/sdk-dev.md** (`file_contains`)
    - /1\.3\.1/ found in .claude/agents/sdk-dev.md
- OK **Release 1.3.1 marker updated in skills/agentguard/SKILL.md** (`file_contains`)
    - /1\.3\.1/ found in skills/agentguard/SKILL.md
- OK **Release 1.3.1 marker updated in sdk/pyproject.toml** (`file_contains`)
    - /1\.3\.1/ found in sdk/pyproject.toml
- OK **Release 1.3.1 marker updated in sdk/PYPI_README.md** (`file_contains`)
    - /1\.3\.1/ found in sdk/PYPI_README.md
- OK **Release 1.3.1 marker updated in CHANGELOG.md** (`file_contains`)
    - /1\.3\.1/ found in CHANGELOG.md
- OK **Release 1.3.1 marker updated in ops/03-ROADMAP_NOW_NEXT_LATER.md** (`file_contains`)
    - /1\.3\.1/ found in ops/03-ROADMAP_NOW_NEXT_LATER.md
- OK **README explains budget preflight usage** (`file_contains`)
    - /budget.check/ found in README.md
- OK **Architecture states concurrent reservation boundary** (`file_contains`)
    - /Concurrent requests/ found in ops/02-ARCHITECTURE.md
- OK **Regression verifies real response charged once before retries stop** (`file_contains`)
    - /test_first_call_is_counted_once_then_retries_are_blocked/ found in sdk/tests/test_budget_preflight.py
- OK **All provider patches have preflight guard support** (`file_contains`)
    - /_check_budget_before_request/ found in sdk/agentguard/instrument.py
- OK **Audit and reproducible installed demo evidence retained** (`file_exists`)
    - proof/v1.3.1/README.md exists
- XX **undeclared change: traces.jsonl** (`undeclared_change`, RED)
    - traces.jsonl changed since session.start; no active claim named that path

## 1 gap(s) - a claimed 'done' is not real

- [RED/fail] undeclared change: traces.jsonl - traces.jsonl changed since session.start; no active claim named that path
