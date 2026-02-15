"""End-to-end pipeline test: agent → tracer → guards → sinks → ingest → verify.

Exercises every SDK feature in a single pipeline, then verifies the output
at every layer: local JSONL file, remote ingest server, EvalSuite, CLI,
export.
"""
from __future__ import annotations

import io
import json
import os
import tempfile
import threading
import time

import pytest

from agentguard import (
    Tracer,
    JsonlFileSink,
    TraceSink,
    LoopGuard,
    FuzzyLoopGuard,
    BudgetGuard,
    TimeoutGuard,
    RateLimitGuard,
    LoopDetected,
    BudgetExceeded,
    EvalSuite,
    estimate_cost,
)
from agentguard.sinks.http import HttpSink
from agentguard.evaluation import _load_events
from agentguard.export import export_json, export_csv, export_jsonl

from conftest import IngestHandler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _MultiplexSink(TraceSink):
    """Emit to multiple sinks simultaneously (same events, same trace_ids)."""

    def __init__(self, *sinks: TraceSink) -> None:
        self._sinks = sinks

    def emit(self, event):
        for s in self._sinks:
            s.emit(event)


# ---------------------------------------------------------------------------
# Full Pipeline Test
# ---------------------------------------------------------------------------

class TestE2EPipeline:

    def test_full_pipeline(self, ingest_url, tmp_path):
        """Run the complete SDK pipeline and verify at every layer."""
        trace_path = str(tmp_path / "e2e_traces.jsonl")

        # --- Setup sinks ---
        file_sink = JsonlFileSink(trace_path)
        http_sink = HttpSink(
            url=ingest_url,
            api_key="ag_test_key_e2e",
            batch_size=5,
            flush_interval=0.3,
            compress=True,
            _allow_private=True,
        )
        sink = _MultiplexSink(file_sink, http_sink)

        # --- Setup guards ---
        warnings = []
        loop_guard = LoopGuard(max_repeats=3, window=6)
        fuzzy_guard = FuzzyLoopGuard(max_tool_repeats=4, max_alternations=3, window=10)
        budget_guard = BudgetGuard(
            max_cost_usd=1.00,
            max_calls=20,
            warn_at_pct=0.7,
            on_warning=warnings.append,
        )
        timeout_guard = TimeoutGuard(max_seconds=25)
        rate_guard = RateLimitGuard(max_calls_per_minute=1000)

        # --- Setup tracer ---
        tracer = Tracer(
            sink=sink,
            service="e2e-test",
            guards=[loop_guard, fuzzy_guard],
            metadata={"env": "test", "version": "1.0.0"},
            sampling_rate=1.0,
        )

        # --- Run agent simulation ---
        timeout_guard.start()
        root_cost_tracker = None

        with tracer.trace("agent.e2e_run", data={"task": "fibonacci"}) as root:
            # Step 1: Reasoning
            root.event("reasoning.step", data={"thought": "analyze task"})
            root.event("reasoning.step", data={"thought": "plan approach"})

            # Step 2: Tool calls with child spans
            with root.span("tool.search") as tool_span:
                tool_span.event("tool.result", data={"result": "fibonacci definition"})

            with root.span("tool.search") as tool_span:
                tool_span.event("tool.result", data={"result": "fib algorithm"})

            with root.span("tool.calculate") as tool_span:
                tool_span.event("tool.result", data={"result": "55"})

            # Step 3: LLM call with cost
            cost1 = estimate_cost("gpt-4o", input_tokens=500, output_tokens=200)
            root.cost.add("gpt-4o", input_tokens=500, output_tokens=200)
            budget_guard.consume(tokens=700, calls=1, cost_usd=cost1)
            root.event("llm.result", data={
                "model": "gpt-4o",
                "cost_usd": cost1,
                "usage": {"prompt_tokens": 500, "completion_tokens": 200},
            })

            # Step 4: Trigger LoopGuard
            loop_caught = False
            for i in range(4):
                try:
                    loop_guard.check("search", {"query": "same"})
                except LoopDetected:
                    root.event("guard.loop_detected", data={"iteration": i})
                    loop_caught = True
                    loop_guard.reset()
                    break
            assert loop_caught, "LoopGuard should have fired"

            # Step 5: Push budget past 70% → warning
            budget_guard.consume(tokens=1000, calls=5, cost_usd=0.75)

            # Step 6: Timeout + rate limit (should pass)
            timeout_guard.check()
            rate_guard.check()

            # Step 7: Second LLM call (Anthropic)
            cost2 = estimate_cost("claude-3-5-sonnet-20241022", input_tokens=300, output_tokens=150)
            root.cost.add("claude-3-5-sonnet-20241022", input_tokens=300, output_tokens=150)
            budget_guard.consume(tokens=450, calls=1, cost_usd=cost2)
            root.event("llm.result", data={
                "model": "claude-3-5-sonnet-20241022",
                "cost_usd": cost2,
            })

            root.event("agent.complete", data={"total_cost": root.cost.total})
            root_cost_tracker = root.cost

        # --- Flush ---
        http_sink.shutdown()
        time.sleep(0.5)

        # =====================================================================
        # Phase D: Assertions on local JSONL
        # =====================================================================
        events = _load_events(trace_path)

        # D1: Enough events
        assert len(events) >= 15, f"Expected >=15 events, got {len(events)}"

        # D2: Required fields
        for e in events:
            assert e.get("service") == "e2e-test"
            assert e.get("kind") in ("span", "event")
            assert e.get("phase") in ("start", "end", "emit")
            assert "trace_id" in e
            assert "span_id" in e
            assert "name" in e
            assert isinstance(e.get("ts"), (int, float))

        # D3: Metadata on every event
        for e in events:
            assert e.get("metadata", {}).get("env") == "test"
            assert e.get("metadata", {}).get("version") == "1.0.0"

        # D4: cost_usd in LLM events
        llm_events = [e for e in events if e["name"] == "llm.result"]
        assert len(llm_events) >= 2
        for le in llm_events:
            assert le.get("data", {}).get("cost_usd", 0) > 0

        # D5: Loop detection event
        loop_events = [e for e in events if e["name"] == "guard.loop_detected"]
        assert len(loop_events) >= 1

        # D6: Span durations
        end_spans = [e for e in events if e["kind"] == "span" and e["phase"] == "end"]
        assert len(end_spans) >= 1
        for es in end_spans:
            assert es.get("duration_ms") is not None
            assert es["duration_ms"] >= 0

        # D7: Tool results
        tool_events = [e for e in events if e["name"] == "tool.result"]
        assert len(tool_events) >= 3

        # D8: Single trace_id
        trace_ids = set(e["trace_id"] for e in events)
        assert len(trace_ids) == 1

        # D9: Budget warning fired
        assert len(warnings) >= 1

        # =====================================================================
        # Phase E: Assertions on ingest server
        # =====================================================================
        server_events = IngestHandler.events
        assert len(server_events) >= 15, f"Server got {len(server_events)} events"

        # E1: All valid (server accepted them)
        for e in server_events:
            assert e["kind"] in ("span", "event")

        # E2: Idempotency keys unique
        keys = IngestHandler.idempotency_keys
        assert len(keys) >= 1
        assert len(keys) == len(set(keys))

        # E3: Metadata in server events
        for e in server_events:
            assert e.get("metadata", {}).get("env") == "test"

        # =====================================================================
        # Phase F: EvalSuite
        # =====================================================================
        eval_result = (
            EvalSuite(trace_path)
            .assert_no_errors()
            .assert_event_exists("reasoning.step")
            .assert_event_exists("llm.result")
            .assert_event_exists("agent.complete")
            .assert_completes_within(25.0)
            .assert_cost_under(max_cost_usd=1.00)
            .run()
        )
        assert eval_result.passed, f"EvalSuite failed:\n{eval_result.summary}"

        # =====================================================================
        # Phase G: CLI commands
        # =====================================================================
        from agentguard.cli import _report, _summarize

        buf = io.StringIO()
        import sys
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            _report(trace_path)
        finally:
            sys.stdout = old_stdout
        report_out = buf.getvalue()
        assert "AgentGuard report" in report_out
        assert "Estimated cost:" in report_out

        buf = io.StringIO()
        sys.stdout = buf
        try:
            _summarize(trace_path)
        finally:
            sys.stdout = old_stdout
        summarize_out = buf.getvalue()
        assert "events:" in summarize_out

        # =====================================================================
        # Phase H: Export
        # =====================================================================
        json_path = str(tmp_path / "export.json")
        csv_path = str(tmp_path / "export.csv")
        jsonl_path = str(tmp_path / "export.jsonl")

        count_json = export_json(trace_path, json_path)
        assert count_json >= 15
        with open(json_path) as f:
            exported = json.load(f)
        assert len(exported) == count_json

        count_csv = export_csv(trace_path, csv_path)
        assert count_csv >= 15

        count_jsonl = export_jsonl(trace_path, jsonl_path)
        assert count_jsonl >= 15

        # =====================================================================
        # Phase I: CostTracker
        # =====================================================================
        assert root_cost_tracker.total > 0
        cost_dict = root_cost_tracker.to_dict()
        assert cost_dict["call_count"] == 2
        assert cost_dict["total_cost_usd"] > 0
        assert len(cost_dict["calls"]) == 2


