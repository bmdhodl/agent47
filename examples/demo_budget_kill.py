#!/usr/bin/env python3
"""
AgentGuard Demo: BudgetGuard kills a runaway agent

This demo requires NO API keys — it simulates an autonomous research agent
that makes repeated LLM calls, burning through a $1.00 budget. AgentGuard's
BudgetGuard stops the agent mid-run when the budget is exceeded.

Usage:
    python demo_budget_kill.py

What you'll see:
    1. Agent starts researching with a $1.00 budget
    2. Each "LLM call" adds realistic cost ($0.05-0.12 per call)
    3. At 80% ($0.80) → WARNING fires
    4. At 100% ($1.00) → BudgetExceeded raised, agent killed
"""

import sys
import time

from agentguard import (
    BudgetExceeded,
    BudgetGuard,
    JsonlFileSink,
    LoopGuard,
    Tracer,
)

# ANSI colors for terminal output
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"

# Simulated LLM responses and costs (realistic GPT-4o pricing)
AGENT_STEPS = [
    {"action": "Planning research strategy", "model": "gpt-4o", "input_tokens": 850, "output_tokens": 320, "cost": 0.054},
    {"action": "Searching knowledge base", "model": "gpt-4o", "input_tokens": 1200, "output_tokens": 450, "cost": 0.078},
    {"action": "Analyzing search results", "model": "gpt-4o", "input_tokens": 2100, "output_tokens": 380, "cost": 0.089},
    {"action": "Generating follow-up queries", "model": "gpt-4o", "input_tokens": 1800, "output_tokens": 520, "cost": 0.095},
    {"action": "Deep-diving into subtopic", "model": "gpt-4o", "input_tokens": 2400, "output_tokens": 610, "cost": 0.112},
    {"action": "Cross-referencing sources", "model": "gpt-4o", "input_tokens": 1950, "output_tokens": 480, "cost": 0.098},
    {"action": "Synthesizing findings", "model": "gpt-4o", "input_tokens": 2800, "output_tokens": 720, "cost": 0.126},
    {"action": "Expanding research scope", "model": "gpt-4o", "input_tokens": 3100, "output_tokens": 850, "cost": 0.141},
    {"action": "Verifying claims", "model": "gpt-4o", "input_tokens": 2200, "output_tokens": 390, "cost": 0.093},
    {"action": "Writing draft section", "model": "gpt-4o", "input_tokens": 3500, "output_tokens": 1200, "cost": 0.168},
]


def cost_bar(used: float, limit: float, width: int = 20) -> str:
    """Render a progress bar for budget usage."""
    pct = min(used / limit, 1.0)
    filled = int(width * pct)
    empty = width - filled

    if pct >= 1.0:
        color = RED
    elif pct >= 0.8:
        color = YELLOW
    else:
        color = GREEN

    bar = f"{color}{'█' * filled}{'░' * empty}{RESET}"
    return f"[{bar}] ${used:.2f}/${limit:.2f}"


def main():
    print()
    print(f"{BOLD}AgentGuard Demo: BudgetGuard kills a runaway agent{RESET}")
    print(f"{DIM}{'─' * 55}{RESET}")
    print()

    # --- Set up AgentGuard ---
    budget = BudgetGuard(
        max_cost_usd=1.00,
        warn_at_pct=0.8,
        on_warning=lambda msg: print(
            f"\n  {YELLOW}{BOLD}⚠ WARNING:{RESET}{YELLOW} {msg}{RESET}\n"
        ),
    )

    tracer = Tracer(
        sink=JsonlFileSink("demo_traces.jsonl"),
        service="research-agent",
        guards=[LoopGuard(max_repeats=10, window=20)],
    )

    print(f"  Agent:  {CYAN}Autonomous Research Agent{RESET}")
    print(f"  Budget: {GREEN}$1.00{RESET} (warning at 80%)")
    print(f"  Task:   Research quantum computing breakthroughs")
    print()
    time.sleep(1.0)

    # --- Run the agent ---
    for i, step in enumerate(AGENT_STEPS, 1):
        try:
            with tracer.trace(f"step.{i}") as ctx:
                # Simulate LLM call with delay
                action = step["action"]
                print(f"  {DIM}[{i:2d}]{RESET} {action}...", end="", flush=True)
                time.sleep(0.8)

                # Feed cost into BudgetGuard
                budget.consume(
                    tokens=step["input_tokens"] + step["output_tokens"],
                    calls=1,
                    cost_usd=step["cost"],
                )

                state = budget.state
                bar = cost_bar(state.cost_used, 1.00)
                print(f"\r  {DIM}[{i:2d}]{RESET} {action:<35s} {bar}")

                ctx.event("llm.call", data={
                    "model": step["model"],
                    "cost_usd": step["cost"],
                    "tokens": step["input_tokens"] + step["output_tokens"],
                })

        except BudgetExceeded as e:
            # The kill shot
            print(f"\r  {DIM}[{i:2d}]{RESET} {step['action']:<35s} {cost_bar(budget.state.cost_used, 1.00)}")
            print()
            print(f"  {RED}{BOLD}✗ BUDGET EXCEEDED — AGENT KILLED{RESET}")
            print(f"  {RED}{e}{RESET}")
            print()

            state = budget.state
            print(f"  {BOLD}Final state:{RESET}")
            print(f"    Total cost:   {RED}${state.cost_used:.2f}{RESET} (limit: $1.00)")
            print(f"    Total tokens: {state.tokens_used:,}")
            print(f"    API calls:    {state.calls_used}")
            print(f"    Stopped at:   step {i} of {len(AGENT_STEPS)}")
            print()
            print(f"  {GREEN}Without AgentGuard, this agent would have kept spending.{RESET}")
            print()
            return 1

    print()
    print(f"  {GREEN}Agent completed within budget.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
