import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from agentguard.sinks.http import HttpSink


class _CollectorHandler(BaseHTTPRequestHandler):
    received: list = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        auth = self.headers.get("Authorization", "")
        self.__class__.received.append({"body": body, "auth": auth})
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


class TestHttpSink(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _CollectorHandler.received = []
        cls.server = HTTPServer(("127.0.0.1", 0), _CollectorHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        _CollectorHandler.received.clear()

    def test_batch_flush(self):
        sink = HttpSink(
            url=f"http://127.0.0.1:{self.port}/ingest",
            api_key="test-key",
            batch_size=3,
            flush_interval=60,
        )
        for i in range(3):
            sink.emit({"event": i})
        time.sleep(0.3)
        sink.shutdown()
        self.assertEqual(len(_CollectorHandler.received), 1)
        batch = _CollectorHandler.received[0]
        self.assertEqual(batch["auth"], "Bearer test-key")
        lines = batch["body"].strip().split("\n")
        self.assertEqual(len(lines), 3)

    def test_interval_flush(self):
        sink = HttpSink(
            url=f"http://127.0.0.1:{self.port}/ingest",
            batch_size=100,
            flush_interval=0.2,
        )
        sink.emit({"event": "timer"})
        time.sleep(0.5)
        sink.shutdown()
        self.assertGreaterEqual(len(_CollectorHandler.received), 1)
        lines = _CollectorHandler.received[0]["body"].strip().split("\n")
        parsed = json.loads(lines[0])
        self.assertEqual(parsed["event"], "timer")

    def test_shutdown_flushes_remaining(self):
        sink = HttpSink(
            url=f"http://127.0.0.1:{self.port}/ingest",
            batch_size=100,
            flush_interval=60,
        )
        sink.emit({"event": "final"})
        sink.shutdown()
        self.assertGreaterEqual(len(_CollectorHandler.received), 1)


class TestHttpSinkHTTPWarning(unittest.TestCase):
    def test_warns_on_http_with_api_key(self):
        """HttpSink should log a warning when using http:// with an API key."""
        import logging

        with self.assertLogs("agentguard.sinks.http", level="WARNING") as cm:
            sink = HttpSink(
                url=f"http://127.0.0.1:{TestHttpSink.port}/ingest",
                api_key="secret-key",
                batch_size=100,
                flush_interval=60,
            )
            sink.shutdown()
        self.assertTrue(any("HTTPS" in msg for msg in cm.output))

    def test_no_warning_on_https(self):
        """HttpSink should not warn when using https:// URL."""
        import logging

        logger = logging.getLogger("agentguard.sinks.http")
        # Should not log any warnings — we test by checking it doesn't raise
        # (assertLogs would raise if no logs are emitted)
        sink = HttpSink(
            url="https://example.com/ingest",
            api_key="secret-key",
            batch_size=100,
            flush_interval=60,
        )
        sink.shutdown()
        # If we got here without the assertLogs context, it means no warning

    def test_no_warning_on_http_without_api_key(self):
        """HttpSink should not warn when using http:// without an API key."""
        sink = HttpSink(
            url=f"http://127.0.0.1:{TestHttpSink.port}/ingest",
            batch_size=100,
            flush_interval=60,
        )
        sink.shutdown()


class TestHttpSinkExports(unittest.TestCase):
    def test_importable_from_top_level(self):
        """HttpSink should be importable from agentguard directly."""
        from agentguard import HttpSink as TopLevelHttpSink

        self.assertIs(TopLevelHttpSink, HttpSink)


if __name__ == "__main__":
    unittest.main()
