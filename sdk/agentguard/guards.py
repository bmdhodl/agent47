"""Runtime guards for AI agents: loop detection, budget enforcement, timeout.

Usage::

    from agentguard import LoopGuard, BudgetGuard, TimeoutGuard

    loop = LoopGuard(max_repeats=3)
    loop.check("search", {"query": "docs"})

    budget = BudgetGuard(max_cost_usd=5.00)
    budget.consume(tokens=150, calls=1, cost_usd=0.02)

    timeout = TimeoutGuard(max_seconds=30)
    with timeout:
        timeout.check()
"""
from __future__ import annotations

import json
import threading
import time
from collections import Counter, deque
from dataclasses import dataclass
from typing import Any, Callable, Deque, Dict, Optional, Tuple
from urllib.parse import urlparse


class AgentGuardError(Exception):
    """Base exception for all AgentGuard errors.

    Catch this to handle any error raised by the AgentGuard SDK::

        try:
            guard.check("tool", args)
        except AgentGuardError:
            # handle any AgentGuard error
            pass
    """


class LoopDetected(AgentGuardError, RuntimeError):
    """Raised when a tool call loop is detected by LoopGuard."""
    pass


class BudgetExceeded(AgentGuardError, RuntimeError):
    """Raised when a budget limit is exceeded by BudgetGuard."""
    pass


class BudgetWarning(UserWarning):
    """Emitted when budget usage crosses the warn_at_pct threshold."""
    pass


class TimeoutExceeded(AgentGuardError, RuntimeError):
    """Raised when an agent run exceeds its time limit."""
    pass


class AgentKilled(AgentGuardError, RuntimeError):
    """Raised when an agent is killed via a remote dashboard signal.

    This exception is raised by ``RemoteGuard`` when the dashboard
    sends a kill signal for the running agent::

        try:
            guard.check()
        except AgentKilled:
            print("Agent was stopped remotely")
    """
    pass




