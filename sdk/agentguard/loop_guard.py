"""LoopGuard: stop repeated tool calls, including reworded ones."""
from __future__ import annotations

import threading
from collections import deque
from typing import Any, Deque, Dict, Optional, Tuple

from ._loop_match import advance_streak, describe_outcome, normalize_args, outcome_of
from ._loop_match import stable_json as _stable_json
from .guards import BaseGuard, LoopDetected, _extract_tool_name


class LoopGuard(BaseGuard):
    """Detect repeated identical tool calls within a sliding window.

    Thread-safe. Uses a lock to protect history mutations.

    Tracks the last ``window`` tool calls and raises ``LoopDetected`` if
    the same (tool_name, tool_args) pair appears ``max_repeats`` times
    consecutively at the end of the window.

    Usage::

        guard = LoopGuard(max_repeats=3, window=6)
        guard.check("search", {"query": "docs"})  # ok
        guard.check("search", {"query": "docs"})  # ok
        guard.check("search", {"query": "docs"})  # raises LoopDetected

    Reworded loops are opt-in. ``normalize=True`` also matches calls that differ
    only in case or whitespace. ``max_no_progress=N`` raises when one tool comes
    back empty, or with the same error, N results in a row whatever its args;
    feed outcomes with ``record_result()`` or ``tool.result`` / ``tool.error``
    trace events. Any other result in between starts the count over.

    Args:
        max_repeats: How many identical calls in a row trigger detection.
        window: Size of the sliding history window.
        normalize: Ignore case and whitespace in string arguments.
        max_no_progress: Empty or same-error results in a row that trigger
            detection. None (default) turns the check off.
    """

    def __init__(self, max_repeats: int = 3, window: int = 6, *, normalize: bool = False,
                 max_no_progress: Optional[int] = None) -> None:
        if max_repeats < 2:
            raise ValueError("max_repeats must be >= 2")
        if window < max_repeats:
            raise ValueError("window must be >= max_repeats")
        if max_no_progress is not None and (isinstance(max_no_progress, bool) or max_no_progress < 2):
            raise ValueError("max_no_progress must be >= 2 or None")
        self._max_repeats = max_repeats
        self._window = window
        self._normalize = normalize
        self._max_no_progress = max_no_progress
        self._stall: Optional[Dict[str, Any]] = None
        self._history: Deque[Tuple[str, str]] = deque(maxlen=window)
        self._lock = threading.Lock()

    def check(self, tool_name: str, tool_args: Optional[Dict[str, Any]] = None) -> None:
        """Record a tool call and check for loops.

        Thread-safe: uses a lock to protect history mutations.

        Args:
            tool_name: Name of the tool being called.
            tool_args: Arguments passed to the tool.

        Raises:
            LoopDetected: If the same call was repeated max_repeats times.
        """
        args = tool_args or {}
        signature = (tool_name, _stable_json(normalize_args(args) if self._normalize else args))
        with self._lock:
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

    def record_result(self, tool_name: str, result: Any = None, *, error: Any = None,
                      tool_args: Optional[Dict[str, Any]] = None) -> None:
        """Record a tool outcome. A no-op unless ``max_no_progress`` is set.

        Raises:
            LoopDetected: If ``tool_name`` came back empty, or with the same
                error, ``max_no_progress`` times in a row.
        """
        if self._max_no_progress is None:
            return
        outcome = outcome_of(result, error, tool_args)
        with self._lock:
            self._stall = advance_streak(self._stall, tool_name, outcome)
            count = self._stall["count"] if self._stall else 0
        if count >= self._max_no_progress:
            raise LoopDetected(
                f"No progress: {tool_name} {describe_outcome(outcome)} {count} times in a row "
                f"(limit: {self._max_no_progress}), last args {_stable_json(tool_args or {})}. "
                f"Change the approach instead of rewording the call."
            )

    def auto_check(self, event_name: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Auto-check: delegates to check(); tool.result / tool.error also feed record_result()."""
        self.check(event_name, event_data)
        tool_name = _extract_tool_name(event_name, event_data)
        if self._max_no_progress is None or not tool_name:
            return
        data = event_data or {}
        if event_name == "tool.error":
            self.record_result(tool_name, error=f"{data.get('error_type', '')}: {data.get('message', '')}")
        elif event_name == "tool.result":
            self.record_result(tool_name, data.get("result", data.get("output")))

    @property
    def max_repeats(self) -> int:
        """Maximum identical calls before triggering detection."""
        return self._max_repeats

    @property
    def window(self) -> int:
        """Size of the sliding history window."""
        return self._window

    def reset(self) -> None:
        """Clear the call history."""
        with self._lock:
            self._history.clear()
            self._stall = None

    def __repr__(self) -> str:
        extra = ", normalize=True" if self._normalize else ""
        if self._max_no_progress is not None:
            extra += f", max_no_progress={self._max_no_progress}"
        return f"LoopGuard(max_repeats={self._max_repeats}, window={self._window}{extra})"
