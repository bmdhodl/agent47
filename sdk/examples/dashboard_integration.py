"""dashboard_integration.py — Full SDK-to-dashboard flow.

Demonstrates the complete pipeline: trace an agent, send events to the
AgentGuard dashboard via HttpSink, then use the CLI to generate a local
report.

Setup:
  pip install agentguard47
  # Get your API key from https://app.agentguard47.com

Run:
  export AGENTGUARD_API_KEY=ag_...
  python dashboard_integration.py

Or use the one-liner init():
  AGENTGUARD_API_KEY=ag_... python dashboard_integration.py
"""
from __future__ import annotations

import os
import sys
import time

# --- Method 1: One-liner init (recommended) ---

def run_with_init():
    """Use agentguard.init() for zero-config setup."""
    import agentguard

    # init() reads AGENTGUARD_API_KEY from env, sets up HttpSink,
    # auto-patches OpenAI/Anthropic, creates LoopGuard + BudgetGuard.
    tracer = agentguard.init(
        service="dashboard-demo",
        budget_usd=1.00,
    )

    with tracer.trace("agent.dashboard_demo") as ctx:
        ctx.event("reasoning.step", data={"thought": "planning research"})

        with ctx.span("tool.search", data={"query": "AgentGuard features"}):
            ctx.event("tool.result", data={"result": "found 5 features"})

        ctx.event("reasoning.step", data={"thought": "summarizing"})

        with ctx.span("tool.summarize"):
            ctx.event("tool.result", data={"summary": "AgentGuard provides runtime guards"})
            ctx.cost.add("gpt-4o-mini", input_tokens=500, output_tokens=200)

        ctx.event("agent.complete", data={"answer": "Summary written"})

    # Clean shutdown — flushes pending events to dashboard
    agentguard.shutdown()
    return tracer


# --- Method 2: Manual setup (more control) ---

def run_with_manual_setup():
    """Manual Tracer + HttpSink for full control."""
    from agentguard import Tracer, LoopGuard, BudgetGuard, JsonlFileSink
    from agentguard.sinks.http import HttpSink

    api_key = os.environ.get("AGENTGUARD_API_KEY")
    here = os.path.dirname(os.path.abspath(__file__))

    # Dual sink: local file + dashboard
    local_sink = JsonlFileSink(os.path.join(here, "dashboard_traces.jsonl"))

    if api_key:
        http_sink = HttpSink(
            url="https://app.agentguard47.com/api/ingest",
            api_key=api_key,
        )
        # Use a simple multiplexer to send to both
        class DualSink:
            def emit(self, event):
                local_sink.emit(event)
                http_sink.emit(event)
            def shutdown(self):
                http_sink.shutdown()
        sink = DualSink()
    else:
        sink = local_sink

    tracer = Tracer(
        sink=sink,
        service="dashboard-demo",
        guards=[
            LoopGuard(max_repeats=5),
            BudgetGuard(max_cost_usd=1.00),
        ],
        metadata={"env": "demo", "version": "1.0"},
    )

    with tracer.trace("agent.manual_demo") as ctx:
        ctx.event("reasoning.step", data={"thought": "planning"})
        with ctx.span("tool.search"):
            ctx.event("tool.result", data={"result": "found data"})
        ctx.event("agent.complete", data={"answer": "Done"})

    if hasattr(sink, "shutdown"):
        sink.shutdown()

    print(f"  Local trace: {here}/dashboard_traces.jsonl")
    return tracer


# --- CLI report ---

def show_report():
    """Generate a report from the local trace file."""
    here = os.path.dirname(os.path.abspath(__file__))
    trace_file = os.path.join(here, "dashboard_traces.jsonl")

    if not os.path.exists(trace_file):
        print("  No local trace file found.")
        return

    from agentguard.cli import _report
    print("\n--- CLI Report ---")
    _report(trace_file)


if __name__ == "__main__":
    api_key = os.environ.get("AGENTGUARD_API_KEY")

    print("=== AgentGuard Dashboard Integration ===\n")

    if api_key:
        print(f"  API key: {api_key[:8]}...")
        print("  Using init() → HttpSink → Dashboard\n")
        run_with_init()
        print("  Events sent to dashboard!")
    else:
        print("  No AGENTGUARD_API_KEY set.")
        print("  Using manual setup → local JSONL only\n")
        run_with_manual_setup()

    time.sleep(1)  # Allow async flush
    show_report()

    print("\n--- Next Steps ---")
    if api_key:
        print("  1. Open https://app.agentguard47.com to see your traces")
        print("  2. Run: agentguard report dashboard_traces.jsonl")
    else:
        print("  1. Get an API key: https://app.agentguard47.com")
        print("  2. Re-run with: AGENTGUARD_API_KEY=ag_... python dashboard_integration.py")
        print("  3. Or view locally: agentguard report dashboard_traces.jsonl")
