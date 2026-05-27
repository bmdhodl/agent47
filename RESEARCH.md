# RESEARCH

## API surface assumption verified

The task body said `guard.goal(name, verifier=...)`. The intel concept page (`Knowledge/concepts/cost-per-completed-goal.md`) sketches `from agentguard47 import AgentGuard; guard = AgentGuard(...)`. The actual package exposes `BudgetGuard` (no class named `AgentGuard`). Source: `sdk/agentguard/__init__.py:18-37` lists every public guard class — `AgentGuard` is not there; only `AgentGuardError`.

Decision: add `goal()` as a method on `BudgetGuard`. The "guard" in the concept page sketch is the budget guard — that is where cost state lives, so it is the natural integration point. Adding a `goal()` method is additive (zero breaking change per the task scope rule).

## Cost accumulation hook

`BudgetGuard.consume(...)` is the single place every dollar gets recorded (`sdk/agentguard/guards.py:244-291`). Hooking goal-attribution there means any caller that uses the standard cost path — including auto-patched OpenAI / Anthropic clients, manual `consume` calls, and integration callbacks — gets goal attribution for free, with no other code changes.

The hook calls `agentguard.goal._record_consume(...)` which reads the innermost active goal via a `ContextVar` and appends a `Call`. No-op when no goal is open.

## ContextVar for nesting + async

`contextvars.ContextVar` is the standard library tool the paper (and Python docs) recommend for per-task state that needs to propagate through `asyncio` and `concurrent.futures` worker callsites. No new dependency required. The active-goal stack is a tuple so nested `with` blocks are unambiguous; pop on exit uses `ContextVar.reset(token)`.

## Failure-cost rule

From the concept page: "failure_cost = portion of cost spent on attempts that failed." Implementation:

- If `succeeded is True` and `attempts >= 1`: every call with `attempt_idx < attempts` is failure cost (the final attempt is the winning one).
- If `succeeded is False`: every direct call is failure cost.
- Sub-goal failure cost rolls up.

This requires the caller to call `g.attempt()` at the top of each retry so we can stamp each call's `attempt_idx`. The task body explicitly says v1 keeps `attempt()` explicit (no auto-detection).

## Verifier exception semantics

If the `with` block exits via exception, we do NOT call the verifier — succeeded is forced to False. Rationale: the verifier is a success oracle, not an exception handler. Calling it on an in-flight exception risks masking the real error. Verifier exceptions on clean exit propagate (fail loudly per global instructions).

## Files inspected before writing code

- `sdk/agentguard/__init__.py` — public surface
- `sdk/agentguard/guards.py` — BudgetGuard, BaseGuard
- `sdk/agentguard/setup.py` — module-level init pattern (not used for this feature)
- `sdk/tests/test_cost.py`, `tests/test_concurrency.py` — confirmed no test currently asserts that `consume` does NOT call into any other module (so the hook is safe)
- `Knowledge/concepts/cost-per-completed-goal.md` — design rationale
- `Queue/agent47/Complete/energy-per-successful-goal-metric.md` — parent task context

## What did NOT make the cut (v1)

- LLM-as-judge verifiers (explicitly deferred per task scope).
- Persistence / sink wiring (operators serialize and ship).
- Dashboard wiring (separate follow-up in agent47-dashboard).
- Module-level `init()` integration. The setup-pattern path could later expose `agentguard.goal(...)` as a convenience that grabs the configured BudgetGuard, but that is additive on top of the v1 method API.
