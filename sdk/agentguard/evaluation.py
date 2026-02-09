"""Evaluation as Code — assertion-based trace analysis.

Usage::

    from agentguard import EvalSuite

    result = (
        EvalSuite("traces.jsonl")
        .assert_no_loops()
        .assert_budget_under(tokens=50000)
        .assert_completes_within(30.0)
        .run()
    )
    print(result.summary)
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AssertionResult:
    """Result of a single evaluation assertion."""
    name: str
    passed: bool
    message: str


@dataclass
class EvalResult:
    """Aggregated results from an EvalSuite run.

    Attributes:
        assertions: List of individual assertion results.
    """
    assertions: List[AssertionResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True if all assertions passed."""
        return all(a.passed for a in self.assertions)

    @property
    def summary(self) -> str:
        """Human-readable summary of all assertion results."""
        total = len(self.assertions)
        passed = sum(1 for a in self.assertions if a.passed)
        failed = total - passed
        lines = [f"EvalResult: {passed}/{total} passed, {failed} failed"]
        for a in self.assertions:
            status = "PASS" if a.passed else "FAIL"
            lines.append(f"  [{status}] {a.name}: {a.message}")
        return "\n".join(lines)


class EvalSuite:
    """Load a trace from JSONL and run assertions against it.

    Usage::

        result = (
            EvalSuite("traces.jsonl")
            .assert_no_loops()
            .assert_tool_called("search", min_times=1)
            .assert_budget_under(tokens=50000)
            .run()
        )
        print(result.summary)

    Args:
        path: Path to a JSONL trace file.
    """

    def __init__(self, path: str) -> None:
        self._events = _load_events(path)
        self._assertions: List[_Assertion] = []

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    def assert_no_loops(self) -> "EvalSuite":
        """Assert that no loop guard events were recorded."""
        self._assertions.append(_Assertion(
            name="no_loops",
            check=_check_no_loops,
        ))
        return self

    def assert_tool_called(self, name: str, min_times: int = 1) -> "EvalSuite":
        """Assert a tool was called at least min_times."""
        self._assertions.append(_Assertion(
            name=f"tool_called:{name}>={min_times}",
            check=lambda events, n=name, m=min_times: _check_tool_called(events, n, m),
        ))
        return self

    def assert_budget_under(self, tokens: Optional[int] = None, calls: Optional[int] = None) -> "EvalSuite":
        """Assert total token/call usage is under a limit."""
        label_parts = []
        if tokens is not None:
            label_parts.append(f"tokens<{tokens}")
        if calls is not None:
            label_parts.append(f"calls<{calls}")
        self._assertions.append(_Assertion(
            name=f"budget_under:{','.join(label_parts)}",
            check=lambda events, t=tokens, c=calls: _check_budget_under(events, t, c),
        ))
        return self

    def assert_completes_within(self, seconds: float) -> "EvalSuite":
        """Assert the longest span completed within a time limit."""
        self._assertions.append(_Assertion(
            name=f"completes_within:{seconds}s",
            check=lambda events, s=seconds: _check_completes_within(events, s),
        ))
        return self

    def assert_event_exists(self, name: str) -> "EvalSuite":
        """Assert that at least one event with the given name exists."""
        self._assertions.append(_Assertion(
            name=f"event_exists:{name}",
            check=lambda events, n=name: _check_event_exists(events, n),
        ))
        return self

    def assert_no_errors(self) -> "EvalSuite":
        """Assert no events have error data."""
        self._assertions.append(_Assertion(
            name="no_errors",
            check=_check_no_errors,
        ))
        return self

    def assert_cost_under(self, max_cost_usd: float) -> "EvalSuite":
        """Assert total estimated cost is under a dollar limit."""
        self._assertions.append(_Assertion(
            name=f"cost_under:${max_cost_usd}",
            check=lambda events, m=max_cost_usd: _check_cost_under(events, m),
        ))
        return self

    def assert_no_budget_warnings(self) -> "EvalSuite":
        """Assert no budget warning events were recorded."""
        self._assertions.append(_Assertion(
            name="no_budget_warnings",
            check=_check_no_budget_warnings,
        ))
        return self

    def run(self) -> EvalResult:
        result = EvalResult()
        for assertion in self._assertions:
            ar = assertion.check(self._events)
            result.assertions.append(ar)
        return result


