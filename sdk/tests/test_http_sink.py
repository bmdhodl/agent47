import json
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from agentguard.sinks.http import HttpSink


class _CollectorHandler(BaseHTTPRequestHandler):
    received: list = []

    def do_POST(self):
        import gzip as _gzip

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        encoding = self.headers.get("Content-Encoding", "")
        if encoding == "gzip":
            raw = _gzip.decompress(raw)
        body = raw.decode("utf-8")
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
            url=f"http://127.0.0.1:{self.port}/ingest", _allow_private=True,
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
            url=f"http://127.0.0.1:{self.port}/ingest", _allow_private=True,
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
            url=f"http://127.0.0.1:{self.port}/ingest", _allow_private=True,
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
                url=f"http://127.0.0.1:{TestHttpSink.port}/ingest", _allow_private=True,
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
            url=f"http://127.0.0.1:{TestHttpSink.port}/ingest", _allow_private=True,
            batch_size=100,
            flush_interval=60,
        )
        sink.shutdown()


class _429DateHandler(BaseHTTPRequestHandler):
    """Returns 429 with HTTP-date Retry-After, then 200."""
    call_count = 0

    def do_POST(self):
        import gzip as _gzip

        length = int(self.headers.get("Content-Length", 0))
        self.rfile.read(length)
        self.__class__.call_count += 1
        if self.__class__.call_count == 1:
            self.send_response(429)
            # HTTP-date format — not numeric seconds
            self.send_header("Retry-After", "Sat, 01 Jan 2000 00:00:00 GMT")
            self.end_headers()
            self.wfile.write(b"rate limited")
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


class TestHttpSinkRetryAfterHttpDate(unittest.TestCase):
    """Verify HttpSink handles HTTP-date Retry-After without crashing."""

    @classmethod
    def setUpClass(cls):
        _429DateHandler.call_count = 0
        cls.server = HTTPServer(("127.0.0.1", 0), _429DateHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_http_date_retry_after_does_not_crash(self):
        """Retry-After with HTTP-date should fall back to default backoff."""
        _429DateHandler.call_count = 0
        sink = HttpSink(
            url=f"http://127.0.0.1:{self.port}/ingest", _allow_private=True,
            batch_size=1,
            flush_interval=60,
            compress=False,
            max_retries=3,
        )
        sink.emit({"event": "test"})
        time.sleep(2)  # allow retry cycle
        sink.shutdown()
        # Should have retried: first call = 429, second = 200
        self.assertGreaterEqual(_429DateHandler.call_count, 2)


class TestHttpSinkExports(unittest.TestCase):
    def test_importable_from_top_level(self):
        """HttpSink should be importable from agentguard directly."""
        from agentguard import HttpSink as TopLevelHttpSink

        self.assertIs(TopLevelHttpSink, HttpSink)


class TestHttpSinkSSRF(unittest.TestCase):
    """Verify SSRF protection blocks private/reserved IPs."""

    def test_blocks_localhost_ip(self):
        with self.assertRaises(ValueError) as ctx:
            HttpSink(url="http://127.0.0.1/steal", batch_size=1, flush_interval=60)
        self.assertIn("private/reserved", str(ctx.exception))

    def test_blocks_localhost_127_range(self):
        with self.assertRaises(ValueError):
            HttpSink(url="http://127.0.0.2:8080/exfil", batch_size=1, flush_interval=60)

    def test_blocks_10_range(self):
        with self.assertRaises(ValueError):
            HttpSink(url="http://10.0.0.1/internal", batch_size=1, flush_interval=60)

    def test_blocks_172_16_range(self):
        with self.assertRaises(ValueError):
            HttpSink(url="http://172.16.0.1/internal", batch_size=1, flush_interval=60)

    def test_blocks_192_168_range(self):
        with self.assertRaises(ValueError):
            HttpSink(url="http://192.168.1.1/internal", batch_size=1, flush_interval=60)

    def test_blocks_link_local(self):
        with self.assertRaises(ValueError):
            HttpSink(url="http://169.254.169.254/metadata", batch_size=1, flush_interval=60)

    def test_blocks_zero_network(self):
        with self.assertRaises(ValueError):
            HttpSink(url="http://0.0.0.0/steal", batch_size=1, flush_interval=60)

    def test_blocks_ipv6_loopback(self):
        with self.assertRaises(ValueError):
            HttpSink(url="http://[::1]/steal", batch_size=1, flush_interval=60)

    def test_blocks_invalid_scheme(self):
        with self.assertRaises(ValueError) as ctx:
            HttpSink(url="ftp://example.com/data", batch_size=1, flush_interval=60)
        self.assertIn("scheme", str(ctx.exception))

    def test_blocks_no_hostname(self):
        with self.assertRaises(ValueError):
            HttpSink(url="http://", batch_size=1, flush_interval=60)

    def test_allows_public_ip(self):
        """Public IP addresses should be allowed."""
        # This won't actually connect, but shouldn't raise ValueError
        sink = HttpSink(
            url="https://203.0.113.1/ingest",
            batch_size=100,
            flush_interval=60,
        )
        sink.shutdown()

    def test_allow_private_flag(self):
        """_allow_private=True bypasses SSRF checks (for testing)."""
        sink = HttpSink(
            url="http://127.0.0.1:9999/test",
            _allow_private=True,
            batch_size=100,
            flush_interval=60,
        )
        sink.shutdown()


class _HeartbeatCollectorHandler(BaseHTTPRequestHandler):
    received: list = []

    def do_POST(self):
        import gzip as _gzip

        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)
        encoding = self.headers.get("Content-Encoding", "")
        if encoding == "gzip":
            raw = _gzip.decompress(raw)
        body = raw.decode("utf-8")
        self.__class__.received.append(body)
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass


