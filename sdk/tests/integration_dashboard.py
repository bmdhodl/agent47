#!/usr/bin/env python3
"""Integration test: cost guardrail pipeline → real dashboard.

Standalone script (not pytest) for manual pre-release validation.
Exercises: BudgetGuard → patch_openai → HttpSink → real dashboard → query traces.

Required env vars:
  AGENTGUARD_API_KEY    — dashboard API key (ag_...)

Optional env vars:
  AGENTGUARD_DASHBOARD_URL  — dashboard URL (default: https://app.agentguard47.com)
  OPENAI_API_KEY            — if set, uses real OpenAI; otherwise mock

Run: AGENTGUARD_API_KEY=ag_... python3 sdk/tests/integration_dashboard.py
"""
from __future__ import annotations

import json
import os
import ssl
import sys
import time
import types
import urllib.request

# Ensure SDK is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agentguard import (
    BudgetExceeded,
    BudgetGuard,
    Tracer,
)
from agentguard.instrument import (
    _originals,
    patch_openai,
    unpatch_openai,
)
from agentguard.sinks.http import HttpSink

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = ""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name}: {detail}")


def make_mock_openai():
    """Create a mock openai module."""
    usage = types.SimpleNamespace(prompt_tokens=1000, completion_tokens=500, total_tokens=1500)
    result = types.SimpleNamespace(usage=usage)

    class MockCompletions:
        def create(self, *args, **kwargs):
            return result

    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()

    class MockOpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = MockChat()

    mod = types.ModuleType("openai")
    mod.OpenAI = MockOpenAI
    return mod, MockOpenAI


def main():
    global passed, failed

    api_key = os.environ.get("AGENTGUARD_API_KEY")
    if not api_key:
        print("ERROR: AGENTGUARD_API_KEY env var required")
        sys.exit(1)

    base_url = os.environ.get("AGENTGUARD_DASHBOARD_URL", "https://app.agentguard47.com")
    ingest_url = f"{base_url}/api/ingest"
    use_real_openai = bool(os.environ.get("OPENAI_API_KEY"))

    print(f"\n=== Dashboard Integration Test ===")
    print(f"  Dashboard: {base_url}")
    print(f"  OpenAI:    {'real' if use_real_openai else 'mock'}")
    print()

    # --- Setup ---
    warnings = []
    guard = BudgetGuard(max_cost_usd=0.05, warn_at_pct=0.3, on_warning=warnings.append)
    http_sink = HttpSink(url=ingest_url, api_key=api_key, batch_size=5, flush_interval=0.5)
    tracer = Tracer(sink=http_sink, service="integration-dashboard-test", guards=[guard])

    # --- OpenAI setup ---
    if use_real_openai:
        import openai as real_openai
        patch_openai(tracer, budget_guard=guard)
        client = real_openai.OpenAI()
    else:
        mod, cls = make_mock_openai()
        sys.modules["openai"] = mod
        _originals.clear()
        patch_openai(tracer, budget_guard=guard)
        client = cls()

    # --- Run agent loop ---
    print("Phase 1: Running agent loop until BudgetExceeded...")
    exceeded = False
    calls = 0
    try:
        for _ in range(50):
            client.chat.completions.create(model="gpt-4o")
            calls += 1
    except BudgetExceeded:
        exceeded = True
    finally:
        unpatch_openai()
        if not use_real_openai:
            del sys.modules["openai"]
            _originals.clear()

    check("BudgetExceeded raised", exceeded)
    check("At least 1 call succeeded", calls > 0, f"got {calls}")
    check("Budget warning fired", len(warnings) > 0, f"got {len(warnings)}")

    # --- Flush ---
    print("\nPhase 2: Flushing events to dashboard...")
    http_sink.shutdown()
    time.sleep(2)  # extra wait for network

    # --- Query dashboard ---
    print("\nPhase 3: Querying dashboard /api/v1/traces...")
    ctx = ssl.create_default_context()
    req = urllib.request.Request(
        f"{base_url}/api/v1/traces",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, context=ctx) as resp:
            body = json.loads(resp.read().decode())
        traces = body.get("traces", body.get("data", []))
        check("Traces endpoint reachable", True)
        check("At least 1 trace returned", len(traces) > 0, f"got {len(traces)}")

        if traces:
            latest = traces[0]
            cost = latest.get("total_cost", latest.get("cost_usd", 0))
            event_count = latest.get("event_count", latest.get("events", 0))
            check("total_cost > 0", cost > 0, f"got {cost}")
            check("event_count > 0", event_count > 0, f"got {event_count}")
    except urllib.error.HTTPError as e:
        check("Traces endpoint reachable", False, f"HTTP {e.code}: {e.reason}")
    except Exception as e:
        check("Traces endpoint reachable", False, str(e))

    # --- Summary ---
    print(f"\n{'=' * 50}")
    total = passed + failed
    print(f"RESULTS: {passed}/{total} passed, {failed} failed")
    if failed > 0:
        print("SOME CHECKS FAILED!")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED!")


if __name__ == "__main__":
    main()
