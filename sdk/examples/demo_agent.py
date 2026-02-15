"""Minimal end-to-end demo that produces traces.jsonl.

Run:
  python demo_agent.py
  agentguard summarize traces.jsonl
"""

from __future__ import annotations

from typing import Dict

from agentguard.guards import BudgetGuard, LoopDetected, LoopGuard
from agentguard.tracing import JsonlFileSink, Tracer

HERE = __file__.rsplit("/", 1)[0]
TRACES_PATH = f"{HERE}/traces.jsonl"


def fake_search(query: str) -> Dict[str, str]:
    return {"result": f"Found info about: {query}"}


def fake_llm(prompt: str) -> Dict[str, str]:
    return {"text": f"Answering: {prompt}"}


def run_agent() -> None:
    tracer = Tracer(sink=JsonlFileSink(TRACES_PATH), service="demo")
    loop_guard = LoopGuard(max_repeats=3, window=5)
    budget = BudgetGuard(max_calls=10)

    with tracer.trace("agent.run", data={"mode": "demo"}) as span:
        prompt = "Explain why agents loop"
        span.event("reasoning.step", data={"step": 1, "thought": "search docs"})

        loop_guard.check("search", {"query": "agent loop causes"})
        budget.consume(calls=1)
        search_result = fake_search("agent loop causes")
        span.event("tool.result", data=search_result)

        span.event("reasoning.step", data={"step": 2, "thought": "draft response"})
        budget.consume(calls=1)
        llm_result = fake_llm(prompt)
        span.event("llm.result", data=llm_result)

        # Demonstrate loop detection
        try:
            for _ in range(3):
                loop_guard.check("search", {"query": "agent loop causes"})
        except LoopDetected as exc:
            span.event("guard.loop_detected", data={"error": str(exc)})


if __name__ == "__main__":
    run_agent()
