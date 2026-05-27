"""Goal-level metering for AgentGuard.

A ``Goal`` is a user-meaningful outcome (e.g. "refund this charge"). One goal
may span many model calls, tool calls, retries, and dead ends. Per-call cost
metering hides that structure; goal-level metering exposes it.

Use ``BudgetGuard.goal(name, verifier=...)`` to open a goal block. Any cost
consumed via ``BudgetGuard.consume(...)`` inside that block accumulates against
the goal. On exit, the verifier runs and ``g.succeeded`` is populated. Failed
attempts (anything before the final attempt of a successful goal, or every
attempt of a failed goal) accrue ``g.failure_cost``.

See ``concepts/cost-per-completed-goal`` in the knowledge wiki for the design
rationale.
"""
from __future__ import annotations

import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple


@dataclass
class Call:
    """A single accounted call inside a goal block."""

    tokens: int
    calls: int
    cost_usd: float
    attempt_idx: int
    ts: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tokens": self.tokens,
            "calls": self.calls,
            "cost_usd": self.cost_usd,
            "attempt_idx": self.attempt_idx,
            "ts": self.ts,
        }


@dataclass
class Goal:
    """A goal ledger.

    Populated as nested calls execute inside ``BudgetGuard.goal(...)``. The
    block-exit handler runs the verifier and sets ``succeeded``.

    Attributes:
        name: Caller-supplied label for the goal.
        verifier: Zero-arg callable returning bool. Runs on block exit.
        calls: Direct calls recorded inside this goal (not sub-goals).
        sub_goals: Child goals opened inside this goal's block.
        attempts: Number of attempts (incremented by ``attempt()`` from agent code).
        succeeded: Whether the verifier returned True. ``None`` until exit.
        start_ts: Wall-clock at block enter.
        end_ts: Wall-clock at block exit. ``None`` until exit.
    """

    name: str
    verifier: Callable[[], bool]
    calls: List[Call] = field(default_factory=list)
    sub_goals: List["Goal"] = field(default_factory=list)
    attempts: int = 0
    succeeded: Optional[bool] = None
    start_ts: float = 0.0
    end_ts: Optional[float] = None

    def attempt(self) -> int:
        """Mark the start of a new attempt. Returns the new attempt index (1-based).

        Agent code calls this at the top of each retry so failure cost can be
        attributed correctly. Explicit per task scope (v1 does not auto-detect
        attempts).
        """
        self.attempts += 1
        return self.attempts

    def _record(self, call: Call) -> None:
        """Append a Call. Intended for internal use by ``BudgetGuard.consume``."""
        self.calls.append(call)

    @property
    def own_cost_usd(self) -> float:
        """Cost of direct calls, excluding sub-goals."""
        return sum(c.cost_usd for c in self.calls)

    @property
    def cost_usd(self) -> float:
        """Total cost: direct calls + sub-goal totals. No double count."""
        return self.own_cost_usd + sum(g.cost_usd for g in self.sub_goals)

    @property
    def failure_cost(self) -> float:
        """Cost of calls in failed attempts.

        If the goal succeeded and ``attempts >= 1``, calls with
        ``attempt_idx < attempts`` are failure cost (the final attempt is the
        winning one). If the goal failed, every direct call is failure cost.
        Sub-goal failure cost rolls up the same way.
        """
        if self.succeeded is False:
            own = self.own_cost_usd
        elif self.succeeded is True and self.attempts >= 1:
            final = self.attempts
            own = sum(c.cost_usd for c in self.calls if c.attempt_idx < final)
        else:
            # succeeded is None (still open) or attempts == 0
            own = 0.0
        return own + sum(g.failure_cost for g in self.sub_goals)

    @property
    def duration_sec(self) -> float:
        end = self.end_ts if self.end_ts is not None else time.time()
        return end - self.start_ts

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict suitable for JSON."""
        return {
            "name": self.name,
            "cost_usd": self.cost_usd,
            "own_cost_usd": self.own_cost_usd,
            "failure_cost": self.failure_cost,
            "attempts": self.attempts,
            "succeeded": self.succeeded,
            "duration_sec": self.duration_sec,
            "calls": [c.to_dict() for c in self.calls],
            "sub_goals": [g.to_dict() for g in self.sub_goals],
        }


# Stack of active goals, innermost last. Goals are popped on block exit.
# ContextVar so async + threadpool callsites see the correct innermost goal.
_active_goals: ContextVar[Tuple[Goal, ...]] = ContextVar(
    "agentguard_active_goals", default=()
)


def _current_goal() -> Optional[Goal]:
    """Return the innermost active goal, or None if no goal block is open."""
    stack = _active_goals.get()
    return stack[-1] if stack else None


class _GoalContext:
    """Context manager returned by ``BudgetGuard.goal(...)``.

    Exiting the block runs the verifier and finalizes the goal ledger.
    Verifier exceptions propagate (fail loudly).
    """

    def __init__(self, name: str, verifier: Callable[[], bool]) -> None:
        if not callable(verifier):
            raise TypeError(
                f"verifier must be callable, got {type(verifier).__name__}"
            )
        self._goal = Goal(name=name, verifier=verifier)
        self._token = None  # type: ignore[assignment]

    def __enter__(self) -> Goal:
        parent = _current_goal()
        if parent is not None:
            parent.sub_goals.append(self._goal)
        self._goal.start_ts = time.time()
        self._token = _active_goals.set((*_active_goals.get(), self._goal))
        return self._goal

    def __exit__(self, exc_type, exc, tb) -> None:
        self._goal.end_ts = time.time()
        if self._token is not None:
            _active_goals.reset(self._token)
        # Only run the verifier if the block exited cleanly. If an exception
        # is propagating, the goal clearly did not succeed; do not also swallow
        # by calling the verifier.
        if exc_type is None:
            self._goal.succeeded = bool(self._goal.verifier())
        else:
            self._goal.succeeded = False


def _record_consume(tokens: int, calls: int, cost_usd: float) -> None:
    """Hook called from ``BudgetGuard.consume`` to attribute the call to the
    innermost active goal, if any. No-op when no goal is active.
    """
    goal = _current_goal()
    if goal is None:
        return
    goal._record(
        Call(
            tokens=int(tokens),
            calls=int(calls),
            cost_usd=float(cost_usd),
            attempt_idx=goal.attempts if goal.attempts > 0 else 1,
            ts=time.time(),
        )
    )
