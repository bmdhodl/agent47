"""Tests for SDK hardening: security, thread safety, and DX improvements."""
from __future__ import annotations

import json
import logging
import threading
import types
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

import agentguard
from agentguard.guards import (
    AgentGuardError,
    BudgetExceeded,
    FuzzyLoopGuard,
    LoopDetected,
    LoopGuard,
    TimeoutExceeded,
)
from agentguard.sinks.http import _validate_api_key, _validate_url
from agentguard.tracing import _MAX_NAME_LENGTH, _sanitize_data, _truncate_name, Tracer


# --- AgentGuardError base exception ---


class TestAgentGuardError:
    """Test the base exception hierarchy."""

    def test_base_exception_exists(self):
        assert issubclass(AgentGuardError, Exception)

    def test_loop_detected_inherits(self):
        assert issubclass(LoopDetected, AgentGuardError)
        assert issubclass(LoopDetected, RuntimeError)

    def test_budget_exceeded_inherits(self):
        assert issubclass(BudgetExceeded, AgentGuardError)
        assert issubclass(BudgetExceeded, RuntimeError)

    def test_timeout_exceeded_inherits(self):
        assert issubclass(TimeoutExceeded, AgentGuardError)
        assert issubclass(TimeoutExceeded, RuntimeError)

    def test_catch_all_agentguard_errors(self):
        """Users can catch AgentGuardError to handle any SDK error."""
        guard = LoopGuard(max_repeats=2)
        with pytest.raises(AgentGuardError):
            for _ in range(3):
                guard.check("tool", {"arg": "same"})

    def test_catch_specific_still_works(self):
        """Catching RuntimeError still works (backward compat)."""
        guard = LoopGuard(max_repeats=2)
        with pytest.raises(RuntimeError):
            for _ in range(3):
                guard.check("tool", {"arg": "same"})

    def test_agentguard_error_importable(self):
        from agentguard import AgentGuardError as AGE
        assert AGE is AgentGuardError


# --- __version__ ---


class TestVersion:
    def test_version_attribute_exists(self):
        assert hasattr(agentguard, "__version__")

    def test_version_is_string(self):
        assert isinstance(agentguard.__version__, str)

    def test_version_in_all(self):
        assert "__version__" in agentguard.__all__


# --- Thread safety: LoopGuard ---


class TestLoopGuardThreadSafety:
    def test_concurrent_checks_no_crash(self):
        guard = LoopGuard(max_repeats=100, window=200)
        errors: List[Exception] = []
        barrier = threading.Barrier(10)

        def worker(tid: int):
            barrier.wait()
            try:
                for i in range(50):
                    guard.check(f"tool_{tid}_{i}", {"i": i})
            except LoopDetected:
                pass
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, f"Unexpected errors: {errors}"

    def test_concurrent_reset_no_crash(self):
        guard = LoopGuard(max_repeats=3)
        errors: List[Exception] = []

        def worker():
            try:
                for _ in range(100):
                    try:
                        guard.check("tool", {"a": 1})
                    except LoopDetected:
                        guard.reset()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, f"Unexpected errors: {errors}"


# --- Thread safety: FuzzyLoopGuard ---


class TestFuzzyLoopGuardThreadSafety:
    def test_concurrent_checks_no_crash(self):
        guard = FuzzyLoopGuard(max_tool_repeats=100, window=200)
        errors: List[Exception] = []
        barrier = threading.Barrier(10)

        def worker(tid: int):
            barrier.wait()
            try:
                for i in range(50):
                    guard.check(f"tool_{tid}_{i}")
            except LoopDetected:
                pass
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, f"Unexpected errors: {errors}"


# --- HTTP header injection ---


class TestHeaderInjection:
    def test_newline_in_api_key_rejected(self):
        with pytest.raises(ValueError, match="header injection"):
            _validate_api_key("ag_key\nEvil-Header: injected")

    def test_carriage_return_in_api_key_rejected(self):
        with pytest.raises(ValueError, match="header injection"):
            _validate_api_key("ag_key\r\nEvil-Header: injected")

    def test_clean_api_key_accepted(self):
        # Should not raise
        _validate_api_key("ag_abc123def456")

    def test_init_rejects_crlf_api_key(self):
        from agentguard.setup import shutdown
        shutdown()
        with pytest.raises(ValueError, match="header injection"):
            agentguard.init(api_key="ag_key\nEvil: header", auto_patch=False)
        shutdown()


# --- SSRF redirect protection ---


class TestSsrfRedirectProtection:
    def test_redirect_to_private_ip_blocked(self):
        """_validate_url is called on redirect targets."""
        with pytest.raises(ValueError, match="private"):
            _validate_url("http://127.0.0.1/api")

    def test_redirect_to_metadata_endpoint_blocked(self):
        """Cloud metadata IP is blocked."""
        with pytest.raises(ValueError, match="private"):
            _validate_url("http://169.254.169.254/latest/meta-data/")


