#!/usr/bin/env python3
"""End-to-end verification of the cost guardrail pipeline (T1-T7).

Runs a local simulated agent with:
- Tracer → JsonlFileSink (writes events to JSONL)
- BudgetGuard with warning at 50% and limit
- patch_openai() with budget_guard wired in
- Simulated LLM calls that trigger warning and exceeded events
- Reads back JSONL and verifies the full pipeline

Run: PYTHONPATH=sdk python sdk/tests/e2e_cost_guardrail.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types

# Ensure SDK is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from agentguard import (
    BudgetExceeded,
    BudgetGuard,
    EvalSuite,
    JsonlFileSink,
    Tracer,
    summarize_trace,
)
from agentguard.evaluation import _extract_cost
from agentguard.instrument import (
    _originals,
    patch_openai,
    unpatch_openai,
)

checks_passed = 0
checks_failed = 0


def check(name: str, condition: bool, detail: str = ""):
    global checks_passed, checks_failed
    if condition:
        checks_passed += 1
        print(f"  [PASS] {name}")
    else:
        checks_failed += 1
        print(f"  [FAIL] {name}: {detail}")


def make_mock_openai(prompt_tokens=100, completion_tokens=50, total_tokens=150):
    """Create a mock openai module."""
    usage = types.SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
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
    global checks_passed, checks_failed

    print("\n=== E2E Cost Guardrail Pipeline Verification ===\n")

    # ---- Setup ----
    tmpfile = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    trace_path = tmpfile.name
    tmpfile.close()

    warnings_received = []

    try:
        # ---- Phase 1: Under-budget calls with warning ----
        print("Phase 1: Under-budget calls + warning threshold")

        sink = JsonlFileSink(trace_path)
        guard = BudgetGuard(
            max_cost_usd=0.05,
            warn_at_pct=0.3,
            on_warning=lambda msg: warnings_received.append(msg),
        )
        tracer = Tracer(sink=sink, service="e2e-cost-test", guards=[guard])

        # Use enough tokens so cost (~$0.0075/call) crosses 30% of $0.05 = $0.015 after 2 calls
        mod, cls = make_mock_openai(1000, 500, 1500)
        sys.modules["openai"] = mod
        _originals.clear()
        patch_openai(tracer, budget_guard=guard)

        # Make a few calls — should cross 30% warning threshold
        client = cls()
        for i in range(3):
            client.chat.completions.create(model="gpt-4o")

        check("Guard tracked tokens", guard.state.tokens_used == 4500, f"got {guard.state.tokens_used}")
        check("Guard tracked calls", guard.state.calls_used == 3, f"got {guard.state.calls_used}")
        check("Guard tracked cost", guard.state.cost_used > 0, f"got {guard.state.cost_used}")
        check("Warning callback fired", len(warnings_received) > 0, f"got {len(warnings_received)} warnings")

        unpatch_openai()
        del sys.modules["openai"]

        # ---- Phase 2: Over-budget call ----
        print("\nPhase 2: Over-budget call → BudgetExceeded")

        guard2 = BudgetGuard(max_cost_usd=0.0001)
        tracer2 = Tracer(sink=sink, service="e2e-cost-test", guards=[guard2])

        mod2, cls2 = make_mock_openai(100000, 50000, 150000)
        sys.modules["openai"] = mod2
        _originals.clear()
        patch_openai(tracer2, budget_guard=guard2)

        exceeded = False
        try:
            client2 = cls2()
            client2.chat.completions.create(model="gpt-4o")
        except BudgetExceeded:
            exceeded = True

        check("BudgetExceeded raised", exceeded)

        unpatch_openai()
        del sys.modules["openai"]
        _originals.clear()

        # ---- Phase 3: Read back JSONL and verify ----
        print("\nPhase 3: Verify JSONL output")

        events = []
        with open(trace_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))

        check("Events written to JSONL", len(events) > 0, f"got {len(events)}")

        # Check event types present
        names = [e.get("name", "") for e in events]
        check("llm.result events present", "llm.result" in names)
        check("guard.budget_exceeded event present", "guard.budget_exceeded" in names)

        # Check cost at top level (T7)
        llm_events = [e for e in events if e.get("name") == "llm.result"]
        has_top_level_cost = any("cost_usd" in e for e in llm_events)
        check("cost_usd at top level in llm.result", has_top_level_cost)

        has_data_cost = any("cost_usd" in e.get("data", {}) for e in llm_events)
        check("cost_usd NOT in data dict", not has_data_cost)

        # Check exceeded event data
        exceeded_events = [e for e in events if e.get("name") == "guard.budget_exceeded"]
        if exceeded_events:
            exc_data = exceeded_events[0].get("data", {})
            check("exceeded event has message", "message" in exc_data)
            check("exceeded event has model", "model" in exc_data)
            check("exceeded event has cost_usd", "cost_usd" in exc_data)

        # Check warning events
        warning_events = [e for e in events if e.get("name") == "guard.budget_warning"]
        check("guard.budget_warning event(s) present", len(warning_events) > 0, f"got {len(warning_events)}")

        # ---- Phase 4: _extract_cost no double counting ----
        print("\nPhase 4: _extract_cost verification")

        total_cost = 0.0
        for e in events:
            cost = _extract_cost(e)
            if cost is not None:
                total_cost += cost

        # Compare with summarize_trace
        summary = summarize_trace(events)
        check("summarize_trace matches manual sum", abs(summary["cost_usd"] - total_cost) < 0.0001,
              f"summary={summary['cost_usd']}, manual={total_cost}")

        # ---- Phase 5: EvalSuite on the trace ----
        print("\nPhase 5: EvalSuite assertions")

        result = (
            EvalSuite(trace_path)
            .assert_event_exists("llm.result")
            .assert_event_exists("guard.budget_exceeded")
            .run()
        )
        check("EvalSuite all assertions pass", result.passed, result.summary)

        # ---- Phase 6: Sampling rate validation ----
        print("\nPhase 6: Sampling rate validation")

        try:
            Tracer(sampling_rate=-0.5)
            check("Negative sampling_rate rejected", False, "no exception raised")
        except ValueError:
            check("Negative sampling_rate rejected", True)

        try:
            Tracer(sampling_rate=2.0)
            check("Above-1.0 sampling_rate rejected", False, "no exception raised")
        except ValueError:
            check("Above-1.0 sampling_rate rejected", True)

        # ---- Phase 7: Guards fire when sampled out ----
        print("\nPhase 7: Guards fire when sampled out")

        from agentguard.guards import LoopGuard

        loop_guard = LoopGuard(max_repeats=2)
        sampled_out_tracer = Tracer(sampling_rate=0.0, guards=[loop_guard])

        loop_detected = False
        try:
            with sampled_out_tracer.trace("test") as ctx:
                ctx.event("tool.search", data={"query": "same"})
                ctx.event("tool.search", data={"query": "same"})
        except Exception:
            loop_detected = True

        check("LoopGuard fires even when sampled out", loop_detected)

    finally:
        os.unlink(trace_path)

    # ---- Summary ----
    print(f"\n{'='*50}")
    total = checks_passed + checks_failed
    print(f"RESULTS: {checks_passed}/{total} passed, {checks_failed} failed")
    if checks_failed > 0:
        print("SOME CHECKS FAILED!")
        sys.exit(1)
    else:
        print("ALL CHECKS PASSED!")


if __name__ == "__main__":
    main()
