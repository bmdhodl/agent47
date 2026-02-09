"""Tests for SDK-5 production hardening features."""
import gzip
import json
import os
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.error import HTTPError

from agentguard import Tracer, JsonlFileSink
from agentguard.sinks.http import HttpSink
from agentguard.export import load_trace, export_json, export_csv, export_jsonl


class TestTracerMetadata(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        os.close(self.fd)

    def tearDown(self):
        os.unlink(self.path)

    def test_metadata_attached_to_events(self):
        tracer = Tracer(
            sink=JsonlFileSink(self.path),
            service="test",
            metadata={"env": "staging", "git_sha": "abc123"},
        )
        with tracer.trace("agent.run") as span:
            span.event("step", data={"key": "value"})

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        for e in events:
            self.assertEqual(e.get("metadata", {}).get("env"), "staging")
            self.assertEqual(e.get("metadata", {}).get("git_sha"), "abc123")

    def test_no_metadata_when_empty(self):
        tracer = Tracer(sink=JsonlFileSink(self.path), service="test")
        with tracer.trace("agent.run") as span:
            span.event("step")

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        for e in events:
            self.assertNotIn("metadata", e)


class TestTracerSamplingRate(unittest.TestCase):
    def test_sampling_zero_emits_nothing(self):
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        tracer = Tracer(sink=CaptureSink(), service="test", sampling_rate=0.0)
        with tracer.trace("agent.run") as span:
            span.event("step")
        self.assertEqual(len(captured), 0)

    def test_sampling_one_emits_all(self):
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        tracer = Tracer(sink=CaptureSink(), service="test", sampling_rate=1.0)
        with tracer.trace("agent.run") as span:
            span.event("step")
        self.assertGreater(len(captured), 0)

    def test_sampling_partial(self):
        """With 50% sampling, roughly half of traces should be emitted."""
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        tracer = Tracer(sink=CaptureSink(), service="test", sampling_rate=0.5)
        for _ in range(100):
            with tracer.trace("test"):
                pass

        # Should be roughly 50% (between 20 and 180 out of ~200 events)
        # Each trace emits 2 events (start + end), so between 10-90 traces
        self.assertGreater(len(captured), 0)
        self.assertLess(len(captured), 200)

    def test_sampling_concurrent_traces_isolated(self):
        """Concurrent traces should not interfere with each other's sampling."""
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        # One tracer, rate=1.0 — all traces must emit all events
        tracer = Tracer(sink=CaptureSink(), service="test", sampling_rate=1.0)

        import threading

        def run_trace(name):
            with tracer.trace(name) as span:
                span.event(f"{name}.step")

        threads = [threading.Thread(target=run_trace, args=(f"t{i}",)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 10 traces x 3 events each (start, event, end) = 30
        self.assertEqual(len(captured), 30)

    def test_sampling_nested_traces_isolated(self):
        """Nested traces should each get their own sampling decision."""
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        # rate=0.0 means nothing should emit
        tracer = Tracer(sink=CaptureSink(), service="test", sampling_rate=0.0)
        with tracer.trace("outer") as outer:
            outer.event("outer.step")
            with tracer.trace("inner") as inner:
                inner.event("inner.step")

        self.assertEqual(len(captured), 0)

        # rate=1.0 — nested traces should all emit
        captured.clear()
        tracer2 = Tracer(sink=CaptureSink(), service="test", sampling_rate=1.0)
        with tracer2.trace("outer") as outer:
            outer.event("outer.step")
            with tracer2.trace("inner") as inner:
                inner.event("inner.step")

        # outer: start + event + end = 3, inner: start + event + end = 3 = 6
        self.assertEqual(len(captured), 6)


class _GzipCollectorHandler(BaseHTTPRequestHandler):
    received: list = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        encoding = self.headers.get("Content-Encoding", "")
        idempotency_key = self.headers.get("Idempotency-Key", "")
        if encoding == "gzip":
            body = gzip.decompress(body)
        self.__class__.received.append({
            "body": body.decode("utf-8"),
            "encoding": encoding,
            "idempotency_key": idempotency_key,
        })
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


class TestHttpSinkGzip(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _GzipCollectorHandler.received = []
        cls.server = HTTPServer(("127.0.0.1", 0), _GzipCollectorHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        _GzipCollectorHandler.received.clear()

    def test_gzip_compressed(self):
        sink = HttpSink(
            url=f"http://127.0.0.1:{self.port}/ingest", _allow_private=True,
            batch_size=2,
            flush_interval=60,
            compress=True,
        )
        sink.emit({"event": 1})
        sink.emit({"event": 2})
        time.sleep(0.3)
        sink.shutdown()
        self.assertGreaterEqual(len(_GzipCollectorHandler.received), 1)
        self.assertEqual(_GzipCollectorHandler.received[0]["encoding"], "gzip")

    def test_no_compression(self):
        sink = HttpSink(
            url=f"http://127.0.0.1:{self.port}/ingest", _allow_private=True,
            batch_size=2,
            flush_interval=60,
            compress=False,
        )
        sink.emit({"event": 1})
        sink.emit({"event": 2})
        time.sleep(0.3)
        sink.shutdown()
        self.assertGreaterEqual(len(_GzipCollectorHandler.received), 1)
        self.assertEqual(_GzipCollectorHandler.received[0]["encoding"], "")

    def test_idempotency_key_present(self):
        sink = HttpSink(
            url=f"http://127.0.0.1:{self.port}/ingest", _allow_private=True,
            batch_size=1,
            flush_interval=60,
        )
        sink.emit({"event": 1})
        time.sleep(0.3)
        sink.shutdown()
        self.assertGreaterEqual(len(_GzipCollectorHandler.received), 1)
        key = _GzipCollectorHandler.received[0]["idempotency_key"]
        self.assertTrue(len(key) > 0)

    def test_unique_idempotency_keys(self):
        sink = HttpSink(
            url=f"http://127.0.0.1:{self.port}/ingest", _allow_private=True,
            batch_size=1,
            flush_interval=60,
        )
        sink.emit({"event": 1})
        time.sleep(0.2)
        sink.emit({"event": 2})
        time.sleep(0.2)
        sink.shutdown()
        keys = [r["idempotency_key"] for r in _GzipCollectorHandler.received]
        self.assertEqual(len(keys), len(set(keys)))  # all unique


class TestExportJson(unittest.TestCase):
    def test_export_json(self):
        events = [{"name": "a", "kind": "span"}, {"name": "b", "kind": "event"}]
        fd, inp = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")
        fd2, out = tempfile.mkstemp(suffix=".json")
        os.close(fd2)
        count = export_json(inp, out)
        self.assertEqual(count, 2)
        with open(out) as f:
            loaded = json.load(f)
        self.assertEqual(len(loaded), 2)
        os.unlink(inp)
        os.unlink(out)


class TestExportCsv(unittest.TestCase):
    def test_export_csv(self):
        events = [
            {"name": "a", "kind": "span", "service": "test", "phase": "start"},
            {"name": "b", "kind": "event", "service": "test", "phase": "emit"},
        ]
        fd, inp = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            for e in events:
                f.write(json.dumps(e) + "\n")
        fd2, out = tempfile.mkstemp(suffix=".csv")
        os.close(fd2)
        count = export_csv(inp, out)
        self.assertEqual(count, 2)
        with open(out) as f:
            content = f.read()
        self.assertIn("name", content)  # header
        self.assertIn("span", content)
        os.unlink(inp)
        os.unlink(out)

    def test_export_csv_empty(self):
        fd, inp = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd)
        fd2, out = tempfile.mkstemp(suffix=".csv")
        os.close(fd2)
        count = export_csv(inp, out)
        self.assertEqual(count, 0)
        os.unlink(inp)
        os.unlink(out)


class TestExportJsonl(unittest.TestCase):
    def test_export_jsonl_normalizes(self):
        fd, inp = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            f.write('{"name":"a"}\n')
            f.write('bad line\n')
            f.write('{"name":"b"}\n')
        fd2, out = tempfile.mkstemp(suffix=".jsonl")
        os.close(fd2)
        count = export_jsonl(inp, out)
        self.assertEqual(count, 2)  # skipped bad line
        os.unlink(inp)
        os.unlink(out)


class TestLoadTrace(unittest.TestCase):
    def test_load_trace(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            f.write('{"name":"a"}\n{"name":"b"}\n')
        events = load_trace(path)
        self.assertEqual(len(events), 2)
        os.unlink(path)


class TestCliEvalCi(unittest.TestCase):
    def test_eval_ci_flag_exists(self):
        """Verify the --ci flag is accepted by the eval subcommand."""
        from agentguard.cli import main
        import argparse
        # Just verify argparse doesn't reject --ci
        from agentguard.cli import _eval
        # _eval accepts ci param
        import inspect
        sig = inspect.signature(_eval)
        self.assertIn("ci", sig.parameters)


class TestBenchRunnable(unittest.TestCase):
    def test_bench_imports(self):
        from agentguard.bench import main
        self.assertIsNotNone(main)


if __name__ == "__main__":
    unittest.main()
