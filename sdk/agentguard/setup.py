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
    trace_file: Optional[str] = None,
    warn_pct: float = 0.8,
    loop_max: int = 5,
    auto_patch: bool = True,
) -> Any:
    """Initialize AgentGuard with one call.

    Reads configuration from environment variables, falling back to
    keyword arguments, falling back to sane defaults.

    Args:
        api_key: Dashboard API key. Env: ``AGENTGUARD_API_KEY``.
        budget_usd: Dollar budget limit. Env: ``AGENTGUARD_BUDGET_USD``.
        service: Service name. Env: ``AGENTGUARD_SERVICE``. Default: "default".
        trace_file: Local JSONL path (used when no api_key).
            Env: ``AGENTGUARD_TRACE_FILE``. Default: "traces.jsonl".
        warn_pct: Budget warning threshold (0.0-1.0). Default: 0.8.
        loop_max: Max identical calls before LoopGuard fires. Default: 5.
        auto_patch: Auto-patch OpenAI/Anthropic clients. Default: True.

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
    if not (0.0 <= warn_pct <= 1.0):
        raise ValueError(
            f"warn_pct must be between 0.0 and 1.0, got {warn_pct}"
        )
    if api_key and ("\n" in api_key or "\r" in api_key):
        raise ValueError(
            "api_key must not contain newline or carriage return characters "
            "(possible HTTP header injection)"
        )

    # --- Resolve config: kwargs > env vars > defaults ---
    resolved_key = api_key or os.environ.get("AGENTGUARD_API_KEY")
    resolved_service = service or os.environ.get("AGENTGUARD_SERVICE", "default")
    resolved_file = trace_file or os.environ.get("AGENTGUARD_TRACE_FILE", "traces.jsonl")

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
    from agentguard.guards import BudgetGuard, LoopGuard

    guards = [LoopGuard(max_repeats=loop_max, window=max(loop_max, 6))]

    if resolved_budget is not None:
        _budget_guard = BudgetGuard(
            max_cost_usd=resolved_budget,
            warn_at_pct=warn_pct,
            on_warning=lambda msg: logger.warning(msg),
        )
        guards.append(_budget_guard)

    # --- Build tracer ---
    from agentguard.tracing import Tracer

    _tracer = Tracer(sink=sink, service=resolved_service, guards=guards)

    # --- Auto-patch LLM clients ---
    if auto_patch:
        _auto_patch(_tracer, _budget_guard)

    _initialized = True

    # Log what we did
    sink_desc = f"dashboard ({resolved_key[:8]}...)" if resolved_key else resolved_file
    budget_desc = f"${resolved_budget:.2f}" if resolved_budget else "unlimited"
    logger.info(
        "AgentGuard initialized: service=%s sink=%s budget=%s",
        resolved_service, sink_desc, budget_desc,
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