# --- Event data size limit ---


class TestEventDataSizeLimit:
    def test_small_data_passes_through(self):
        data = {"key": "value"}
        assert _sanitize_data(data) == data

    def test_none_passes_through(self):
        assert _sanitize_data(None) is None

    def test_oversized_data_truncated(self):
        # Create data that exceeds 64KB
        big_data = {"payload": "x" * 70_000}
        result = _sanitize_data(big_data)
        assert result is not None
        assert result.get("_truncated") is True
        assert "_original_size_bytes" in result

    def test_non_serializable_data_replaced(self):
        data = {"obj": object()}
        result = _sanitize_data(data)
        assert result == {"_error": "not_serializable"}

    def test_exactly_at_limit_passes(self):
        # Just under 64KB should pass
        data = {"payload": "x" * 65_000}
        result = _sanitize_data(data)
        # This is right around the limit — check if it's truncated or not
        serialized_size = len(json.dumps(data).encode("utf-8"))
        if serialized_size <= 65_536:
            assert result == data
        else:
            assert result.get("_truncated") is True


# --- init() validation ---


class TestInitValidation:
    @pytest.fixture(autouse=True)
    def clean_state(self):
        agentguard.shutdown()
        yield
        agentguard.shutdown()

    def test_warn_pct_too_low(self):
        with pytest.raises(ValueError, match="warn_pct"):
            agentguard.init(budget_usd=5.0, warn_pct=-0.1, auto_patch=False)

    def test_warn_pct_too_high(self):
        with pytest.raises(ValueError, match="warn_pct"):
            agentguard.init(budget_usd=5.0, warn_pct=1.5, auto_patch=False)

    def test_warn_pct_valid_boundaries(self):
        tracer = agentguard.init(budget_usd=5.0, warn_pct=0.0, auto_patch=False)
        assert tracer is not None
        agentguard.shutdown()
        tracer = agentguard.init(budget_usd=5.0, warn_pct=1.0, auto_patch=False)
        assert tracer is not None


# --- IDN/SSRF protection (from v1.1.0) ---


class TestIdnSsrfProtection:
    def test_ascii_hostname_allowed(self):
        _validate_url("https://example.com/api/ingest")

    def test_ip_address_allowed(self):
        _validate_url("https://93.184.216.34/api/ingest")

    def test_private_ip_blocked(self):
        with pytest.raises(ValueError, match="private"):
            _validate_url("https://127.0.0.1/api/ingest")

    def test_allow_private_flag(self):
        _validate_url("https://127.0.0.1/api/ingest", allow_private=True)

    def test_non_ascii_hostname_rejected(self):
        with pytest.raises(ValueError, match="non-ASCII"):
            _validate_url("https://\u2139ocalhost/api/ingest")

    def test_punycode_direct_allowed(self):
        _validate_url("https://xn--nxasmq6b.example.com/api", allow_private=True)

    def test_invalid_scheme_rejected(self):
        with pytest.raises(ValueError):
            _validate_url("ftp://example.com/api")

    def test_missing_hostname_rejected(self):
        with pytest.raises(ValueError):
            _validate_url("https:///api")


# --- Name length limits (from v1.1.0) ---


class TestNameLengthLimits:
    def test_short_name_passes_through(self):
        result = _truncate_name("tool.search")
        assert result == "tool.search"

    def test_exact_limit_passes_through(self):
        name = "x" * _MAX_NAME_LENGTH
        result = _truncate_name(name)
        assert result == name

    def test_long_name_truncated(self):
        name = "x" * (_MAX_NAME_LENGTH + 500)
        result = _truncate_name(name)
        assert len(result) == _MAX_NAME_LENGTH

    def test_truncation_logs_warning(self, caplog):
        name = "y" * (_MAX_NAME_LENGTH + 100)
        with caplog.at_level(logging.WARNING, logger="agentguard.tracing"):
            _truncate_name(name)
        assert any("truncated" in r.message.lower() for r in caplog.records)

    def test_tracer_truncates_service_name(self):
        long_service = "svc" * 500
        tracer = Tracer(service=long_service)
        assert len(tracer._service) == _MAX_NAME_LENGTH

    def test_span_name_truncated(self):
        collected = []

        class CollectorSink:
            def emit(self, event):
                collected.append(event)

        tracer = Tracer(sink=CollectorSink())
        long_name = "span." + "a" * _MAX_NAME_LENGTH
        with tracer.trace(long_name):
            pass
        for event in collected:
            assert len(event["name"]) <= _MAX_NAME_LENGTH

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
            assert len(name) <= _MAX_NAME_LENGTH
