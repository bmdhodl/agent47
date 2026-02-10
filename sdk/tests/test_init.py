"""Tests for agentguard.init() one-liner setup."""
from __future__ import annotations

import os
import sys
import tempfile
import types
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

import agentguard
from agentguard.setup import (
    _auto_patch,
    _budget_guard,
    _initialized,
    _tracer,
    get_budget_guard,
    get_tracer,
    init,
    shutdown,
)


class CollectorSink:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def emit(self, event: Dict[str, Any]) -> None:
        self.events.append(event)


@pytest.fixture(autouse=True)
def clean_state():
    """Ensure clean state before and after each test."""
    shutdown()
    yield
    shutdown()


class TestInit:
    """Test agentguard.init() basic behavior."""

    def test_init_returns_tracer(self):
        tracer = agentguard.init(auto_patch=False)
        assert tracer is not None
        assert hasattr(tracer, "trace")

    def test_init_default_local_sink(self):
        tracer = agentguard.init(auto_patch=False)
        assert "JsonlFileSink" in repr(tracer._sink)

    def test_init_custom_trace_file(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            tracer = agentguard.init(trace_file=path, auto_patch=False)
            assert path in repr(tracer._sink)
        finally:
            os.unlink(path)

    def test_init_custom_service(self):
        tracer = agentguard.init(service="test-svc", auto_patch=False)
        assert tracer._service == "test-svc"

    def test_init_default_service(self):
        tracer = agentguard.init(auto_patch=False)
        assert tracer._service == "default"

    def test_init_idempotency_raises(self):
        agentguard.init(auto_patch=False)
        with pytest.raises(RuntimeError, match="already called"):
            agentguard.init(auto_patch=False)

    def test_init_after_shutdown_works(self):
        agentguard.init(auto_patch=False)
        agentguard.shutdown()
        tracer = agentguard.init(auto_patch=False)
        assert tracer is not None


class TestInitEnvVars:
    """Test env var configuration."""

    def test_service_from_env(self):
        with patch.dict(os.environ, {"AGENTGUARD_SERVICE": "env-svc"}):
            tracer = agentguard.init(auto_patch=False)
            assert tracer._service == "env-svc"

    def test_trace_file_from_env(self):
        with patch.dict(os.environ, {"AGENTGUARD_TRACE_FILE": "/tmp/test.jsonl"}):
            tracer = agentguard.init(auto_patch=False)
            assert "/tmp/test.jsonl" in repr(tracer._sink)

    def test_budget_from_env(self):
        with patch.dict(os.environ, {"AGENTGUARD_BUDGET_USD": "3.50"}):
            agentguard.init(auto_patch=False)
            guard = agentguard.get_budget_guard()
            assert guard is not None
            assert guard._max_cost_usd == 3.50

    def test_invalid_budget_env_ignored(self):
        with patch.dict(os.environ, {"AGENTGUARD_BUDGET_USD": "not-a-number"}):
            agentguard.init(auto_patch=False)
            guard = agentguard.get_budget_guard()
            assert guard is None

    def test_kwargs_override_env(self):
        with patch.dict(os.environ, {"AGENTGUARD_SERVICE": "env-svc"}):
            tracer = agentguard.init(service="kwarg-svc", auto_patch=False)
            assert tracer._service == "kwarg-svc"


class TestInitBudgetGuard:
    """Test budget guard setup via init()."""

    def test_no_budget_by_default(self):
        agentguard.init(auto_patch=False)
        assert agentguard.get_budget_guard() is None

    def test_budget_creates_guard(self):
        agentguard.init(budget_usd=5.00, auto_patch=False)
        guard = agentguard.get_budget_guard()
        assert guard is not None
        assert guard._max_cost_usd == 5.00

    def test_budget_warning_threshold(self):
        agentguard.init(budget_usd=10.00, warn_pct=0.5, auto_patch=False)
        guard = agentguard.get_budget_guard()
        assert guard._warn_at_pct == 0.5

    def test_budget_guard_in_tracer_guards(self):
        agentguard.init(budget_usd=5.00, auto_patch=False)
        tracer = agentguard.get_tracer()
        guard = agentguard.get_budget_guard()
        assert guard in tracer._guards


class TestInitLoopGuard:
    """Test loop guard is always enabled."""

    def test_loop_guard_default(self):
        tracer = agentguard.init(auto_patch=False)
        from agentguard.guards import LoopGuard
        loop_guards = [g for g in tracer._guards if isinstance(g, LoopGuard)]
        assert len(loop_guards) == 1
        assert loop_guards[0]._max_repeats == 5

    def test_loop_guard_custom(self):
        tracer = agentguard.init(loop_max=10, auto_patch=False)
        from agentguard.guards import LoopGuard
        loop_guards = [g for g in tracer._guards if isinstance(g, LoopGuard)]
        assert loop_guards[0]._max_repeats == 10


class TestInitAutoPatch:
    """Test auto-patching of LLM clients."""

    def test_auto_patch_openai(self):
        """If openai is importable, it gets patched."""
        # Create mock openai module
        mock_usage = types.SimpleNamespace(prompt_tokens=10, completion_tokens=5, total_tokens=15)
        mock_result = types.SimpleNamespace(usage=mock_usage)

        class MockCompletions:
            def create(self, *a, **kw):
                return mock_result

        class MockChat:
            def __init__(self):
                self.completions = MockCompletions()

        class MockOpenAI:
            def __init__(self, *a, **kw):
                self.chat = MockChat()

        mod = types.ModuleType("openai")
        mod.OpenAI = MockOpenAI

        sys.modules["openai"] = mod
        try:
            tracer = agentguard.init(budget_usd=10.0)
            client = MockOpenAI()
            client.chat.completions.create(model="gpt-4o-mini")

            guard = agentguard.get_budget_guard()
            assert guard.state.tokens_used == 15
            assert guard.state.calls_used == 1
        finally:
            agentguard.shutdown()
            del sys.modules["openai"]

    def test_auto_patch_disabled(self):
        """auto_patch=False skips patching."""
        tracer = agentguard.init(auto_patch=False)
        from agentguard.instrument import _originals
        # No openai/anthropic entries in _originals
        assert "openai_init" not in _originals
        assert "anthropic_init" not in _originals


class TestShutdown:
    """Test shutdown behavior."""

    def test_shutdown_clears_state(self):
        agentguard.init(auto_patch=False)
        assert agentguard.get_tracer() is not None
        agentguard.shutdown()
        assert agentguard.get_tracer() is None

    def test_shutdown_safe_when_not_initialized(self):
        # Should not raise
        agentguard.shutdown()
        agentguard.shutdown()

    def test_shutdown_unpatches(self):
        from agentguard.instrument import _originals

        # Mock openai
        mod = types.ModuleType("openai")
        class MockOpenAI:
            def __init__(self, *a, **kw):
                pass
        mod.OpenAI = MockOpenAI
        sys.modules["openai"] = mod

        try:
            agentguard.init()
            assert "openai_init" in _originals
            agentguard.shutdown()
            assert "openai_init" not in _originals
        finally:
            if "openai" in sys.modules:
                del sys.modules["openai"]


class TestGetters:
    """Test get_tracer() and get_budget_guard()."""

    def test_get_tracer_before_init(self):
        assert agentguard.get_tracer() is None

    def test_get_tracer_after_init(self):
        agentguard.init(auto_patch=False)
        assert agentguard.get_tracer() is not None

    def test_get_budget_guard_no_budget(self):
        agentguard.init(auto_patch=False)
        assert agentguard.get_budget_guard() is None

    def test_get_budget_guard_with_budget(self):
        agentguard.init(budget_usd=1.00, auto_patch=False)
        assert agentguard.get_budget_guard() is not None


class TestModuleLevelAccess:
    """Test that init/shutdown are accessible via agentguard module."""

    def test_module_has_init(self):
        assert hasattr(agentguard, "init")
        assert callable(agentguard.init)

    def test_module_has_shutdown(self):
        assert hasattr(agentguard, "shutdown")
        assert callable(agentguard.shutdown)

    def test_two_line_quickstart(self):
        """The actual two-liner works."""
        import agentguard
        tracer = agentguard.init(auto_patch=False)
        assert tracer is not None
        agentguard.shutdown()
