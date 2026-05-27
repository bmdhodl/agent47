# WORK_PLAN: goal-level metering API prototype

## Problem
AgentGuard today only meters per-session via `BudgetGuard`. Operators care about cost-per-completed-goal (per the arXiv:2605.22883 framing). Ship v1 of a `guard.goal(name, verifier=...)` context manager that buckets nested call costs against a named goal, runs a verifier on exit, and exposes a structured ledger.

## Approach
- New module `sdk/agentguard/goal.py`:
  - `Call` dataclass — single accounted call (tokens, calls, cost_usd, attempt_idx, ts).
  - `Goal` dataclass holding name, verifier, calls, sub-goals, attempts counter, start/end ts. Methods: `attempt()`, `_record(call)`, `to_dict()`. Properties: `cost_usd`, `failure_cost`, `duration_sec`, `succeeded` (set on exit).
  - `_active_goal_stack: ContextVar[tuple[Goal, ...]]` so nested calls inside async/threadpool see the right goal. The stack holds parent + descendants so we can implement nesting cleanly.
- `BudgetGuard.goal(name, verifier)` returns a context manager. On `__enter__` pushes a new Goal onto the contextvar stack and records start. On `__exit__` pops, runs verifier, sets succeeded, attaches goal to parent (if any) as a sub-goal.
- Hook into `BudgetGuard.consume(...)` so that, when a goal is active, we also append a `Call` to the innermost goal. This keeps all existing call accounting intact (no breaking change) and adds goal-bucketing as a side effect.
- `cost_usd` = own calls + sub-goal totals (no double-count: own calls only contain direct `consume` calls; sub-goals' calls live on the sub-goal objects).
- `failure_cost` = cost of all calls in failed attempts. An attempt is failed if it is not the final attempt of a successful goal. If `not succeeded`, all calls are failure cost.
- Verifier MUST be a callable returning bool. We do not catch verifier exceptions — they propagate (fail loudly per global instructions).

## Files likely to touch
- `sdk/agentguard/goal.py` (new)
- `sdk/agentguard/guards.py` (BudgetGuard.goal method + hook into consume)
- `sdk/agentguard/__init__.py` (export Goal)
- `sdk/tests/test_goal.py` (new)
- `sdk/README.md` (new section)
- `README.md` at repo root if it mirrors

## Done checklist
- [ ] `Goal` exposes `cost_usd`, `attempts`, `succeeded`, `failure_cost`, `duration_sec`, `calls`, `to_dict()`.
- [ ] `BudgetGuard.goal(name, verifier)` works as a context manager.
- [ ] Nested goals: parent total = own + sub totals, no double count.
- [ ] Happy path test (1 attempt, succeeds).
- [ ] 3-attempts-then-success test (failure_cost > 0).
- [ ] Nested goals test.
- [ ] Failed goal test (succeeded=False, full cost = failure cost).
- [ ] README section "Goal-level metering".
- [ ] All existing tests still pass.
- [ ] No new external deps.

## Risks / assumptions
- Hooking into `BudgetGuard.consume` is the right integration point. Alternative would be a separate `record_call` API, but consume is already where every cost lands. The hook is one append; zero behavior change when no goal is active.
- Contextvars are the right propagation mechanism (async + threadpool safe, as the paper assumes). The standard lib provides this — no new deps.
- Verifier contract is binary bool in v1 (per task scope). Fuzzy verifiers are v2.
- Per the concept page sketch, the `guard` in `with guard.goal(...)` is a `BudgetGuard` instance (the only "guard" with cost state). The concept page's reference to `AgentGuard(budget_usd=5.00)` is aspirational naming — current package uses `BudgetGuard(max_cost_usd=...)`. We stay consistent with the existing API.
