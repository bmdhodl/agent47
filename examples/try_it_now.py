"""Try AgentGuard in 60 seconds — no API keys needed."""
from agentguard import BudgetGuard, BudgetExceeded

budget = BudgetGuard(max_cost_usd=1.00, warn_at_pct=0.8,
                     on_warning=lambda msg: print(f"  WARNING: {msg}"))

print("Simulating agent making LLM calls with a $1.00 budget...\n")
for i in range(1, 20):
    try:
        budget.consume(tokens=500, calls=1, cost_usd=0.12)
        print(f"  Call {i}: ${budget.state.cost_used:.2f} spent")
    except BudgetExceeded as e:
        print(f"\n  STOPPED at call {i}: {e}")
        print(f"  Total: ${budget.state.cost_used:.2f} | {budget.state.calls_used} calls")
        print("\n  Without AgentGuard, this agent would have kept spending.")
        break
