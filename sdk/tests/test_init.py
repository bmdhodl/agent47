"""Tests for agentguard.init() one-liner setup."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import types
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

import agentguard
from agentguard.setup import shutdown


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
            assert tracer._sink._path == path
        finally:
            os.unlink(path)

    def test_init_custom_service(self):
        tracer = agentguard.init(service="test-svc", auto_patch=False)
        assert tracer._service == "test-svc"

    def test_init_custom_session_id(self):
        tracer = agentguard.init(session_id="session-abc", auto_patch=False)
        assert tracer._session_id == "session-abc"

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

    def test_invalid_budget_env_falls_back_to_repo_config_budget(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".agentguard.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"budget_usd": 4.5}, handle)

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch.dict(os.environ, {"AGENTGUARD_BUDGET_USD": "not-a-number"}), patch(
                    "agentguard.setup.logger.warning"
                ) as mock_warning:
                    tracer = agentguard.init(auto_patch=False)
                assert tracer is not None
                assert agentguard.get_budget_guard()._max_cost_usd == 4.5
                mock_warning.assert_called_once()
            finally:
                os.chdir(old_cwd)

    def test_kwargs_override_env(self):
        with patch.dict(os.environ, {"AGENTGUARD_SERVICE": "env-svc"}):
            tracer = agentguard.init(service="kwarg-svc", auto_patch=False)
            assert tracer._service == "kwarg-svc"

    def test_repo_config_applies_when_kwargs_and_env_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".agentguard.json")
            trace_path = os.path.join(tmpdir, ".agentguard", "traces.jsonl")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "service": "repo-svc",
                        "trace_file": ".agentguard/traces.jsonl",
                        "budget_usd": 7.5,
                    },
                    handle,
                )

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                tracer = agentguard.init(auto_patch=False)
                assert tracer._service == "repo-svc"
                assert tracer._sink._path == trace_path
                assert agentguard.get_budget_guard()._max_cost_usd == 7.5
            finally:
                os.chdir(old_cwd)

    def test_repo_config_trace_directory_is_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".agentguard.json")
            trace_path = os.path.join(tmpdir, ".agentguard", "traces.jsonl")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"trace_file": ".agentguard/traces.jsonl"}, handle)

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                tracer = agentguard.init(auto_patch=False)
                with tracer.trace("agent.run") as span:
                    span.event("reasoning.step", data={"step": 1})
            finally:
                agentguard.shutdown()
                os.chdir(old_cwd)

            assert os.path.exists(trace_path)

    def test_env_overrides_repo_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".agentguard.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"service": "repo-svc"}, handle)

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch.dict(os.environ, {"AGENTGUARD_SERVICE": "env-svc"}):
                    tracer = agentguard.init(auto_patch=False)
                assert tracer._service == "env-svc"
            finally:
                os.chdir(old_cwd)

    def test_kwargs_override_repo_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".agentguard.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"service": "repo-svc"}, handle)

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                tracer = agentguard.init(service="kwarg-svc", auto_patch=False)
                assert tracer._service == "kwarg-svc"
            finally:
                os.chdir(old_cwd)

    def test_malformed_repo_config_is_ignored_when_all_values_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".agentguard.json")
            trace_path = os.path.join(tmpdir, "explicit.jsonl")
            with open(config_path, "w", encoding="utf-8") as handle:
                handle.write("{bad json")

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch("agentguard.setup.logger.warning") as mock_warning:
                    tracer = agentguard.init(
                        service="explicit-svc",
                        trace_file=trace_path,
                        budget_usd=2.0,
                        warn_pct=0.6,
                        loop_max=7,
                        retry_max=4,
                        profile="default",
                        auto_patch=False,
                    )
                assert tracer._service == "explicit-svc"
                assert tracer._sink._path == trace_path
                assert agentguard.get_budget_guard()._max_cost_usd == 2.0
                mock_warning.assert_not_called()
            finally:
                os.chdir(old_cwd)

    def test_malformed_repo_config_falls_back_to_defaults_with_warning(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".agentguard.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                handle.write("{bad json")

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                with patch("agentguard.setup.logger.warning") as mock_warning:
                    tracer = agentguard.init(auto_patch=False)
                assert tracer._service == "default"
                mock_warning.assert_called()
            finally:
                os.chdir(old_cwd)

    def test_local_only_ignores_api_key_env(self):
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            with patch.dict(os.environ, {"AGENTGUARD_API_KEY": "ag_env_key"}):
                tracer = agentguard.init(
                    trace_file=path,
                    local_only=True,
                    auto_patch=False,
                )
            assert "JsonlFileSink" in repr(tracer._sink)
        finally:
            os.unlink(path)

    def test_local_only_conflicts_with_api_key(self):
        with pytest.raises(ValueError, match="local_only=True cannot be combined with api_key"):
            agentguard.init(
                api_key="ag_conflict",
                local_only=True,
                auto_patch=False,
            )

    def test_api_key_not_logged(self):
        with patch("agentguard.setup.logger.info") as mock_info:
            agentguard.init(api_key="ag_secret_value", auto_patch=False)

        logged_args = " ".join(str(arg) for arg in mock_info.call_args.args)
        assert "ag_secret_value" not in logged_args

    def test_session_id_not_logged_raw(self):
        with patch("agentguard.setup.logger.info") as mock_info:
            agentguard.init(session_id="session-secret-123", auto_patch=False)

        logged_args = " ".join(str(arg) for arg in mock_info.call_args.args)
        assert "session-secret-123" not in logged_args
        assert "session=%s" in logged_args

    def test_blank_session_id_rejected(self):
        with pytest.raises(ValueError, match="session_id"):
            agentguard.init(session_id="   ", auto_patch=False)


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

    def test_coding_agent_profile_tightens_guard_defaults(self):
        tracer = agentguard.init(profile="coding-agent", auto_patch=False)
        from agentguard.guards import LoopGuard, RetryGuard

        loop_guards = [g for g in tracer._guards if isinstance(g, LoopGuard)]
        retry_guards = [g for g in tracer._guards if isinstance(g, RetryGuard)]

        assert loop_guards[0]._max_repeats == 3
        assert retry_guards[0].max_retries == 2

    def test_deployed_agent_profile_tightens_guard_defaults(self):
        tracer = agentguard.init(
            profile="deployed-agent", budget_usd=10.00, auto_patch=False
        )
        from agentguard.guards import LoopGuard, RetryGuard

        loop_guards = [g for g in tracer._guards if isinstance(g, LoopGuard)]
        retry_guards = [g for g in tracer._guards if isinstance(g, RetryGuard)]
        budget_guard = agentguard.get_budget_guard()

        assert loop_guards[0]._max_repeats == 2
        assert retry_guards[0].max_retries == 1
        assert budget_guard._warn_at_pct == 0.5

    def test_repo_config_profile_applies_retry_guard(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".agentguard.json")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"profile": "coding-agent"}, handle)

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                tracer = agentguard.init(auto_patch=False)
                from agentguard.guards import RetryGuard

                retry_guards = [g for g in tracer._guards if isinstance(g, RetryGuard)]
                assert retry_guards[0].max_retries == 2
            finally:
                os.chdir(old_cwd)

    def test_repo_config_profile_applies_when_core_args_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, ".agentguard.json")
            trace_path = os.path.join(tmpdir, "explicit.jsonl")
            with open(config_path, "w", encoding="utf-8") as handle:
                json.dump({"profile": "coding-agent"}, handle)

            old_cwd = os.getcwd()
            os.chdir(tmpdir)
            try:
                tracer = agentguard.init(
                    service="explicit-svc",
                    trace_file=trace_path,
                    budget_usd=2.0,
                    auto_patch=False,
                )
                from agentguard.guards import RetryGuard

                retry_guards = [g for g in tracer._guards if isinstance(g, RetryGuard)]
                assert retry_guards[0].max_retries == 2
            finally:
                os.chdir(old_cwd)


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
            agentguard.init(budget_usd=10.0)
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
        agentguard.init(auto_patch=False)
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
