"""Offline behavior checks for #866; no provider or subscription calls."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SDK = Path(__file__).resolve().parents[1]


def _run_script(tmp_path, source):
    script = tmp_path / "worker.py"
    script.write_text(source, encoding="utf-8")
    # Never inherit a remote sink, credentials, or a caller's budget settings.
    env = {key: value for key, value in os.environ.items()
           if not key.upper().startswith("AGENTGUARD_")}
    env["PYTHONPATH"] = str(SDK)
    result = subprocess.run(
        [sys.executable, "-m", "agentguard", "run", "--profile", "coding-agent",
         "--budget-usd", "0.01", "--trace-file", "trace.jsonl", str(script)],
        cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8",
        timeout=15, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    trace = tmp_path / "trace.jsonl"
    events = ([json.loads(line) for line in trace.read_text(encoding="utf-8").splitlines()]
              if trace.exists() else [])
    return result, events


def test_run_does_not_count_uninstrumented_work(tmp_path):
    result, events = _run_script(tmp_path, """
import agentguard
for attempt in range(8):
    print('mock_dispatch', attempt)
guard = agentguard.get_budget_guard()
print('recorded_calls', guard.state.calls_used)
"""
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("mock_dispatch") == 8
    assert "recorded_calls 0" in result.stdout
    assert not any(event.get("error") for event in events)


def test_run_stops_repeated_traced_work_before_dispatch(tmp_path):
    result, events = _run_script(tmp_path, """
import agentguard
with agentguard.get_tracer().trace('worker') as span:
    for attempt in range(8):
        span.event('tool.search', data={'query': 'same'})
        print('mock_dispatch', attempt)
"""
    )
    assert result.returncode == 1, result.stderr
    assert result.stdout.count("mock_dispatch") == 2
    assert "stopped the run" in result.stderr
    assert any((event.get("error") or {}).get("type") == "LoopDetected" for event in events)


@pytest.mark.parametrize("event_name, expected_dispatches", [("tool.retry", 2), ("tool.error", 3)])
def test_retry_stop_depends_on_where_the_event_is_emitted(tmp_path, event_name, expected_dispatches):
    # A pre-dispatch retry event can refuse work; a post-error event cannot undo it.
    result, events = _run_script(tmp_path, f"""
import agentguard
with agentguard.get_tracer().trace('worker') as span:
    for attempt in range(8):
        if {event_name!r} == 'tool.error':
            print('mock_dispatch', attempt)
        span.event({event_name!r}, data={{'tool_name': 'search', 'attempt': attempt}})
        if {event_name!r} == 'tool.retry':
            print('mock_dispatch', attempt)
"""
    )
    assert result.returncode == 1, result.stderr
    assert result.stdout.count("mock_dispatch") == expected_dispatches
    assert "Retry limit exceeded" in result.stderr
    assert any((event.get("error") or {}).get("type") == "RetryLimitExceeded" for event in events)


def test_timeout_allows_work_to_finish_then_refuses_at_next_check(tmp_path):
    result, _ = _run_script(tmp_path, """
import threading
from agentguard import TimeoutGuard
guard = TimeoutGuard(max_seconds=0.001)
guard.start()
threading.Event().wait(0.02)  # Bounded blocking work, with no guard check inside it.
print('work_completed')
guard.check()
print('next_dispatch')
"""
    )
    assert result.returncode == 1, result.stderr
    assert "work_completed" in result.stdout
    assert "next_dispatch" not in result.stdout
    assert "timeout" in result.stderr


def test_timeout_context_checks_after_the_body_not_during_it(tmp_path):
    result, _ = _run_script(tmp_path, """
import threading
from agentguard import TimeoutGuard
with TimeoutGuard(max_seconds=0.001):
    threading.Event().wait(0.02)
    print('work_completed')
print('next_dispatch')
"""
    )
    assert result.returncode == 1, result.stderr
    assert "work_completed" in result.stdout
    assert "next_dispatch" not in result.stdout
    assert "timeout" in result.stderr
