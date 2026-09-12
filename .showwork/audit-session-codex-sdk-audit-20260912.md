# Claims audit - session codex-sdk-audit-20260912

**Verdict: RED**  (1/11 verified)

- OK **Budget audit rejects corrupt stored counters before mutation** (`file_contains`)
    - /stored budget/ found in sdk/agentguard/_budget_validation.py
- XX **undeclared change: .github/workflows/codeql.yml** (`undeclared_change`, RED)
    - .github/workflows/codeql.yml changed since session.start; no active claim named that path
- XX **undeclared change: .github/workflows/scorecard.yml** (`undeclared_change`, RED)
    - .github/workflows/scorecard.yml changed since session.start; no active claim named that path
- XX **undeclared change: ARCHITECTURE.md** (`undeclared_change`, RED)
    - ARCHITECTURE.md changed since session.start; no active claim named that path
- XX **undeclared change: README.md** (`undeclared_change`, RED)
    - README.md changed since session.start; no active claim named that path
- XX **undeclared change: inbox/log.md** (`undeclared_change`, RED)
    - inbox/log.md changed since session.start; no active claim named that path
- XX **undeclared change: memory/state.md** (`undeclared_change`, RED)
    - memory/state.md changed since session.start; no active claim named that path
- XX **undeclared change: ops/02-ARCHITECTURE.md** (`undeclared_change`, RED)
    - ops/02-ARCHITECTURE.md changed since session.start; no active claim named that path
- XX **undeclared change: proof/audit-20260912/pytest-full.txt** (`undeclared_change`, RED)
    - proof/audit-20260912/pytest-full.txt changed since session.start; no active claim named that path
- XX **undeclared change: sdk/PYPI_README.md** (`undeclared_change`, RED)
    - sdk/PYPI_README.md changed since session.start; no active claim named that path
- XX **undeclared change: traces.jsonl** (`undeclared_change`, RED)
    - traces.jsonl changed since session.start; no active claim named that path

## 10 gap(s) - a claimed 'done' is not real

- [RED/fail] undeclared change: .github/workflows/codeql.yml - .github/workflows/codeql.yml changed since session.start; no active claim named that path
- [RED/fail] undeclared change: .github/workflows/scorecard.yml - .github/workflows/scorecard.yml changed since session.start; no active claim named that path
- [RED/fail] undeclared change: ARCHITECTURE.md - ARCHITECTURE.md changed since session.start; no active claim named that path
- [RED/fail] undeclared change: README.md - README.md changed since session.start; no active claim named that path
- [RED/fail] undeclared change: inbox/log.md - inbox/log.md changed since session.start; no active claim named that path
- [RED/fail] undeclared change: memory/state.md - memory/state.md changed since session.start; no active claim named that path
- [RED/fail] undeclared change: ops/02-ARCHITECTURE.md - ops/02-ARCHITECTURE.md changed since session.start; no active claim named that path
- [RED/fail] undeclared change: proof/audit-20260912/pytest-full.txt - proof/audit-20260912/pytest-full.txt changed since session.start; no active claim named that path
- [RED/fail] undeclared change: sdk/PYPI_README.md - sdk/PYPI_README.md changed since session.start; no active claim named that path
- [RED/fail] undeclared change: traces.jsonl - traces.jsonl changed since session.start; no active claim named that path