@dataclass
class _Assertion:
    name: str
    check: Any  # Callable[[List[Dict]], AssertionResult]


# --- check functions ---


def _check_no_loops(events: List[Dict[str, Any]]) -> AssertionResult:
    loop_events = [e for e in events if e.get("name") == "guard.loop_detected"]
    if loop_events:
        return AssertionResult(
            name="no_loops",
            passed=False,
            message=f"Found {len(loop_events)} loop detection event(s)",
        )
    return AssertionResult(name="no_loops", passed=True, message="No loops detected")


def _check_tool_called(events: List[Dict[str, Any]], tool_name: str, min_times: int) -> AssertionResult:
    name = f"tool_called:{tool_name}>={min_times}"
    # Count tool.result events or span events with matching tool name
    count = 0
    for e in events:
        ename = e.get("name", "")
        if ename == "tool.result":
            count += 1
        elif ename.startswith(f"tool.{tool_name}"):
            if e.get("phase") == "start" or e.get("kind") == "event":
                count += 1
    if count >= min_times:
        return AssertionResult(name=name, passed=True, message=f"Tool called {count} time(s)")
    return AssertionResult(name=name, passed=False, message=f"Tool called {count} time(s), expected >= {min_times}")


def _check_budget_under(events: List[Dict[str, Any]], max_tokens: Optional[int], max_calls: Optional[int]) -> AssertionResult:
    parts = []
    if max_tokens is not None:
        parts.append(f"tokens<{max_tokens}")
    if max_calls is not None:
        parts.append(f"calls<{max_calls}")
    name = f"budget_under:{','.join(parts)}"

    total_tokens = 0
    total_calls = 0
    for e in events:
        data = e.get("data", {})
        if isinstance(data, dict):
            usage = data.get("token_usage") or data.get("usage") or {}
            if isinstance(usage, dict):
                total_tokens += usage.get("total_tokens", 0)
        if e.get("name", "").startswith("tool.") and e.get("kind") == "span" and e.get("phase") == "start":
            total_calls += 1

    failures = []
    if max_tokens is not None and total_tokens >= max_tokens:
        failures.append(f"tokens={total_tokens} >= {max_tokens}")
    if max_calls is not None and total_calls >= max_calls:
        failures.append(f"calls={total_calls} >= {max_calls}")

    if failures:
        return AssertionResult(name=name, passed=False, message="; ".join(failures))
    return AssertionResult(name=name, passed=True, message=f"tokens={total_tokens}, calls={total_calls}")


def _check_completes_within(events: List[Dict[str, Any]], max_seconds: float) -> AssertionResult:
    name = f"completes_within:{max_seconds}s"
    max_ms = 0.0
    for e in events:
        dur = e.get("duration_ms")
        if isinstance(dur, (int, float)) and dur > max_ms:
            max_ms = dur
    actual_seconds = max_ms / 1000.0
    if actual_seconds <= max_seconds:
        return AssertionResult(name=name, passed=True, message=f"Completed in {actual_seconds:.3f}s")
    return AssertionResult(name=name, passed=False, message=f"Took {actual_seconds:.3f}s, limit is {max_seconds}s")


def _check_event_exists(events: List[Dict[str, Any]], event_name: str) -> AssertionResult:
    name = f"event_exists:{event_name}"
    found = any(e.get("name") == event_name for e in events)
    if found:
        return AssertionResult(name=name, passed=True, message="Event found")
    return AssertionResult(name=name, passed=False, message="Event not found")


def _check_no_errors(events: List[Dict[str, Any]]) -> AssertionResult:
    errors = [e for e in events if e.get("error") is not None]
    if errors:
        return AssertionResult(
            name="no_errors",
            passed=False,
            message=f"Found {len(errors)} event(s) with errors",
        )
    return AssertionResult(name="no_errors", passed=True, message="No errors found")


