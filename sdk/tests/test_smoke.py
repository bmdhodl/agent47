#!/usr/bin/env python3
"""Smoke test: exercises the AgentGuard happy path.

Standalone:
    PYTHONPATH=sdk python sdk/tests/test_smoke.py

With pytest:
    PYTHONPATH=sdk python -m pytest sdk/tests/test_smoke.py -v
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time


def smoke_test() -> bool:
    """Run 9 smoke checks. Returns True on success."""
    start = time.perf_counter()
    errors = []

    # --- 1. Import all public exports ---
    try:
        from agentguard import (
            Tracer, JsonlFileSink, StdoutSink, TraceSink,
            LoopGuard, FuzzyLoopGuard, BudgetGuard, TimeoutGuard, RateLimitGuard,
            LoopDetected, BudgetExceeded, BudgetWarning, TimeoutExceeded,
            estimate_cost,
            HttpSink,
            EvalSuite, EvalResult, AssertionResult,
            AsyncTracer, AsyncTraceContext,
            trace_agent, trace_tool,
            patch_openai, patch_anthropic,
            unpatch_openai, unpatch_anthropic,
            async_trace_agent, async_trace_tool,
            patch_openai_async, patch_anthropic_async,
            unpatch_openai_async, unpatch_anthropic_async,
        )
        print("[PASS] 1/9   All imports successful")
    except ImportError as e:
        print(f"[FAIL] 1/9   Import failed: {e}")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        trace_path = os.path.join(tmpdir, "smoke.jsonl")

        # --- 2. Create tracer with guards + metadata + sampling ---
        try:
            tracer = Tracer(
                sink=JsonlFileSink(trace_path),
                service="smoke-test",
                guards=[LoopGuard(max_repeats=3)],
                metadata={"test": "smoke"},
                sampling_rate=1.0,
            )
            print("[PASS] 2/9   Tracer created with guards, metadata, sampling")
        except Exception as e:
            errors.append(f"Tracer creation: {e}")
            print(f"[FAIL] 2/9   Tracer creation: {e}")
            return False

        # --- 3. Run traced agent ---
        try:
            with tracer.trace("agent.smoke", data={"task": "test"}) as ctx:
                ctx.event("reasoning.step", data={"thought": "planning"})
                with ctx.span("tool.search") as tool_ctx:
                    tool_ctx.event("tool.result", data={"result": "found"})
                cost = estimate_cost("gpt-4o", input_tokens=100, output_tokens=50)
                ctx.cost.add("gpt-4o", input_tokens=100, output_tokens=50)
                ctx.event("llm.result", data={"model": "gpt-4o", "cost_usd": cost})
            print("[PASS] 3/9   Traced agent run completed")
        except Exception as e:
            errors.append(f"Agent run: {e}")
            print(f"[FAIL] 3/9   Agent run: {e}")
            return False

        # --- 4. Verify JSONL output ---
        try:
            with open(trace_path) as f:
                events = [json.loads(line) for line in f if line.strip()]
            assert len(events) >= 6, f"got {len(events)}"
            assert all(e.get("service") == "smoke-test" for e in events)
            trace_events = [e for e in events if e.get("kind") != "meta"]
            assert all("metadata" in e for e in trace_events)
            # Verify watermark event exists
            watermarks = [e for e in events if e.get("name") == "watermark"]
            assert len(watermarks) == 1, f"expected 1 watermark, got {len(watermarks)}"
            print(f"[PASS] 4/9   {len(events)} events in JSONL, all valid")
        except Exception as e:
            errors.append(f"JSONL verify: {e}")
            print(f"[FAIL] 4/9   JSONL verify: {e}")

        # --- 5. EvalSuite ---
        try:
            eval_result = (
                EvalSuite(trace_path)
                .assert_no_loops()
                .assert_no_errors()
                .assert_event_exists("reasoning.step")
                .assert_completes_within(10.0)
                .run()
            )
            assert eval_result.passed, eval_result.summary
            print("[PASS] 5/9   EvalSuite assertions passed")
        except Exception as e:
            errors.append(f"EvalSuite: {e}")
            print(f"[FAIL] 5/9   EvalSuite: {e}")

        # --- 6. All 5 guard types ---
        try:
            # LoopGuard
            g = LoopGuard(max_repeats=2, window=4)
            g.check("tool_a", {"x": 1})
            caught = False
            try:
                g.check("tool_a", {"x": 1})
            except LoopDetected:
                caught = True
            assert caught, "LoopGuard didn't fire"

            # BudgetGuard
            b = BudgetGuard(max_cost_usd=0.01)
            b.consume(cost_usd=0.005)
            caught = False
            try:
                b.consume(cost_usd=0.01)
            except BudgetExceeded:
                caught = True
            assert caught, "BudgetGuard didn't fire"

            # TimeoutGuard
            t = TimeoutGuard(max_seconds=100)
            t.start()
            t.check()

            # RateLimitGuard
            r = RateLimitGuard(max_calls_per_minute=1000)
            r.check()

            # FuzzyLoopGuard
            fz = FuzzyLoopGuard(max_tool_repeats=3, max_alternations=2, window=6)
            fz.check("tool_a", {})
            fz.check("tool_a", {"different": True})
            caught = False
            try:
                fz.check("tool_a", {"yet_another": True})
            except LoopDetected:
                caught = True
            assert caught, "FuzzyLoopGuard didn't fire"

            print("[PASS] 6/9   All 5 guard types fire correctly")
        except Exception as e:
            errors.append(f"Guards: {e}")
            print(f"[FAIL] 6/9   Guards: {e}")

        # --- 7. Cost estimation ---
        try:
            c = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
            assert c > 0
            print(f"[PASS] 7/9   Cost estimate: gpt-4o 1K/500 = ${c:.4f}")
        except Exception as e:
            errors.append(f"Cost: {e}")
            print(f"[FAIL] 7/9   Cost: {e}")

        # --- 8. Export ---
        try:
            from agentguard.export import export_json, export_csv
            json_out = os.path.join(tmpdir, "smoke.json")
            csv_out = os.path.join(tmpdir, "smoke.csv")
            export_json(trace_path, json_out)
            export_csv(trace_path, csv_out)
            assert os.path.getsize(json_out) > 0
            assert os.path.getsize(csv_out) > 0
            print("[PASS] 8/9   Export to JSON + CSV works")
        except Exception as e:
            errors.append(f"Export: {e}")
            print(f"[FAIL] 8/9   Export: {e}")

        # --- 9. CLI report ---
        try:
            import io
            from agentguard.cli import _report
            buf = io.StringIO()
            old = sys.stdout
            sys.stdout = buf
            try:
                _report(trace_path)
            finally:
                sys.stdout = old
            assert "AgentGuard report" in buf.getvalue()
            print("[PASS] 9/9   CLI report works")
        except Exception as e:
            errors.append(f"CLI: {e}")
            print(f"[FAIL] 9/9   CLI: {e}")

    elapsed = time.perf_counter() - start
    print(f"\n{'='*50}")
    if errors:
        print(f"SMOKE TEST FAILED ({len(errors)} errors) in {elapsed:.2f}s")
        for e in errors:
            print(f"  - {e}")
        return False
    print(f"SMOKE TEST PASSED in {elapsed:.2f}s")
    return True


# --- pytest compatibility ---
def test_smoke():
    """Pytest wrapper."""
    assert smoke_test(), "Smoke test failed"


if __name__ == "__main__":
    ok = smoke_test()
    sys.exit(0 if ok else 1)
