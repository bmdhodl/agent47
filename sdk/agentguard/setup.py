"""One-liner setup for AgentGuard.

Usage::

    import agentguard
    agentguard.init()

That's it. Reads config from environment variables, auto-patches LLM
clients, and starts tracing with sane defaults.

Environment variables:
    AGENTGUARD_API_KEY    — API key for dashboard. If set, traces go to
                            the hosted dashboard. If missing, traces go
                            to a local JSONL file.
    AGENTGUARD_BUDGET_USD — Dollar budget limit (e.g. "5.00"). Enables
                            BudgetGuard with 80% warning threshold.
    AGENTGUARD_SERVICE    — Service name for traces. Default: "default".
    AGENTGUARD_TRACE_FILE — Local trace file path. Default: "traces.jsonl".
                            Only used when AGENTGUARD_API_KEY is not set.

Power-user override::

    agentguard.init(
        api_key="ag_...",
        budget_usd=5.00,
        service="my-agent",
    )
"""
from __future__ import annotations

import logging
import os
from typing import Any, Optional

logger = logging.getLogger("agentguard")

# Global state — set by init(), cleared by shutdown()
_tracer: Optional[Any] = None
_budget_guard: Optional[Any] = None
_initialized: bool = False


def init(
    *,
    api_key: Optional[str] = None,
    budget_usd: Optional[float] = None,
    service: Optional[str] = None,
    session_id: Optional[str] = None,
    trace_file: Optional[str] = None,
    warn_pct: Optional[float] = None,
    loop_max: Optional[int] = None,
    retry_max: Optional[int] = None,
    profile: Optional[str] = None,
    auto_patch: bool = True,
    watermark: bool = True,
    local_only: bool = False,
) -> Any:
    """Initialize AgentGuard with one call.

    Reads configuration from environment variables, falling back to
    keyword arguments, falling back to sane defaults.

    Args:
        api_key: Dashboard API key. Env: ``AGENTGUARD_API_KEY``.
        budget_usd: Dollar budget limit. Env: ``AGENTGUARD_BUDGET_USD``.
        service: Service name. Env: ``AGENTGUARD_SERVICE``. Default: "default".
        session_id: Optional identifier that correlates multiple tracer instances
            across the same higher-level agent session. No environment variable.
        trace_file: Local JSONL path (used when no api_key).
            Env: ``AGENTGUARD_TRACE_FILE``. Default: "traces.jsonl".
        warn_pct: Budget warning threshold (0.0-1.0). Defaults to the selected
            profile's value (0.8 for built-in profiles).
        loop_max: Max identical calls before LoopGuard fires. Defaults to the
            selected profile's value.
        retry_max: Max consecutive retries per tool before RetryGuard fires.
            Defaults to the selected profile's value.
        profile: Built-in guard profile. Supported: ``default``, ``coding-agent``.
            May be passed explicitly or loaded from repo config. No environment
            variable. Default: ``default``.
        auto_patch: Auto-patch OpenAI/Anthropic clients. Default: True.
        watermark: Emit "Traced by AgentGuard" in trace output. Default: True.
        local_only: Force local file output. Ignores any dashboard API key from
            the environment and raises if an explicit api_key is provided.
            Default: False.

    Returns:
        The configured Tracer instance.

    Raises:
        RuntimeError: If init() is called twice without shutdown() first.
    """
    global _tracer, _budget_guard, _initialized

    if _initialized:
        raise RuntimeError(
            "agentguard.init() already called. Call agentguard.shutdown() first "
            "to re-initialize, or use the returned tracer directly."
        )

    # --- Validate inputs ---
    if warn_pct is not None and not (0.0 <= warn_pct <= 1.0):
        raise ValueError(f"warn_pct must be between 0.0 and 1.0, got {warn_pct}")
    if local_only and api_key:
        raise ValueError("local_only=True cannot be combined with api_key")
    if api_key and ("\n" in api_key or "\r" in api_key):
        raise ValueError(
            "api_key must not contain newline or carriage return characters "
            "(possible HTTP header injection)"
        )

    from agentguard.profiles import get_profile_defaults, normalize_profile
    from agentguard.repo_config import CONFIG_FILE_NAME, load_repo_config_safely

    needs_repo_defaults = any(
        value is None
        for value in (
            budget_usd,
            service,
            trace_file,
            warn_pct,
            loop_max,
            retry_max,
            profile,
        )
    )
    repo_config = {}
    if needs_repo_defaults:
        _, repo_config, repo_error = load_repo_config_safely()
        if repo_error:
            logger.warning("Ignoring %s: %s", CONFIG_FILE_NAME, repo_error)

    resolved_profile = normalize_profile(profile or repo_config.get("profile"))
    profile_defaults = get_profile_defaults(resolved_profile)

    # --- Resolve config: kwargs > env vars > repo config > profile defaults > hard defaults ---
    resolved_key = None if local_only else (api_key or os.environ.get("AGENTGUARD_API_KEY"))
    resolved_service = (
        service
        or os.environ.get("AGENTGUARD_SERVICE")
        or repo_config.get("service")
        or "default"
    )
    resolved_file = (
        trace_file
        or os.environ.get("AGENTGUARD_TRACE_FILE")
        or repo_config.get("trace_file")
        or "traces.jsonl"
    )
    resolved_warn_pct = (
        warn_pct
        if warn_pct is not None
        else repo_config.get("warn_pct", profile_defaults["warn_pct"])
    )
    resolved_loop_max = (
        loop_max if loop_max is not None else repo_config.get("loop_max", profile_defaults["loop_max"])
    )
    resolved_retry_max = (
        retry_max
        if retry_max is not None
        else repo_config.get("retry_max", profile_defaults["retry_max"])
    )

    resolved_budget: Optional[float] = budget_usd
    if resolved_budget is None:
        env_budget = os.environ.get("AGENTGUARD_BUDGET_USD")
        if env_budget:
            try:
                resolved_budget = float(env_budget)
            except ValueError:
                logger.warning(
                    "Invalid AGENTGUARD_BUDGET_USD=%r, ignoring", env_budget
                )
                if "budget_usd" in repo_config:
                    resolved_budget = float(repo_config["budget_usd"])
        elif "budget_usd" in repo_config:
            resolved_budget = float(repo_config["budget_usd"])

    # --- Build sink ---
    if resolved_key:
        from agentguard.sinks.http import HttpSink

        sink = HttpSink(
            url="https://app.agentguard47.com/api/ingest",
            api_key=resolved_key,
        )
    else:
        from agentguard.tracing import JsonlFileSink

        sink = JsonlFileSink(resolved_file)

    # --- Build guards ---
    from agentguard.guards import BudgetGuard, LoopGuard, RetryGuard

    guards = [LoopGuard(max_repeats=resolved_loop_max, window=max(resolved_loop_max, 6))]

    if resolved_retry_max is not None:
        guards.append(RetryGuard(max_retries=resolved_retry_max))

    _budget_guard = None
    if resolved_budget is not None:
        _budget_guard = BudgetGuard(
            max_cost_usd=resolved_budget,
            warn_at_pct=resolved_warn_pct,
            on_warning=lambda msg: logger.warning(msg),
        )
        guards.append(_budget_guard)

    # --- Build tracer ---
    from agentguard.tracing import Tracer

    _tracer = Tracer(
        sink=sink,
        service=resolved_service,
        session_id=session_id,
        guards=guards,
        watermark=watermark,
    )

    # --- Auto-patch LLM clients ---
    if auto_patch:
        _auto_patch(_tracer, _budget_guard)

    _initialized = True

    # Log what we did
    sink_desc = "dashboard" if resolved_key else resolved_file
    budget_desc = f"${resolved_budget:.2f}" if resolved_budget else "unlimited"
    logger.info(
        "AgentGuard initialized: service=%s session_id=%s sink=%s budget=%s profile=%s",
        resolved_service, session_id, sink_desc, budget_desc, resolved_profile,
    )

    return _tracer