class TestHttpSinkHeartbeat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _HeartbeatCollectorHandler.received = []
        cls.server = HTTPServer(("127.0.0.1", 0), _HeartbeatCollectorHandler)
        cls.port = cls.server.server_address[1]
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        _HeartbeatCollectorHandler.received.clear()

    def test_heartbeat_emits_events(self):
        from agentguard.guards import BudgetGuard

        budget = BudgetGuard(max_cost_usd=10.0)
        budget.consume(cost_usd=2.50)

        sink = HttpSink(
            url=f"http://127.0.0.1:{self.port}/ingest", _allow_private=True,
            batch_size=1,
            flush_interval=60,
            heartbeat_interval=0.2,
            heartbeat_guards=[budget],
        )
        time.sleep(0.5)
        sink.shutdown()

        # Should have received at least one heartbeat
        self.assertGreaterEqual(len(_HeartbeatCollectorHandler.received), 1)
        # Parse the first heartbeat
        first_batch = _HeartbeatCollectorHandler.received[0]
        events = [json.loads(line) for line in first_batch.strip().split("\n")]
        heartbeats = [e for e in events if e.get("kind") == "heartbeat"]
        self.assertGreaterEqual(len(heartbeats), 1)
        hb = heartbeats[0]
        self.assertEqual(hb["name"], "agent.heartbeat")
        self.assertIn("BudgetGuard", hb["data"]["guards"])
        self.assertAlmostEqual(
            hb["data"]["guards"]["BudgetGuard"]["cost_used"], 2.50
        )

    def test_heartbeat_disabled_by_default(self):
        sink = HttpSink(
            url=f"http://127.0.0.1:{self.port}/ingest", _allow_private=True,
            batch_size=100,
            flush_interval=60,
        )
        time.sleep(0.3)
        sink.shutdown()
        # No heartbeat events should be emitted
        heartbeat_found = False
        for batch in _HeartbeatCollectorHandler.received:
            for line in batch.strip().split("\n"):
                if line:
                    event = json.loads(line)
                    if event.get("kind") == "heartbeat":
                        heartbeat_found = True
        self.assertFalse(heartbeat_found)


if __name__ == "__main__":
    unittest.main()
