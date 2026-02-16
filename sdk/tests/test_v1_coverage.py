"""Additional tests for v1.0 coverage: sinks, CLI, security."""
import io
import json
import os
import tempfile
import unittest
from unittest.mock import patch

from agentguard.tracing import StdoutSink, JsonlFileSink, Tracer
from agentguard.sinks.http import HttpSink
from agentguard.cli import _summarize, _report, _eval


class TestStdoutSink(unittest.TestCase):
    def test_emit_prints_json(self):
        sink = StdoutSink()
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            sink.emit({"name": "test", "kind": "event"})
        output = captured.getvalue().strip()
        parsed = json.loads(output)
        self.assertEqual(parsed["name"], "test")

    def test_repr(self):
        self.assertEqual(repr(StdoutSink()), "StdoutSink()")


class TestJsonlFileSinkEdgeCases(unittest.TestCase):
    def test_concurrent_writes(self):
        """Multiple threads writing to the same sink should not corrupt data."""
        import threading
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        sink = JsonlFileSink(path)

        def write_events(n):
            for i in range(50):
                sink.emit({"thread": n, "i": i})

        threads = [threading.Thread(target=write_events, args=(t,)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        with open(path) as f:
            lines = [line.strip() for line in f if line.strip()]
        self.assertEqual(len(lines), 200)  # 4 threads * 50 events
        # Verify all lines are valid JSON
        for line in lines:
            json.loads(line)
        os.unlink(path)


class TestCliSubcommands(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            f.write(json.dumps({
                "name": "agent.run", "kind": "span", "phase": "start",
                "ts": 1000.0, "data": {},
            }) + "\n")
            f.write(json.dumps({
                "name": "reasoning.step", "kind": "event", "phase": "emit",
                "ts": 1000.001, "data": {"step": 1},
            }) + "\n")
            f.write(json.dumps({
                "name": "agent.run", "kind": "span", "phase": "end",
                "ts": 1000.05, "duration_ms": 50, "data": {}, "error": None,
            }) + "\n")

    def tearDown(self):
        os.unlink(self.path)

    def test_summarize(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            _summarize(self.path)
        output = captured.getvalue()
        self.assertIn("events: 3", output)

    def test_report(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            _report(self.path)
        output = captured.getvalue()
        self.assertIn("Total events: 3", output)
        self.assertIn("Reasoning steps: 1", output)

    def test_eval_passes(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            _eval(self.path)
        output = captured.getvalue()
        self.assertIn("PASS", output)

    def test_eval_ci_passes(self):
        captured = io.StringIO()
        with patch("sys.stdout", captured):
            _eval(self.path, ci=True)
        output = captured.getvalue()
        self.assertIn("PASS", output)


class TestHttpSinkUrlValidation(unittest.TestCase):
    def test_rejects_key_in_query_string(self):
        with self.assertRaises(ValueError) as ctx:
            HttpSink(url="https://example.com/ingest?api_key=secret123")
        self.assertIn("credentials", str(ctx.exception))

    def test_rejects_token_in_query_string(self):
        with self.assertRaises(ValueError):
            HttpSink(url="https://example.com/ingest?token=secret")

    def test_allows_clean_url(self):
        sink = HttpSink(
            url="https://example.com/ingest?format=jsonl",
            batch_size=100,
            flush_interval=60,
        )
        sink.shutdown()

    def test_allows_url_with_non_secret_params(self):
        sink = HttpSink(
            url="https://example.com/ingest?version=2&format=ndjson",
            batch_size=100,
            flush_interval=60,
        )
        sink.shutdown()


class TestTracerGuardsWithBudgetGuard(unittest.TestCase):
    def test_tracer_with_budget_guard(self):
        from agentguard import BudgetGuard
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        tracer = Tracer(sink=CaptureSink(), service="test")
        with tracer.trace("agent.run") as span:
            span.event("step1")
            span.event("step2")
        self.assertGreater(len(captured), 0)


class TestAsyncTracerMetadata(unittest.TestCase):
    def test_async_tracer_does_not_crash(self):
        """AsyncTracer should not crash when used without metadata/sampling."""
        import asyncio
        from agentguard import AsyncTracer

        async def run():
            captured = []

            class CaptureSink:
                def emit(self, event):
                    captured.append(event)

            tracer = AsyncTracer(sink=CaptureSink(), service="test")
            async with tracer.trace("agent.run") as span:
                span.event("step")
            return captured

        result = asyncio.run(run())
        self.assertGreater(len(result), 0)


if __name__ == "__main__":
    unittest.main()