class BaseGuard:
    """Base class for all guards.

    Subclass and override ``auto_check()`` to integrate with the Tracer's
    automatic guard dispatch. Override ``reset()`` to clear state.

    Usage::

        class MyGuard(BaseGuard):
            def auto_check(self, event_name, event_data=None):
                if event_name == "tool.dangerous":
                    raise RuntimeError("Blocked!")
    """

    def auto_check(self, event_name: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Called automatically by the Tracer on each emitted event.

        Override in subclasses to participate in auto-checking.
        The default implementation is a no-op.

        Args:
            event_name: Name of the event being emitted.
            event_data: Optional data attached to the event.
        """

    def reset(self) -> None:
        """Reset guard state. Override in subclasses."""


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
        signature = (tool_name, _stable_json(args))
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

    def auto_check(self, event_name: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Auto-check: delegates to check(event_name, event_data)."""
        self.check(event_name, event_data)

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

    def __repr__(self) -> str:
        return f"LoopGuard(max_repeats={self._max_repeats}, window={self._window})"


@dataclass
class BudgetState:
    """Tracks accumulated usage for BudgetGuard."""
    tokens_used: int = 0
    calls_used: int = 0
    cost_used: float = 0.0


class BudgetGuard(BaseGuard):
    """Enforce token, call, and dollar cost budgets.

    Thread-safe. Raises ``BudgetExceeded`` when any configured limit is
    exceeded. Optionally calls ``on_warning`` when usage crosses
    ``warn_at_pct``.

    Usage::

        guard = BudgetGuard(max_cost_usd=5.00, max_calls=100)
        guard.consume(tokens=150, calls=1, cost_usd=0.02)

        # With warning callback at 80%:
        guard = BudgetGuard(
            max_cost_usd=5.00,
            warn_at_pct=0.8,
            on_warning=lambda msg: print(f"WARNING: {msg}"),
        )

    Args:
        max_tokens: Maximum total tokens allowed. None = unlimited.
        max_calls: Maximum total calls allowed. None = unlimited.
        max_cost_usd: Maximum total cost in USD. None = unlimited.
        warn_at_pct: Fraction (0.0-1.0) at which to trigger a warning. None = no warning.
        on_warning: Callback invoked with a message when warn_at_pct is crossed.
    """

    def __init__(
        self,
        max_tokens: Optional[int] = None,
        max_calls: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
        warn_at_pct: Optional[float] = None,
        on_warning: Optional[Callable[[str], None]] = None,
    ) -> None:
        if max_tokens is None and max_calls is None and max_cost_usd is None:
            raise ValueError("Provide max_tokens, max_calls, or max_cost_usd")
        self._max_tokens = max_tokens
        self._max_calls = max_calls
        self._max_cost_usd = max_cost_usd
        self._warn_at_pct = warn_at_pct
        self._on_warning = on_warning
        self._warned = False
        self._lock = threading.Lock()
        self.state = BudgetState()

    @property
    def max_tokens(self) -> Optional[int]:
        """Maximum total tokens allowed, or None if unlimited."""
        return self._max_tokens

    @property
    def max_calls(self) -> Optional[int]:
        """Maximum total calls allowed, or None if unlimited."""
        return self._max_calls

    @property
    def max_cost_usd(self) -> Optional[float]:
        """Maximum total cost in USD, or None if unlimited."""
        return self._max_cost_usd

    def consume(self, tokens: int = 0, calls: int = 0, cost_usd: float = 0.0) -> None:
        """Record resource consumption and check limits.

        Thread-safe: uses a lock to protect state mutations.

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
        with self._lock:
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
            # Check warning threshold
            if self._warn_at_pct is not None and not self._warned:
                self._check_warning()

    def _check_warning(self) -> None:
        """Emit a warning if usage crosses the warn_at_pct threshold.

        Must be called while holding self._lock.
        """
        pct = self._warn_at_pct
        if pct is None:  # pragma: no cover — defensive; caller checks first
            return
        triggered = False
        parts = []
        if self._max_tokens is not None:
            ratio = self.state.tokens_used / self._max_tokens
            if ratio >= pct:
                triggered = True
                parts.append(f"tokens {ratio:.0%}")
        if self._max_calls is not None:
            ratio = self.state.calls_used / self._max_calls
            if ratio >= pct:
                triggered = True
                parts.append(f"calls {ratio:.0%}")
        if self._max_cost_usd is not None:
            ratio = self.state.cost_used / self._max_cost_usd
            if ratio >= pct:
                triggered = True
                parts.append(f"cost {ratio:.0%}")
        if triggered:
            self._warned = True
            msg = f"Budget warning: {', '.join(parts)} of limit reached (threshold: {pct:.0%})"
            if self._on_warning:
                self._on_warning(msg)

    @classmethod
    def from_remote(
        cls,
        api_key: str,
        name: str = "default",
        dashboard_url: str = "https://app.agentguard47.com",
        fallback_max_cost_usd: Optional[float] = None,
        fallback_max_tokens: Optional[int] = None,
        fallback_max_calls: Optional[int] = None,
    ) -> "BudgetGuard":
        """Create a BudgetGuard with limits fetched from the dashboard.

        Attempts to fetch budget configuration from the dashboard API.
        Falls back to the provided local defaults if the fetch fails.

        Usage::

            # Fetch limits from dashboard, fall back to $10 max:
            guard = BudgetGuard.from_remote(
                api_key="ag_live_abc123",
                name="production",
                fallback_max_cost_usd=10.00,
            )

        Args:
            api_key: Dashboard API key.
            name: Budget configuration name on the dashboard.
            dashboard_url: Base URL of the dashboard API.
            fallback_max_cost_usd: Local fallback if fetch fails.
            fallback_max_tokens: Local fallback if fetch fails.
            fallback_max_calls: Local fallback if fetch fails.

        Returns:
            A configured BudgetGuard instance.

        Raises:
            ValueError: If no limits are available (neither remote nor fallback).
        """
        import urllib.request as _urllib_request
        from urllib.error import HTTPError as _HTTPError

        parsed = urlparse(dashboard_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"dashboard_url scheme must be http or https, got {parsed.scheme!r}")

        url = f"{dashboard_url.rstrip('/')}/api/v1/budgets?name={name}"
        headers = {"Authorization": f"Bearer {api_key}"}

        max_cost_usd = fallback_max_cost_usd
        max_tokens = fallback_max_tokens
        max_calls = fallback_max_calls

        try:
            req = _urllib_request.Request(url, headers=headers, method="GET")
            with _urllib_request.urlopen(req, timeout=10) as resp:  # nosec B310 — scheme validated above
                data = json.loads(resp.read().decode("utf-8"))
            if "max_cost_usd" in data:
                max_cost_usd = float(data["max_cost_usd"])
            if "max_tokens" in data:
                max_tokens = int(data["max_tokens"])
            if "max_calls" in data:
                max_calls = int(data["max_calls"])
        except (_HTTPError, OSError, json.JSONDecodeError, ValueError, KeyError):
            pass  # Fall back to local defaults

        return cls(
            max_cost_usd=max_cost_usd,
            max_tokens=max_tokens,
            max_calls=max_calls,
        )

    def reset(self) -> None:
        """Reset all usage counters to zero."""
        with self._lock:
            self.state = BudgetState()
            self._warned = False

    def __repr__(self) -> str:
        parts = []
        if self._max_tokens is not None:
            parts.append(f"max_tokens={self._max_tokens}")
        if self._max_calls is not None:
            parts.append(f"max_calls={self._max_calls}")
        if self._max_cost_usd is not None:
            parts.append(f"max_cost_usd={self._max_cost_usd}")
        return f"BudgetGuard({', '.join(parts)})"


class TimeoutGuard(BaseGuard):
    """Enforce a wall-clock time limit on agent runs.

    Can be used as a context manager for convenience::

        with TimeoutGuard(max_seconds=30) as guard:
            # ... do work ...
            guard.check()  # optional mid-run check

    Or manually::

        guard = TimeoutGuard(max_seconds=30)
        guard.start()
        # ... do work ...
        guard.check()

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

    def auto_check(self, event_name: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Auto-check: delegates to check() if the timer has been started."""
        if self._start is not None:
            self.check()

    def __enter__(self) -> "TimeoutGuard":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        if exc_type is None and self._start is not None:
            self.check()
        return False

    def reset(self) -> None:
        """Reset the timer."""
        self._start = None

    def __repr__(self) -> str:
        return f"TimeoutGuard(max_seconds={self._max_seconds})"


class FuzzyLoopGuard(BaseGuard):
    """Detect loops even when tool args vary, and A-B-A-B alternation patterns.

    Thread-safe. Uses a lock to protect history mutations.

    Unlike LoopGuard (exact match only), FuzzyLoopGuard catches:
    - Same tool called repeatedly with different args (frequency check)
    - Two tools alternating: A-B-A-B-A-B (alternation check)

    Usage::

        guard = FuzzyLoopGuard(max_tool_repeats=5, max_alternations=3, window=10)
        guard.check("search", {"q": "docs"})
        guard.check("search", {"q": "api"})    # same tool, different args
        guard.check("search", {"q": "help"})   # still same tool...

    Args:
        max_tool_repeats: Max times the same tool name (any args) can appear in window.
        max_alternations: Max A-B-A-B cycles before triggering.
        window: Sliding window size.
    """

    def __init__(
        self,
        max_tool_repeats: int = 5,
        max_alternations: int = 3,
        window: int = 10,
    ) -> None:
        if max_tool_repeats < 2:
            raise ValueError("max_tool_repeats must be >= 2")
        if max_alternations < 2:
            raise ValueError("max_alternations must be >= 2")
        self._max_tool_repeats = max_tool_repeats
        self._max_alternations = max_alternations
        self._window = window
        self._history: Deque[str] = deque(maxlen=window)
        self._lock = threading.Lock()

    def check(self, tool_name: str, tool_args: Optional[Dict[str, Any]] = None) -> None:
        """Record a tool call and check for fuzzy loop patterns.

        Thread-safe: uses a lock to protect history mutations.

        Args:
            tool_name: Name of the tool being called.
            tool_args: Arguments (used for reporting, not matching).

        Raises:
            LoopDetected: If a fuzzy loop pattern is detected.
        """
        with self._lock:
            self._history.append(tool_name)

            # Frequency check: same tool name too many times in window
            counts = Counter(self._history)
            if counts[tool_name] >= self._max_tool_repeats:
                raise LoopDetected(
                    f"Fuzzy loop: {tool_name} called {counts[tool_name]} times "
                    f"in last {len(self._history)} calls (limit: {self._max_tool_repeats})"
                )

            # Alternation check: A-B-A-B pattern
            if len(self._history) >= self._max_alternations * 2:
                history_list = list(self._history)
                tail = history_list[-(self._max_alternations * 2):]
                a, b = tail[0], tail[1]
                if a != b and all(
                    tail[i] == (a if i % 2 == 0 else b) for i in range(len(tail))
                ):
                    raise LoopDetected(
                        f"Alternation loop: {a} ↔ {b} repeated "
                        f"{self._max_alternations} times"
                    )

    def auto_check(self, event_name: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Auto-check: delegates to check(event_name, event_data)."""
        self.check(event_name, event_data)

    def reset(self) -> None:
        """Clear the call history."""
        with self._lock:
            self._history.clear()

    def __repr__(self) -> str:
        return (
            f"FuzzyLoopGuard(max_tool_repeats={self._max_tool_repeats}, "
            f"max_alternations={self._max_alternations}, window={self._window})"
        )


class RateLimitGuard(BaseGuard):
    """Enforce a maximum call rate using a sliding time window.

    Thread-safe. Uses a lock to protect timestamp mutations.

    Usage::

        guard = RateLimitGuard(max_calls_per_minute=60)
        guard.check()  # call before each API request

    Args:
        max_calls_per_minute: Maximum calls allowed in a 60-second window.
    """

    def __init__(self, max_calls_per_minute: int) -> None:
        if max_calls_per_minute < 1:
            raise ValueError("max_calls_per_minute must be >= 1")
        self._max_calls = max_calls_per_minute
        self._window_seconds = 60.0
        self._timestamps: Deque[float] = deque()
        self._lock = threading.Lock()

    def check(self) -> None:
        """Record a call and check the rate limit.

        Thread-safe: uses a lock to protect timestamp mutations.

        Raises:
            BudgetExceeded: If the call rate exceeds the limit.
        """
        with self._lock:
            now = time.monotonic()
            cutoff = now - self._window_seconds
            # Remove expired timestamps
            while self._timestamps and self._timestamps[0] < cutoff:
                self._timestamps.popleft()
            if len(self._timestamps) >= self._max_calls:
                raise BudgetExceeded(
                    f"Rate limit exceeded: {len(self._timestamps)} calls "
                    f"in the last 60s (limit: {self._max_calls}/min)"
                )
            self._timestamps.append(now)

    def auto_check(self, event_name: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Auto-check: delegates to check()."""
        self.check()

    def reset(self) -> None:
        """Clear the call history."""
        with self._lock:
            self._timestamps.clear()

    def __repr__(self) -> str:
        return f"RateLimitGuard(max_calls_per_minute={self._max_calls})"


class RemoteGuard(BaseGuard):
    """Poll the dashboard for remote kill signals and budget updates.

    Background thread checks ``/api/v1/status`` periodically. On kill signal,
    ``check()`` raises ``AgentKilled``. On budget update, linked BudgetGuard
    limits are modified. Falls back gracefully if network is unavailable.

    Usage::

        guard = RemoteGuard(api_key="ag_live_abc123")
        guard.start()
        guard.check()  # raises AgentKilled if dashboard sent kill signal

    Args:
        api_key: Dashboard API key (``ag_...`` prefix).
        poll_interval: Seconds between status polls. Default 30.
        dashboard_url: Base URL of the dashboard API.
        budget_guard: Optional BudgetGuard to update with remote limits.
        agent_id: Optional agent identifier. Defaults to a random UUID.
    """

    def __init__(
        self,
        api_key: str,
        poll_interval: float = 30.0,
        dashboard_url: str = "https://app.agentguard47.com",
        budget_guard: Optional["BudgetGuard"] = None,
        agent_id: Optional[str] = None,
    ) -> None:
        import uuid as _uuid

        if not api_key:
            raise ValueError("api_key is required for RemoteGuard")
        if poll_interval <= 0:
            raise ValueError("poll_interval must be > 0")
        parsed = urlparse(dashboard_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"dashboard_url scheme must be http or https, got {parsed.scheme!r}")

        self._api_key = api_key
        self._poll_interval = poll_interval
        self._dashboard_url = dashboard_url.rstrip("/")
        self._budget_guard = budget_guard
        self._agent_id = agent_id or _uuid.uuid4().hex
        self._killed = False
        self._kill_reason: Optional[str] = None
        self._paused = False
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_poll: Optional[float] = None
        self._started = False

    def start(self) -> None:
        """Start the background polling thread. Idempotent."""
        with self._lock:
            if self._started:
                return
            self._started = True
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._poll_loop, daemon=True
            )
            self._thread.start()

    def stop(self) -> None:
        """Stop the background polling thread."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def check(self) -> None:
        """Check if the agent has been killed remotely. Raises AgentKilled."""
        with self._lock:
            if self._killed:
                reason = self._kill_reason or "Agent killed via remote dashboard signal"
                raise AgentKilled(reason)

    def auto_check(self, event_name: str, event_data: Optional[Dict[str, Any]] = None) -> None:
        """Auto-check: delegates to check()."""
        self.check()

    def reset(self) -> None:
        """Reset the kill/pause state."""
        with self._lock:
            self._killed = False
            self._kill_reason = None
            self._paused = False

    @property
    def agent_id(self) -> str:
        """The unique identifier for this agent instance."""
        return self._agent_id

    @property
    def is_killed(self) -> bool:
        """Whether a remote kill signal has been received."""
        with self._lock:
            return self._killed

    @property
    def is_started(self) -> bool:
        """Whether the polling thread is running."""
        with self._lock:
            return self._started

    def _poll_loop(self) -> None:
        """Background loop: poll the dashboard for status updates."""
        while not self._stop.wait(self._poll_interval):
            self._poll_once()

    def _poll_once(self) -> None:
        """Execute a single poll to the dashboard status API."""
        import urllib.request as _urllib_request
        from urllib.error import HTTPError as _HTTPError

        url = f"{self._dashboard_url}/api/v1/status?agent_id={self._agent_id}"
        headers = {"Authorization": f"Bearer {self._api_key}"}

        try:
            req = _urllib_request.Request(url, headers=headers, method="GET")
            with _urllib_request.urlopen(req, timeout=10) as resp:  # nosec B310 — scheme validated in __init__
                data = json.loads(resp.read().decode("utf-8"))
        except (_HTTPError, OSError, json.JSONDecodeError, ValueError):
            # Network failure — fall back gracefully, agent keeps running
            return

        with self._lock:
            self._last_poll = time.monotonic()

            # Handle kill signal
            action = data.get("action")
            if action == "kill":
                self._killed = True
                self._kill_reason = data.get(
                    "reason", "Agent killed via remote dashboard signal"
                )

            # Handle budget update
            budget_update = data.get("budget")
            if budget_update and self._budget_guard is not None:
                bg = self._budget_guard
                with bg._lock:
                    if "max_cost_usd" in budget_update:
                        bg._max_cost_usd = float(budget_update["max_cost_usd"])
                    if "max_tokens" in budget_update:
                        bg._max_tokens = int(budget_update["max_tokens"])
                    if "max_calls" in budget_update:
                        bg._max_calls = int(budget_update["max_calls"])

    def __repr__(self) -> str:
        status = "killed" if self._killed else ("running" if self._started else "idle")
        return (
            f"RemoteGuard(agent_id={self._agent_id!r}, "
            f"poll_interval={self._poll_interval}, status={status})"
        )


def _stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))