def _check_cost_under(events: List[Dict[str, Any]], max_cost_usd: float) -> AssertionResult:
    name = f"cost_under:${max_cost_usd}"
    total_cost = 0.0
    for e in events:
        # Check top-level cost_usd
        cost = e.get("cost_usd")
        if isinstance(cost, (int, float)):
            total_cost += cost
        # Check inside data dict
        data = e.get("data", {})
        if isinstance(data, dict):
            data_cost = data.get("cost_usd")
            if isinstance(data_cost, (int, float)):
                total_cost += data_cost
    if total_cost < max_cost_usd:
        return AssertionResult(name=name, passed=True, message=f"Cost ${total_cost:.4f} < ${max_cost_usd:.4f}")
    return AssertionResult(name=name, passed=False, message=f"Cost ${total_cost:.4f} >= ${max_cost_usd:.4f}")


def _check_no_budget_warnings(events: List[Dict[str, Any]]) -> AssertionResult:
    warnings = [e for e in events if e.get("name") == "guard.budget_warning"]
    if warnings:
        return AssertionResult(
            name="no_budget_warnings",
            passed=False,
            message=f"Found {len(warnings)} budget warning(s)",
        )
    return AssertionResult(name="no_budget_warnings", passed=True, message="No budget warnings")


# --- summarize ---


def summarize_trace(
    path_or_events: Any,
) -> Dict[str, Any]:
    """Summarize a trace as a dict with totals and breakdowns.

    Accepts either a file path (str) to a JSONL trace file or a list of
    event dicts.

    Returns a dict with keys:
        total_events, spans, events, cost_usd, duration_ms,
        tool_calls, llm_calls, errors, loop_detections

    Usage::

        from agentguard import summarize_trace

        summary = summarize_trace("traces.jsonl")
        print(f"Cost: ${summary['cost_usd']:.4f}")
        print(f"Duration: {summary['duration_ms']:.1f}ms")
    """
    if isinstance(path_or_events, str):
        events = _load_events(path_or_events)
    elif isinstance(path_or_events, list):
        events = path_or_events
    else:
        raise TypeError(
            f"Expected str (file path) or list of events, got {type(path_or_events).__name__}"
        )

    total = len(events)
    spans = 0
    event_count = 0
    total_cost = 0.0
    max_duration_ms = 0.0
    tool_calls = 0
    llm_calls = 0
    error_count = 0
    loop_detections = 0

    for e in events:
        kind = e.get("kind", "")
        name = e.get("name", "")

        if kind == "span":
            spans += 1
            if e.get("phase") == "end":
                dur = e.get("duration_ms")
                if isinstance(dur, (int, float)) and dur > max_duration_ms:
                    max_duration_ms = float(dur)
        elif kind == "event":
            event_count += 1

        # Cost from top-level or data dict
        cost = e.get("cost_usd")
        if isinstance(cost, (int, float)):
            total_cost += float(cost)
        data = e.get("data", {})
        if isinstance(data, dict):
            dcost = data.get("cost_usd")
            if isinstance(dcost, (int, float)):
                total_cost += float(dcost)

        # Tool calls
        if name.startswith("tool.") and kind == "span" and e.get("phase") == "start":
            tool_calls += 1

        # LLM calls
        if name in ("llm.call", "llm.result") and e.get("phase") == "start":
            llm_calls += 1

        # Errors
        if e.get("error") is not None:
            error_count += 1

        # Loop detections
        if name == "guard.loop_detected":
            loop_detections += 1

    return {
        "total_events": total,
        "spans": spans,
        "events": event_count,
        "cost_usd": total_cost,
        "duration_ms": max_duration_ms,
        "tool_calls": tool_calls,
        "llm_calls": llm_calls,
        "errors": error_count,
        "loop_detections": loop_detections,
    }


# --- loader ---


def _load_events(path: str) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events
