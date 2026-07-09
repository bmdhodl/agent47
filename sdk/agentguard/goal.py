"""Goal-level metering for AgentGuard.

A ``Goal`` is a user-meaningful outcome (e.g. "refund this charge"). One goal
may span many model calls, tool calls, retries, and dead ends. Per-call cost
metering hides that structure; goal-level metering exposes it.

Use ``BudgetGuard.goal(name, verifier=..., max_cost_usd=...)`` to open a goal
block. Any cost consumed via ``BudgetGuard.consume(...)`` inside that block
accumulates against the goal. Optional per-goal limits raise ``BudgetExceeded``
when the goal ledger (including nested sub-goals) crosses the cap. On exit, the
verifier runs and ``g.succeeded`` is populated. Failed attempts (anything before
the final attempt of a successful goal, or every attempt of a failed goal)
accrue ``g.failure_cost``.

See ``concepts/cost-per-completed-goal`` in the knowledge wiki for the design
rationale.
"""
from __future__ import annotations

import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar, copy_context
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
        max_tokens / max_calls / max_cost_usd: Optional hard caps for this goal.
        calls: Direct calls recorded inside this goal (not sub-goals).
        sub_goals: Child goals opened inside this goal's block.
        attempts: Number of attempts (incremented by ``attempt()`` from agent code).
        succeeded: Whether the verifier returned True. ``None`` until exit.
        start_ts: Wall-clock at block enter.
        end_ts: Wall-clock at block exit. ``None`` until exit.
    """

    name: str
    verifier: Callable[[], bool]
    max_tokens: Optional[int] = None
    max_calls: Optional[int] = None
    max_cost_usd: Optional[float] = None
    warn_at_pct: Optional[float] = None
    on_warning: Optional[Callable[["Goal", str], None]] = None
    _warned: bool = False
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
    def own_tokens(self) -> int:
        """Tokens of direct calls, excluding sub-goals."""
        return sum(int(c.tokens) for c in self.calls)

    @property
    def tokens_used(self) -> int:
        """Total tokens: direct calls + sub-goal totals."""
        return self.own_tokens + sum(g.tokens_used for g in self.sub_goals)

    @property
    def own_calls(self) -> int:
        """Call count of direct records, excluding sub-goals."""
        return sum(int(c.calls) for c in self.calls)

    @property
    def calls_used(self) -> int:
        """Total calls: direct records + sub-goal totals."""
        return self.own_calls + sum(g.calls_used for g in self.sub_goals)

    def _check_warning(self) -> None:
        """Fire on_warning once when this goal crosses warn_at_pct of a cap."""
        if self._warned or self.warn_at_pct is None:
            return
        pct = self.warn_at_pct
        parts: List[str] = []
        if self.max_tokens is not None and self.max_tokens > 0:
            ratio = self.tokens_used / self.max_tokens
            if ratio >= pct:
                parts.append(f"tokens {ratio:.0%}")
        if self.max_calls is not None and self.max_calls > 0:
            ratio = self.calls_used / self.max_calls
            if ratio >= pct:
                parts.append(f"calls {ratio:.0%}")
        if self.max_cost_usd is not None and self.max_cost_usd > 0:
            ratio = self.cost_usd / self.max_cost_usd
            if ratio >= pct:
                parts.append(f"cost {ratio:.0%}")
        if not parts:
            return
        self._warned = True
        msg = (
            f"Goal {self.name!r} budget warning: {', '.join(parts)} "
            f"of limit reached (threshold: {pct:.0%})"
        )
        if self.on_warning is not None:
            self.on_warning(self, msg)

    def _enforce_limits(
        self,
        added_tokens: float,
        added_calls: float,
        added_cost: float,
    ) -> None:
        """Raise BudgetExceeded if this goal's ledger exceeds a configured cap.

        Includes nested sub-goal spend. Message names the goal so operators can
        tell session-limit failures from task-limit failures.
        """
        # Local import avoids a circular import at module load (guards -> goal).
        from .guards import BudgetExceeded

        if self.max_tokens is not None and self.tokens_used > self.max_tokens:
            raise BudgetExceeded(
                f"Goal {self.name!r} token budget exceeded: "
                f"{self.tokens_used} > {self.max_tokens} "
                f"(this call added {added_tokens} tokens)"
            )
        if self.max_calls is not None and self.calls_used > self.max_calls:
            raise BudgetExceeded(
                f"Goal {self.name!r} call budget exceeded: "
                f"{self.calls_used} > {self.max_calls} "
                f"(this call added {added_calls} calls)"
            )
        if self.max_cost_usd is not None and self.cost_usd > self.max_cost_usd:
            raise BudgetExceeded(
                f"Goal {self.name!r} cost budget exceeded: "
                f"${self.cost_usd:.4f} > ${self.max_cost_usd:.4f} "
                f"(this call added ${added_cost:.4f})"
            )

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
            "tokens_used": self.tokens_used,
            "calls_used": self.calls_used,
            "failure_cost": self.failure_cost,
            "attempts": self.attempts,
            "succeeded": self.succeeded,
            "duration_sec": self.duration_sec,
            "max_tokens": self.max_tokens,
            "max_calls": self.max_calls,
            "max_cost_usd": self.max_cost_usd,
            "calls": [c.to_dict() for c in self.calls],
            "sub_goals": [g.to_dict() for g in self.sub_goals],
        }


# Stack of active goals, innermost last. Goals are popped on block exit.
# ContextVar so async + threadpool callsites see the correct innermost goal.
_active_goals: ContextVar[Tuple[Goal, ...]] = ContextVar(
    "agentguard_active_goals", default=()
)
_submit_patch_lock = threading.Lock()
_submit_patch_depth = 0
_original_threadpool_submit = None


def _current_goal() -> Optional[Goal]:
    """Return the innermost active goal, or None if no goal block is open."""
    stack = _active_goals.get()
    return stack[-1] if stack else None


def _install_threadpool_context_patch() -> None:
    """Propagate the active goal context through ThreadPoolExecutor.submit."""
    global _original_threadpool_submit, _submit_patch_depth
    with _submit_patch_lock:
        if _submit_patch_depth == 0:
            _original_threadpool_submit = ThreadPoolExecutor.submit

            def submit_with_context(executor, fn, *args, **kwargs):
                ctx = copy_context()

                def run_with_context(*run_args, **run_kwargs):
                    return ctx.run(fn, *run_args, **run_kwargs)

                return _original_threadpool_submit(
                    executor, run_with_context, *args, **kwargs
                )

            ThreadPoolExecutor.submit = submit_with_context  # type: ignore[method-assign]
        _submit_patch_depth += 1


def _uninstall_threadpool_context_patch() -> None:
    global _original_threadpool_submit, _submit_patch_depth
    with _submit_patch_lock:
        if _submit_patch_depth == 0:
            return
        _submit_patch_depth -= 1
        if _submit_patch_depth == 0 and _original_threadpool_submit is not None:
            ThreadPoolExecutor.submit = _original_threadpool_submit
            _original_threadpool_submit = None


class _GoalContext:
    """Context manager returned by ``BudgetGuard.goal(...)``.

    Exiting the block runs the verifier and finalizes the goal ledger.
    Verifier exceptions propagate (fail loudly).
    """

    def __init__(
        self,
        name: str,
        verifier: Callable[[], bool],
        *,
        max_tokens: Optional[int] = None,
        max_calls: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
        warn_at_pct: Optional[float] = None,
        on_warning: Optional[Callable[["Goal", str], None]] = None,
    ) -> None:
        if not callable(verifier):
            raise TypeError(
                f"verifier must be callable, got {type(verifier).__name__}"
            )
        for limit_name, limit_val in (
            ("max_tokens", max_tokens),
            ("max_calls", max_calls),
            ("max_cost_usd", max_cost_usd),
        ):
            if limit_val is None:
                continue
            if isinstance(limit_val, float) and not math.isfinite(limit_val):
                raise ValueError(
                    f"{limit_name} must be finite, got {limit_val!r}"
                )
            if limit_val < 0:
                raise ValueError(
                    f"{limit_name} must be non-negative, got {limit_val!r}"
                )
        if warn_at_pct is not None:
            if not isinstance(warn_at_pct, (int, float)) or isinstance(
                warn_at_pct, bool
            ):
                raise TypeError(
                    f"warn_at_pct must be a number, got {type(warn_at_pct).__name__}"
                )
            if isinstance(warn_at_pct, float) and not math.isfinite(warn_at_pct):
                raise ValueError(f"warn_at_pct must be finite, got {warn_at_pct!r}")
            if not (0.0 < float(warn_at_pct) <= 1.0):
                raise ValueError(
                    f"warn_at_pct must be in (0, 1], got {warn_at_pct!r}"
                )
            if max_tokens is None and max_calls is None and max_cost_usd is None:
                raise ValueError(
                    "warn_at_pct requires max_tokens, max_calls, or max_cost_usd"
                )
        if on_warning is not None and not callable(on_warning):
            raise TypeError(
                f"on_warning must be callable, got {type(on_warning).__name__}"
            )
        self._goal = Goal(
            name=name,
            verifier=verifier,
            max_tokens=max_tokens,
            max_calls=max_calls,
            max_cost_usd=max_cost_usd,
            warn_at_pct=float(warn_at_pct) if warn_at_pct is not None else None,
            on_warning=on_warning,
        )
        self._token = None  # type: ignore[assignment]

    def __enter__(self) -> Goal:
        parent = _current_goal()
        if parent is not None:
            parent.sub_goals.append(self._goal)
        self._goal.start_ts = time.time()
        self._token = _active_goals.set((*_active_goals.get(), self._goal))
        _install_threadpool_context_patch()
        return self._goal

    def __exit__(self, exc_type, exc, tb) -> None:
        self._goal.end_ts = time.time()
        if self._token is not None:
            _active_goals.reset(self._token)
        _uninstall_threadpool_context_patch()
        # Only run the verifier if the block exited cleanly. If an exception
        # is propagating, the goal clearly did not succeed; do not also swallow
        # by calling the verifier.
        if exc_type is None:
            self._goal.succeeded = bool(self._goal.verifier())
        else:
            self._goal.succeeded = False


def _record_consume(tokens: int, calls: int, cost_usd: float) -> None:
    """Attribute a consume call to the innermost active goal, if any.

    Does not enforce per-goal limits; call ``_enforce_active_goal_limits`` after
    session state is updated so both ledgers include the tripping call.
    """
    goal = _current_goal()
    if goal is None:
        return
    goal._record(_build_call(goal, tokens, calls, cost_usd))


def _enforce_active_goal_limits(
    tokens: float, calls: float, cost_usd: float
) -> None:
    """Enforce hard caps on the full active goal stack (innermost first)."""
    stack = _active_goals.get()
    if not stack:
        return
    for active in reversed(stack):
        active._check_warning()
        active._enforce_limits(tokens, calls, cost_usd)


def _build_call(goal: Goal, tokens: int, calls: int, cost_usd: float) -> Call:
    return Call(
        tokens=int(tokens),
        calls=int(calls),
        cost_usd=float(cost_usd),
        attempt_idx=goal.attempts if goal.attempts > 0 else 1,
        ts=time.time(),
    )
