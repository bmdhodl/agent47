"""
AgentGuard + OpenAI Agents SDK

agentguard.init() patches AsyncOpenAI before the Agents SDK builds its client.
Every model call the Runner makes goes through responses.create, so the budget
is checked before each call is sent and charged from its usage after it returns.
The SDK's own max_turns still applies; whichever limit trips first stops the run.

Tool calls and handoffs are not guard points. The model call each one leads to is.

Requirements:
    pip install agentguard47 openai-agents

Usage:
    export OPENAI_API_KEY=sk-...
    python openai_agents_sdk_budget.py
    agentguard receipt agents_traces.jsonl
"""

import agentguard

# Patch first: a client created before init() is not patched.
agentguard.init(budget_usd=0.05, trace_file="agents_traces.jsonl", service="agents-sdk")

from agents import Agent, MaxTurnsExceeded, Runner, function_tool  # noqa: E402

from agentguard import BudgetExceeded  # noqa: E402


@function_tool
def search_docs(query: str) -> str:
    """Search the docs. Returns nothing useful, so a weak model may keep asking."""
    return "No results."


agent = Agent(
    name="researcher",
    instructions="Answer the question. Use search_docs if you need to.",
    model="gpt-4o-mini",
    tools=[search_docs],
)

if __name__ == "__main__":
    try:
        result = Runner.run_sync(agent, "What does AgentGuard's LoopGuard do?", max_turns=8)
        print("Answer:", result.final_output)
    except BudgetExceeded as exc:
        print("AgentGuard stopped the run:", exc)
    except MaxTurnsExceeded as exc:
        print("The Agents SDK stopped the run at max_turns:", exc)
    finally:
        guard = agentguard.get_budget_guard()
        print(f"Recorded ${guard.state.cost_used:.4f} over {guard.state.calls_used} model calls")
        agentguard.shutdown()