# ---------------------------------------------------------------------------
# Targeted sub-tests
# ---------------------------------------------------------------------------

class TestSamplingIsolation:

    def test_sampling_zero_no_http_events(self, ingest_url):
        """sampling_rate=0.0 should send zero events to the ingest server."""
        sink = HttpSink(
            url=ingest_url,
            api_key="ag_test_key_e2e",
            batch_size=1,
            flush_interval=0.1,
            _allow_private=True,
        )
        tracer = Tracer(sink=sink, service="sample-zero", sampling_rate=0.0)
        with tracer.trace("should.not.appear") as ctx:
            ctx.event("invisible")
        sink.shutdown()
        time.sleep(0.3)
        assert IngestHandler.event_count() == 0


class TestAuthFailure:

    def test_wrong_api_key_rejected(self, ingest_server):
        """Wrong API key → 401 → no events stored."""
        host, port = ingest_server
        IngestHandler.reset()
        sink = HttpSink(
            url=f"http://{host}:{port}/api/ingest",
            api_key="wrong_key",
            batch_size=1,
            flush_interval=0.1,
            _allow_private=True,
        )
        tracer = Tracer(sink=sink, service="auth-fail")
        with tracer.trace("auth.fail"):
            pass
        sink.shutdown()
        time.sleep(0.3)
        assert IngestHandler.event_count() == 0


class TestConcurrentTraces:

    def test_concurrent_jsonl_writes(self, tmp_path):
        """Multiple threads tracing to same Tracer/JsonlFileSink → all events valid."""
        path = str(tmp_path / "concurrent.jsonl")
        sink = JsonlFileSink(path)
        tracer = Tracer(sink=sink, service="concurrent-test")

        def write_trace(n):
            with tracer.trace(f"thread.{n}") as ctx:
                for i in range(10):
                    ctx.event(f"step.{i}", data={"thread": n, "step": i})

        threads = [threading.Thread(target=write_trace, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        events = _load_events(path)
        # 5 threads x (1 span start + 10 events + 1 span end) = 60
        assert len(events) == 60
        for e in events:
            assert e.get("service") == "concurrent-test"
