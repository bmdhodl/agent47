"""
AgentGuard Cost Guardrail — Full Pipeline Example

Demonstrates the complete cost guardrail pipeline:
  1. BudgetGuard with $2.00 limit and 80% warning threshold
  2. patch_openai() wired with budget_guard for automatic enforcement
  3. HttpSink sending trace events to the dashboard (or JsonlFileSink for local)
  4. Simulated agent loop that burns through budget
  5. guard.budget_warning and guard.budget_exceeded events in traces

What happens:
  - Each LLM call is auto-traced with cost estimation
  - Costs are fed into BudgetGuard automatically
  - At 80% of the $2.00 limit, a guard.budget_warning event is emitted
  - When the limit is exceeded, BudgetExceeded is raised with a
    guard.budget_exceeded event in the trace

Requirements:
    pip install agentguard47 openai

Usage (local traces):
    export OPENAI_API_KEY=sk-...
    python cost_guardrail.py

Usage (dashboard):
    export OPENAI_API_KEY=sk-...
    export AGENTGUARD_API_KEY=ag_...
    python cost_guardrail.py
"""

import os
import sys

import openai

from agentguard import (
    BudgetExceeded,
    BudgetGuard,
    JsonlFileSink,
    LoopGuard,
    Tracer,
)
from agentguard.instrument import patch_openai

# --- 1. Configure the sink ---
# Use HttpSink if AGENTGUARD_API_KEY is set, otherwise local JSONL file.

api_key = os.environ.get("AGENTGUARD_API_KEY")
if api_key:
    from agentguard import HttpSink

    sink = HttpSink(
        url="https://app.agentguard47.com/api/ingest",
        api_key=api_key,
    )
    print(f"Sending traces to dashboard (key: {api_key[:8]}...)")
else:
    sink = JsonlFileSink("cost_guardrail_traces.jsonl")
    print("Sending traces to cost_guardrail_traces.jsonl")

# --- 2. Set up guards ---
# BudgetGuard: $2.00 hard limit, warning at 80% ($1.60)
# LoopGuard: catch repeated tool calls (safety net)

budget_guard = BudgetGuard(
    max_cost_usd=2.00,
    warn_at_pct=0.8,
    on_warning=lambda msg: print(f"\n  WARNING: {msg}"),
)
loop_guard = LoopGuard(max_repeats=5, window=10)

# --- 3. Create tracer with guards ---

tracer = Tracer(
    sink=sink,
    service="cost-guardrail-demo",
    guards=[loop_guard],
)

# --- 4. Wire patch_openai with budget_guard ---
# This is the key: budget_guard= auto-feeds every LLM call's cost/tokens
# into the guard. No manual consume() needed.

patch_openai(tracer, budget_guard=budget_guard)

# --- 5. Simulated agent loop ---
# A simple agent that researches a topic. Each iteration calls the LLM.
# It will eventually hit the budget limit.

client = openai.OpenAI()


def research_agent(topic: str, max_iterations: int = 50) -> str:
    """Simulated research agent that makes repeated LLM calls."""
    print(f"\nResearching: {topic}")
    print(f"Budget: ${budget_guard._max_cost_usd:.2f} (warning at 80%)")
    print("-" * 50)

    findings = []

    for i in range(1, max_iterations + 1):
        try:
            with tracer.trace(f"research.iteration.{i}") as ctx:
                # Each call is auto-traced and cost-tracked by patch_openai
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a research assistant. Give a brief 1-sentence finding."},
                        {"role": "user", "content": f"Research iteration {i} on: {topic}. Previous findings: {findings[-3:]}"},
                    ],
                    max_tokens=100,
                )
                finding = response.choices[0].message.content.strip()
                findings.append(finding)
                ctx.event("research.finding", data={"iteration": i, "finding": finding[:100]})

                # Print progress
                state = budget_guard.state
                print(f"  [{i}] ${state.cost_used:.4f} / ${budget_guard._max_cost_usd:.2f}  tokens: {state.tokens_used}  | {finding[:60]}...")

        except BudgetExceeded as e:
            # This is the cost guardrail in action!
            # The guard.budget_exceeded event was already emitted to the sink.
            print(f"\n  BUDGET EXCEEDED after {i} iterations!")
            print(f"  {e}")
            print(f"  Total cost: ${budget_guard.state.cost_used:.4f}")
            print(f"  Total tokens: {budget_guard.state.tokens_used}")
            break
    else:
        print(f"\n  Completed {max_iterations} iterations within budget.")

    return "\n".join(findings)


# --- 6. Run the agent ---

if __name__ == "__main__":
    topic = sys.argv[1] if len(sys.argv) > 1 else "the history of zero-knowledge proofs"

    try:
        result = research_agent(topic)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)

    # --- 7. Print summary ---
    print("\n" + "=" * 50)
    print("TRACE SUMMARY")
    print("=" * 50)
    state = budget_guard.state
    print(f"  Tokens used: {state.tokens_used}")
    print(f"  API calls:   {state.calls_used}")
    print(f"  Total cost:  ${state.cost_used:.4f}")

    # If using local file, show how to view the trace
    if not api_key:
        print(f"\nView trace: agentguard report cost_guardrail_traces.jsonl")
