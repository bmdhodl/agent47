"""
AgentGuard + OpenAI Agents SDK

This example requires the unpublished AgentGuard 2.0.0 candidate. See
docs/integrations/openai-responses.md for the tested versions and installation.
agentguard.init() instruments the standard OpenAIResponsesModel client path.
Its model calls are checked before dispatch and charged from reported usage.
The SDK's own max_turns still applies; whichever limit trips first stops the run.
In 2.0.0, standard clients created before activation are covered. Activate before
dispatch and stream-helper construction. Previously saved bound callables,
custom resource overrides and custom model transports can bypass the patch.

Tool calls and handoffs are not guard points. The model call each one leads to is.

This example makes real provider calls. The integration tests use fake transport
with no credentials or paid calls; custom model transports are outside this path.

Usage:
    export OPENAI_API_KEY=sk-...
    python openai_agents_sdk_budget.py
    agentguard receipt agents_traces.jsonl
"""

import agentguard
from agentguard import BudgetExceeded
from agents import Agent, MaxTurnsExceeded, Runner, function_tool

# Activate before dispatch and before creating stream helpers. Standard clients
# created earlier are covered; saved callables and custom transports may bypass it.
agentguard.init(budget_usd=0.05, trace_file="agents_traces.jsonl", service="agents-sdk")

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
