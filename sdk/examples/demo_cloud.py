"""Demo agent that sends traces to the hosted dashboard via HttpSink.

Usage:
  python demo_cloud.py <url> <api_key>

Example:
  python demo_cloud.py http://localhost:3000/api/ingest ag_your_key_here
"""

from __future__ import annotations

import sys
from typing import Dict

from agentguard.guards import BudgetGuard, LoopDetected, LoopGuard
from agentguard.sinks.http import HttpSink
from agentguard.tracing import Tracer


def fake_search(query: str) -> Dict[str, str]:
    return {"result": f"Found info about: {query}"}


def fake_llm(prompt: str) -> Dict[str, str]:
    return {"text": f"Answering: {prompt}"}


def run_agent(url: str, api_key: str) -> None:
    sink = HttpSink(url=url, api_key=api_key, batch_size=50, flush_interval=1.0)
    tracer = Tracer(sink=sink, service="demo-cloud")

    with tracer.trace("agent.run", data={"mode": "cloud-demo"}) as span:
        prompt = "Explain why agents loop"
        span.event("reasoning.step", data={"step": 1, "thought": "search docs"})

        with span.span("tool.search") as tool_span:
            search_result = fake_search("agent loop causes")
            tool_span.event("tool.result", data=search_result)

        span.event("reasoning.step", data={"step": 2, "thought": "draft response"})

        with span.span("llm.generate") as llm_span:
            llm_result = fake_llm(prompt)
            llm_span.event("llm.result", data=llm_result)

        span.event("reasoning.step", data={"step": 3, "thought": "review and guard"})

        # Demonstrate loop detection
        loop_guard = LoopGuard(max_repeats=3, window=5)
        budget = BudgetGuard(max_calls=10)

        with span.span("guard.check") as guard_span:
            try:
                for i in range(4):
                    loop_guard.check("search", {"query": "agent loop causes"})
                    budget.consume(calls=1)
            except LoopDetected as exc:
                guard_span.event("guard.loop_detected", data={"error": str(exc)})

    sink.shutdown()
    print("Traces sent to dashboard!")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: python {sys.argv[0]} <url> <api_key>")
        sys.exit(1)

    run_agent(sys.argv[1], sys.argv[2])
