"""
Dashboard quickstart — connect your agent to the AgentGuard dashboard.

Sign up at https://app.agentguard47.com and grab an API key from Settings.
Then run: AG_API_KEY=ag_... python examples/dashboard_quickstart.py
"""

import os

from agentguard import Tracer, BudgetGuard, BudgetExceeded
from agentguard.sinks.http import HttpSink
from agentguard.cost import estimate_cost

api_key = os.environ.get("AG_API_KEY")
if not api_key:
    print("Set AG_API_KEY to your AgentGuard API key.")
    print("  Sign up free: https://app.agentguard47.com")
    print("  Create a key in Settings > API Keys")
    raise SystemExit(1)

# Budget guard — halts at $5, warns at 80%
budget = BudgetGuard(
    max_cost_usd=5.00,
    warn_at_pct=0.8,
    on_warning=lambda msg: print(f"  WARNING: {msg}"),
)

# Connect to the dashboard — traces, costs, and kill signals all flow here
tracer = Tracer(
    sink=HttpSink(
        url="https://app.agentguard47.com/api/ingest",
        api_key=api_key,
    ),
    service="my-agent",
    guards=[budget],
)

print("Connected to AgentGuard dashboard.")
print("Simulating agent calls with a $5.00 budget...\n")

with tracer.trace("agent.run") as span:
    for i in range(1, 50):
        try:
            with span.span("llm.completion", data={"model": "gpt-4o", "call": i}):
                # Your real LLM call goes here — we simulate cost
                cost = estimate_cost("gpt-4o", input_tokens=1000, output_tokens=500)
                budget.consume(cost_usd=cost)
            print(f"  Call {i}: ${budget.state.cost_used:.2f} spent")
        except BudgetExceeded as e:
            print(f"\n  STOPPED at call {i}: {e}")
            break

print(f"\nOpen your dashboard to see the trace:")
print(f"  https://app.agentguard47.com")
print(f"\nThe dashboard shows:")
print(f"  - Full trace timeline with every span")
print(f"  - Cost breakdown by model")
print(f"  - Budget guard events")
print(f"  - Kill switch (stop agents remotely)")
