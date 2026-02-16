"""multi_agent_budget_sharing.py — Shared budget across multiple agents.

Demonstrates a team of agents that share a single BudgetGuard. When any
agent pushes the team over budget, all agents stop. Each agent runs in
its own thread with its own trace.

Setup:
  pip install agentguard47

Run:
  python multi_agent_budget_sharing.py
"""
from __future__ import annotations

import os
import threading
import time

from agentguard import (
    BudgetExceeded,
    BudgetGuard,
    JsonlFileSink,
    LoopGuard,
    Tracer,
)

here = os.path.dirname(os.path.abspath(__file__))

# --- Shared budget for the entire team ---
team_budget = BudgetGuard(
    max_cost_usd=0.10,
    max_calls=50,
    warn_at_pct=0.8,
    on_warning=lambda msg: print(f"  [WARNING] {msg}"),
)

tracer = Tracer(
    sink=JsonlFileSink(os.path.join(here, "multi_agent_traces.jsonl")),
    service="agent-team",
    guards=[LoopGuard(max_repeats=10)],
)


# --- Simulated agents ---

def researcher_agent(task: str) -> str:
    """Researcher: makes many small LLM calls to gather info."""
    with tracer.trace("agent.researcher", data={"task": task}) as ctx:
        findings = []
        for i in range(8):
            try:
                team_budget.consume(calls=1, cost_usd=0.005)
            except BudgetExceeded as e:
                ctx.event("guard.budget_exceeded", data={"step": i, "error": str(e)})
                return f"STOPPED at step {i}: {e}"
            ctx.event("research.step", data={"step": i, "source": f"doc_{i}"})
            findings.append(f"finding_{i}")
            time.sleep(0.05)
        return f"Found {len(findings)} items"


def writer_agent(research: str) -> str:
    """Writer: takes research and produces output."""
    with tracer.trace("agent.writer", data={"research": research[:100]}) as ctx:
        for i in range(5):
            try:
                team_budget.consume(calls=1, cost_usd=0.01)
            except BudgetExceeded as e:
                ctx.event("guard.budget_exceeded", data={"step": i, "error": str(e)})
                return f"STOPPED at step {i}: {e}"
            ctx.event("writing.step", data={"step": i, "section": f"section_{i}"})
            time.sleep(0.05)
        return "Article complete"


def reviewer_agent(draft: str) -> str:
    """Reviewer: checks quality and suggests edits."""
    with tracer.trace("agent.reviewer", data={"draft": draft[:100]}) as ctx:
        for i in range(3):
            try:
                team_budget.consume(calls=1, cost_usd=0.008)
            except BudgetExceeded as e:
                ctx.event("guard.budget_exceeded", data={"step": i, "error": str(e)})
                return f"STOPPED at step {i}: {e}"
            ctx.event("review.step", data={"step": i, "feedback": f"edit_{i}"})
            time.sleep(0.05)
        return "Review complete"


# --- Run the team ---

def run_team():
    print("=== Multi-Agent Team with Shared Budget ===")
    print(f"  Budget: ${team_budget.max_cost_usd:.2f}, {team_budget.max_calls} calls")
    print()

    results = {}

    def run_agent(name, fn, *args):
        try:
            results[name] = fn(*args)
        except BudgetExceeded as e:
            results[name] = f"BUDGET EXCEEDED: {e}"

    # Run researcher and writer in parallel, reviewer after
    t1 = threading.Thread(target=run_agent, args=("researcher", researcher_agent, "AI safety"))
    t2 = threading.Thread(target=run_agent, args=("writer", writer_agent, "placeholder research"))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Reviewer runs after
    run_agent("reviewer", reviewer_agent, "placeholder draft")

    print("Results:")
    for name, result in results.items():
        print(f"  {name}: {result}")

    print()
    print(f"Budget used: ${team_budget.state.cost_used:.4f} / ${team_budget.max_cost_usd:.2f}")
    print(f"Calls used:  {team_budget.state.calls_used} / {team_budget.max_calls}")
    print(f"\nTrace saved: {here}/multi_agent_traces.jsonl")
    print("Run: agentguard report multi_agent_traces.jsonl")


if __name__ == "__main__":
    run_team()
