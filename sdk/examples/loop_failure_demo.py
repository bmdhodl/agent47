"""Demonstrates how an AI agent can silently loop on tool calls — and how
AgentGuard detects it.

Run:
    python3 sdk/examples/loop_failure_demo.py

Then inspect the traces:
    agentguard report sdk/examples/loop_traces.jsonl
    agentguard view sdk/examples/loop_traces.jsonl
"""

from agentguard.tracing import Tracer, JsonlFileSink
from agentguard.guards import LoopGuard, LoopDetected
import os

TRACE_FILE = os.path.join(os.path.dirname(__file__), "loop_traces.jsonl")

# Remove stale traces
if os.path.exists(TRACE_FILE):
    os.remove(TRACE_FILE)

tracer = Tracer(sink=JsonlFileSink(TRACE_FILE), service="loop-demo")
guard = LoopGuard(max_repeats=3, window=5)


def fake_search(query: str) -> str:
    """Simulates a search tool that always returns unhelpful results."""
    return f"No relevant results for '{query}'"


def agent_loop():
    """A naive ReAct-style agent that keeps retrying the same search."""
    question = "What is the capital of the lost city of Atlantis?"

    with tracer.trace("agent.run", data={"question": question}) as span:
        for step in range(10):
            span.event("reasoning.step", data={
                "step": step + 1,
                "thought": f"I should search for the answer to: {question}",
            })

            tool_name = "search"
            tool_args = {"query": question}

            try:
                guard.check(tool_name=tool_name, tool_args=tool_args)
            except LoopDetected as e:
                span.event("guard.loop_detected", data={"error": str(e)})
                print(f"[step {step + 1}] Loop detected! {e}")
                return

            with span.span("tool.call", data={"tool": tool_name, **tool_args}):
                result = fake_search(question)
                span.event("tool.result", data={"output": result})
                print(f"[step {step + 1}] search -> {result}")


if __name__ == "__main__":
    print("Running loop failure demo...\n")
    agent_loop()
    print(f"\nTraces written to {TRACE_FILE}")
    print("Run: agentguard report sdk/examples/loop_traces.jsonl")
