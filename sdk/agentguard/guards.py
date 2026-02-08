"""Runtime guards for AI agents: loop detection, budget enforcement, timeout.

Usage::

    from agentguard import LoopGuard, BudgetGuard, TimeoutGuard

    loop = LoopGuard(max_repeats=3)
    loop.check("search", {"query": "docs"})

    budget = BudgetGuard(max_cost_usd=5.00)
    budget.consume(tokens=150, calls=1, cost_usd=0.02)

    timeout = TimeoutGuard(max_seconds=30)
    timeout.start()
    timeout.check()
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, Optional, Tuple
import json
import time


class LoopDetected(RuntimeError):
    """Raised when a tool call loop is detected by LoopGuard."""
    pass


class BudgetExceeded(RuntimeError):
    """Raised when a budget limit is exceeded by BudgetGuard."""
    pass


class TimeoutExceeded(RuntimeError):
    """Raised when an agent run exceeds its time limit."""
    pass


class LoopGuard:
    """Detect repeated identical tool calls within a sliding window.

    Tracks the last ``window`` tool calls and raises ``LoopDetected`` if
    the same (tool_name, tool_args) pair appears ``max_repeats`` times
    consecutively at the end of the window.

    Usage::

        guard = LoopGuard(max_repeats=3, window=6)
        guard.check("search", {"query": "docs"})  # ok
        guard.check("search", {"query": "docs"})  # ok
        guard.check("search", {"query": "docs"})  # raises LoopDetected

    Args:
        max_repeats: How many identical calls in a row trigger detection.
        window: Size of the sliding history window.
    """

    def __init__(self, max_repeats: int = 3, window: int = 6) -> None:
        if max_repeats < 2:
            raise ValueError("max_repeats must be >= 2")
        if window < max_repeats:
            raise ValueError("window must be >= max_repeats")
        self._max_repeats = max_repeats
        self._window = window
        self._history: Deque[Tuple[str, str]] = deque(maxlen=window)

    def check(self, tool_name: str, tool_args: Optional[Dict[str, Any]] = None) -> None:
        """Record a tool call and check for loops.

        Args:
            tool_name: Name of the tool being called.
            tool_args: Arguments passed to the tool.

        Raises:
            LoopDetected: If the same call was repeated max_repeats times.
        """
        args = tool_args or {}
        signature = (tool_name, _stable_json(args))
        self._history.append(signature)
        if len(self._history) < self._max_repeats:
            return
        last_n = list(self._history)[-self._max_repeats:]
        if len(set(last_n)) == 1:
            args_str = _stable_json(args)
            raise LoopDetected(
                f"Loop detected: {tool_name}({args_str}) repeated "
                f"{self._max_repeats} times in last {len(self._history)} calls. "
                f"Consider varying the arguments or breaking the loop."
            )

    def reset(self) -> None:
        """Clear the call history."""
        self._history.clear()

    def __repr__(self) -> str:
        return f"LoopGuard(max_repeats={self._max_repeats}, window={self._window})"


@dataclass
class BudgetState:
    """Tracks accumulated usage for BudgetGuard."""
    tokens_used: int = 0
    calls_used: int = 0
    cost_used: float = 0.0


class BudgetGuard:
    """Enforce token, call, and dollar cost budgets.

    Raises ``BudgetExceeded`` when any configured limit is exceeded.

    Usage::

        guard = BudgetGuard(max_cost_usd=5.00, max_calls=100)
        guard.consume(tokens=150, calls=1, cost_usd=0.02)

    Args:
        max_tokens: Maximum total tokens allowed. None = unlimited.
        max_calls: Maximum total calls allowed. None = unlimited.
        max_cost_usd: Maximum total cost in USD. None = unlimited.
    """

    def __init__(
        self,
        max_tokens: Optional[int] = None,
        max_calls: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
    ) -> None:
        if max_tokens is None and max_calls is None and max_cost_usd is None:
            raise ValueError("Provide max_tokens, max_calls, or max_cost_usd")
        self._max_tokens = max_tokens
        self._max_calls = max_calls
        self._max_cost_usd = max_cost_usd
        self.state = BudgetState()

    def consume(self, tokens: int = 0, calls: int = 0, cost_usd: float = 0.0) -> None:
        """Record resource consumption and check limits.

        Args:
            tokens: Number of tokens consumed.
            calls: Number of API calls made.
            cost_usd: Dollar cost of this consumption.

        Raises:
            TypeError: If any argument is not a number.
            BudgetExceeded: If any configured limit is exceeded.
        """
        if not isinstance(tokens, (int, float)):
            raise TypeError(
                f"tokens must be a number, got {type(tokens).__name__}: {tokens!r}"
            )
        if not isinstance(calls, (int, float)):
            raise TypeError(
                f"calls must be a number, got {type(calls).__name__}: {calls!r}"
            )
        if not isinstance(cost_usd, (int, float)):
            raise TypeError(
                f"cost_usd must be a number, got {type(cost_usd).__name__}: {cost_usd!r}"
            )
        self.state.tokens_used += tokens
        self.state.calls_used += calls
        self.state.cost_used += cost_usd
        if self._max_tokens is not None and self.state.tokens_used > self._max_tokens:
            raise BudgetExceeded(
                f"Token budget exceeded: {self.state.tokens_used} > {self._max_tokens} "
                f"(this call added {tokens} tokens)"
            )
        if self._max_calls is not None and self.state.calls_used > self._max_calls:
            raise BudgetExceeded(
                f"Call budget exceeded: {self.state.calls_used} > {self._max_calls} "
                f"(this call added {calls} calls)"
            )
        if self._max_cost_usd is not None and self.state.cost_used > self._max_cost_usd:
            raise BudgetExceeded(
                f"Cost budget exceeded: ${self.state.cost_used:.4f} > ${self._max_cost_usd:.4f} "
                f"(this call added ${cost_usd:.4f})"
            )

    def reset(self) -> None:
        """Reset all usage counters to zero."""
        self.state = BudgetState()

    def __repr__(self) -> str:
        parts = []
        if self._max_tokens is not None:
            parts.append(f"max_tokens={self._max_tokens}")
        if self._max_calls is not None:
            parts.append(f"max_calls={self._max_calls}")
        if self._max_cost_usd is not None:
            parts.append(f"max_cost_usd={self._max_cost_usd}")
        return f"BudgetGuard({', '.join(parts)})"


class TimeoutGuard:
    """Enforce a wall-clock time limit on agent runs.

    Usage::

        guard = TimeoutGuard(max_seconds=30)
        guard.start()
        # ... do work ...
        guard.check()  # raises TimeoutExceeded if over limit

    Args:
        max_seconds: Maximum allowed elapsed time in seconds.
    """

    def __init__(self, max_seconds: float) -> None:
        if max_seconds <= 0:
            raise ValueError("max_seconds must be > 0")
        self._max_seconds = max_seconds
        self._start: Optional[float] = None

    def start(self) -> None:
        """Start the timer. Must be called before check()."""
        self._start = time.monotonic()

    def check(self) -> None:
        """Check if the time limit has been exceeded.

        Raises:
            RuntimeError: If start() was not called first.
            TimeoutExceeded: If elapsed time exceeds max_seconds.
        """
        if self._start is None:
            raise RuntimeError("TimeoutGuard.start() must be called before check()")
        elapsed = time.monotonic() - self._start
        if elapsed > self._max_seconds:
            raise TimeoutExceeded(
                f"Run exceeded {self._max_seconds}s timeout "
                f"(elapsed: {elapsed:.2f}s)"
            )

    def reset(self) -> None:
        """Reset the timer."""
        self._start = None

    def __repr__(self) -> str:
        return f"TimeoutGuard(max_seconds={self._max_seconds})"


def _stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))
