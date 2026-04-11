# PR Draft

## Title
Add a budget-aware escalation guard for advisor-style model routing

## Summary
- add `BudgetAwareEscalation`, `EscalationSignal`, and `EscalationRequired` so apps can keep a cheaper default model and escalate only hard turns to a stronger model
- support four v1 signals: token count, confidence, tool-call depth, and a custom rule
- keep the SDK boundary intact: AgentGuard decides when to escalate; the app still owns the actual provider call

## Scope
- core guard implementation in `sdk/agentguard/escalation.py`
- public exports and guard-module compatibility re-exports
- tests for signal matching, next-call arming, exports, DX, smoke, and example execution
- one guide and one local-only example
- README / examples / changelog / roadmap / generated PyPI README sync
- proof artifacts under `proof/budget-aware-escalation/`

## Non-goals
- no dashboard work
- no provider-specific routing adapter
- no hidden network behavior
- no new runtime dependencies
- no attempt to auto-switch OpenAI or Anthropic patchers under the hood

## Proof
- `python -m ruff check sdk/agentguard/guards.py sdk/agentguard/escalation.py sdk/agentguard/__init__.py sdk/tests/test_guards.py sdk/tests/test_exports.py sdk/tests/test_dx.py sdk/tests/test_smoke.py sdk/tests/test_example_starters.py sdk/tests/test_architecture.py examples/budget_aware_escalation.py scripts/generate_pypi_readme.py`
- `python -m pytest sdk/tests -v --cov=agentguard --cov-report=term-missing --cov-fail-under=80`
- `python scripts/sdk_release_guard.py`
- `python scripts/sdk_preflight.py`
- `python -m bandit -r sdk/agentguard -s B101,B110,B112,B311 -q`
- `python scripts/generate_pypi_readme.py --write`
- `PYTHONPATH=sdk python examples/budget_aware_escalation.py`

## Saved artifacts
- `proof/budget-aware-escalation/example-output.txt`
- `proof/budget-aware-escalation/budget_aware_escalation_traces.jsonl`
- `proof/budget-aware-escalation/source-notes.md`
- `proof/budget-aware-escalation/blog-draft.md`
