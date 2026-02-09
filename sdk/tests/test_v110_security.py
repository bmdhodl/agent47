"""Tests for v1.1.0 security hardening: IDN SSRF, name length limits."""
import logging
import unittest

from agentguard.sinks.http import _validate_url
from agentguard.tracing import _MAX_NAME_LENGTH, _truncate_name, Tracer


class TestIdnSsrfProtection(unittest.TestCase):
    """Test IDN/Punycode SSRF bypass protection."""

    def test_ascii_hostname_allowed(self):
        # Should not raise for normal ASCII hostnames
        _validate_url("https://example.com/api/ingest")

    def test_ip_address_allowed(self):
        # Direct public IPs should work
        _validate_url("https://93.184.216.34/api/ingest")

    def test_private_ip_blocked(self):
        with self.assertRaises(ValueError) as cm:
            _validate_url("https://127.0.0.1/api/ingest")
        self.assertIn("private/reserved", str(cm.exception))

    def test_allow_private_flag(self):
        # Should not raise with allow_private=True
        _validate_url("https://127.0.0.1/api/ingest", allow_private=True)

    def test_non_ascii_hostname_rejected(self):
        # Unicode hostnames should be rejected
        with self.assertRaises(ValueError) as cm:
            _validate_url("https://\u2139ocalhost/api/ingest")
        self.assertIn("non-ASCII", str(cm.exception))

    def test_punycode_direct_allowed(self):
        # Already-encoded punycode should pass ASCII check
        # (xn-- prefixed domains are ASCII)
        _validate_url("https://xn--nxasmq6b.example.com/api", allow_private=True)

    def test_invalid_scheme_rejected(self):
        with self.assertRaises(ValueError):
            _validate_url("ftp://example.com/api")

    def test_missing_hostname_rejected(self):
        with self.assertRaises(ValueError):
            _validate_url("https:///api")


class TestNameLengthLimits(unittest.TestCase):
    """Test span/event name truncation."""

    def test_short_name_passes_through(self):
        result = _truncate_name("tool.search")
        self.assertEqual(result, "tool.search")

    def test_exact_limit_passes_through(self):
        name = "x" * _MAX_NAME_LENGTH
        result = _truncate_name(name)
        self.assertEqual(result, name)

    def test_long_name_truncated(self):
        name = "x" * (_MAX_NAME_LENGTH + 500)
        result = _truncate_name(name)
        self.assertEqual(len(result), _MAX_NAME_LENGTH)
        self.assertEqual(result, "x" * _MAX_NAME_LENGTH)

    def test_truncation_logs_warning(self):
        name = "y" * (_MAX_NAME_LENGTH + 100)
        with self.assertLogs("agentguard.tracing", level="WARNING") as cm:
            _truncate_name(name)
        self.assertTrue(any("truncated" in msg.lower() for msg in cm.output))

    def test_tracer_truncates_service_name(self):
        long_service = "svc" * 500
        tracer = Tracer(service=long_service)
        self.assertEqual(len(tracer._service), _MAX_NAME_LENGTH)

    def test_span_name_truncated(self):
        collected = []

        class CollectorSink:
            def emit(self, event):
                collected.append(event)

        tracer = Tracer(sink=CollectorSink())
        long_name = "span." + "a" * _MAX_NAME_LENGTH
        with tracer.trace(long_name):
            pass
        # The name in emitted events should be truncated
        for event in collected:
            self.assertLessEqual(len(event["name"]), _MAX_NAME_LENGTH)

    def test_event_name_truncated(self):
        collected = []

        class CollectorSink:
            def emit(self, event):
                collected.append(event)

        tracer = Tracer(sink=CollectorSink())
        long_event_name = "event." + "b" * _MAX_NAME_LENGTH
        with tracer.trace("test") as ctx:
            ctx.event(long_event_name)

        event_names = [e["name"] for e in collected if e["kind"] == "event"]
        for name in event_names:
            self.assertLessEqual(len(name), _MAX_NAME_LENGTH)

    def test_child_span_name_truncated(self):
        collected = []

        class CollectorSink:
            def emit(self, event):
                collected.append(event)

        tracer = Tracer(sink=CollectorSink())
        long_child = "child." + "c" * _MAX_NAME_LENGTH
        with tracer.trace("parent") as ctx:
            with ctx.span(long_child):
                pass

        span_names = [e["name"] for e in collected if e["kind"] == "span"]
        for name in span_names:
            self.assertLessEqual(len(name), _MAX_NAME_LENGTH)


if __name__ == "__main__":
    unittest.main()
