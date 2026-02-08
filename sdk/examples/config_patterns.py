"""Dev vs Prod configuration patterns for AgentGuard.

Dev:  JsonlFileSink, all guards, full sampling, verbose warnings
Prod: HttpSink, essential guards, 10% sampling, alert callback

Usage:
    PYTHONPATH=sdk AGENTGUARD_ENV=dev python examples/config_patterns.py
    PYTHONPATH=sdk AGENTGUARD_ENV=prod AGENTGUARD_API_KEY=ag_... python examples/config_patterns.py
"""
from __future__ import annotations

import os

from agentguard import (
    Tracer,
    JsonlFileSink,
    LoopGuard,
    FuzzyLoopGuard,
    BudgetGuard,
    TimeoutGuard,
    RateLimitGuard,
)
from agentguard.sinks.http import HttpSink


def create_tracer(env: str = None) -> Tracer:
    """Factory: build a Tracer configured for the given environment."""
    env = env or os.environ.get("AGENTGUARD_ENV", "dev")
    if env == "prod":
        return _prod_tracer()
    return _dev_tracer()


def _dev_tracer() -> Tracer:
    """Dev: local file, all guards, full sampling."""
    return Tracer(
        sink=JsonlFileSink("traces.jsonl"),
        service=os.environ.get("SERVICE_NAME", "my-agent"),
        guards=[
            LoopGuard(max_repeats=3, window=6),
            FuzzyLoopGuard(max_tool_repeats=5, max_alternations=3),
            BudgetGuard(
                max_cost_usd=5.00,
                max_calls=100,
                warn_at_pct=0.7,
                on_warning=lambda msg: print(f"[DEV WARNING] {msg}"),
            ),
            RateLimitGuard(max_calls_per_minute=120),
            # TimeoutGuard requires .start() — use it explicitly per-trace
        ],
        metadata={
            "env": "dev",
            "git_sha": os.environ.get("GIT_SHA", "local"),
        },
        sampling_rate=1.0,
    )


def _prod_tracer() -> Tracer:
    """Prod: HTTP sink, essential guards, 10% sampling."""
    api_key = os.environ.get("AGENTGUARD_API_KEY")
    if not api_key:
        raise ValueError("Set AGENTGUARD_API_KEY for prod mode")

    return Tracer(
        sink=HttpSink(
            url=os.environ.get("AGENTGUARD_URL", "https://app.agentguard47.com/api/ingest"),
            api_key=api_key,
            batch_size=20,
            flush_interval=10.0,
            compress=True,
        ),
        service=os.environ.get("SERVICE_NAME", "my-agent"),
        guards=[
            LoopGuard(max_repeats=5, window=10),
            BudgetGuard(
                max_cost_usd=50.00,
                warn_at_pct=0.8,
                on_warning=lambda msg: print(f"[PROD ALERT] {msg}"),
            ),
        ],
        metadata={
            "env": "prod",
            "git_sha": os.environ.get("GIT_SHA", "unknown"),
            "region": os.environ.get("REGION", "us-east-1"),
        },
        sampling_rate=0.1,
    )


if __name__ == "__main__":
    env = os.environ.get("AGENTGUARD_ENV", "dev")
    print(f"Creating tracer for env={env}")

    if env == "prod" and not os.environ.get("AGENTGUARD_API_KEY"):
        print("Skipping prod (no AGENTGUARD_API_KEY). Set it to test prod mode.")
        raise SystemExit(0)

    tracer = create_tracer(env)
    print(f"Tracer: {tracer}")

    with tracer.trace("demo.config_pattern") as ctx:
        ctx.event("reasoning.step", data={"thought": f"running in {env} mode"})
        ctx.event("llm.result", data={"model": "gpt-4o", "cost_usd": 0.001})
        print(f"  Traced demo in {env} mode")

    if env == "dev":
        print("  Traces written to traces.jsonl")
        # Cleanup
        if os.path.exists("traces.jsonl"):
            os.remove("traces.jsonl")

    print("Done")
