from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any, Deque, Dict, Optional, Tuple
import json
import time


class LoopDetected(RuntimeError):
    pass


class BudgetExceeded(RuntimeError):
    pass


class TimeoutExceeded(RuntimeError):
    pass


class LoopGuard:
    def __init__(self, max_repeats: int = 3, window: int = 6) -> None:
        if max_repeats < 2:
            raise ValueError("max_repeats must be >= 2")
        if window < max_repeats:
            raise ValueError("window must be >= max_repeats")
        self._max_repeats = max_repeats
        self._history: Deque[Tuple[str, str]] = deque(maxlen=window)

    def check(self, tool_name: str, tool_args: Optional[Dict[str, Any]] = None) -> None:
        args = tool_args or {}
        signature = (tool_name, _stable_json(args))
        self._history.append(signature)
        if len(self._history) < self._max_repeats:
            return
        last_n = list(self._history)[-self._max_repeats :]
        if len(set(last_n)) == 1:
            raise LoopDetected(
                f"Detected repeated tool call {tool_name} {self._max_repeats} times"
            )

    def reset(self) -> None:
        self._history.clear()


@dataclass
class BudgetState:
    tokens_used: int = 0
    calls_used: int = 0
    cost_used: float = 0.0


class BudgetGuard:
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
                f"Token budget exceeded: {self.state.tokens_used} > {self._max_tokens}"
            )
        if self._max_calls is not None and self.state.calls_used > self._max_calls:
            raise BudgetExceeded(
                f"Call budget exceeded: {self.state.calls_used} > {self._max_calls}"
            )
        if self._max_cost_usd is not None and self.state.cost_used > self._max_cost_usd:
            raise BudgetExceeded(
                f"Cost budget exceeded: ${self.state.cost_used:.4f} > ${self._max_cost_usd:.4f}"
            )

    def reset(self) -> None:
        self.state = BudgetState()


class TimeoutGuard:
    def __init__(self, max_seconds: float) -> None:
        if max_seconds <= 0:
            raise ValueError("max_seconds must be > 0")
        self._max_seconds = max_seconds
        self._start: Optional[float] = None

    def start(self) -> None:
        self._start = time.monotonic()

    def check(self) -> None:
        if self._start is None:
            raise RuntimeError("TimeoutGuard.start() must be called before check()")
        if (time.monotonic() - self._start) > self._max_seconds:
            raise TimeoutExceeded(
                f"Run exceeded {self._max_seconds}s timeout"
            )

    def reset(self) -> None:
        self._start = None


def _stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))