def _auto_patch(tracer: Any, budget_guard: Optional[Any]) -> None:
    """Auto-patch OpenAI and Anthropic clients if importable."""
    from agentguard.instrument import (
        patch_anthropic,
        patch_anthropic_async,
        patch_openai,
        patch_openai_async,
    )

    # OpenAI sync + async
    try:
        import openai  # noqa: F401

        patch_openai(tracer, budget_guard=budget_guard)
        patch_openai_async(tracer, budget_guard=budget_guard)
        logger.debug("Auto-patched OpenAI (sync + async)")
    except ImportError:
        pass

    # Anthropic sync + async
    try:
        import anthropic  # noqa: F401

        patch_anthropic(tracer, budget_guard=budget_guard)
        patch_anthropic_async(tracer, budget_guard=budget_guard)
        logger.debug("Auto-patched Anthropic (sync + async)")
    except ImportError:
        pass


def shutdown() -> None:
    """Flush traces and tear down AgentGuard.

    Safe to call even if init() was never called.
    After shutdown(), init() can be called again.
    """
    global _tracer, _budget_guard, _initialized

    if _tracer is not None:
        sink = getattr(_tracer, "_sink", None)
        if hasattr(sink, "shutdown"):
            sink.shutdown()

    from agentguard.instrument import (
        unpatch_anthropic,
        unpatch_anthropic_async,
        unpatch_openai,
        unpatch_openai_async,
    )

    unpatch_openai()
    unpatch_openai_async()
    unpatch_anthropic()
    unpatch_anthropic_async()

    _tracer = None
    _budget_guard = None
    _initialized = False


def get_tracer() -> Any:
    """Get the global tracer created by init().

    Returns:
        The Tracer instance, or None if init() hasn't been called.
    """
    return _tracer


def get_budget_guard() -> Any:
    """Get the global BudgetGuard created by init().

    Returns:
        The BudgetGuard instance, or None if no budget was configured.
    """
    return _budget_guard
