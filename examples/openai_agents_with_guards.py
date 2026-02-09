"""
AgentGuard + OpenAI Function Calling with Guards

This example shows how to add AgentGuard to an OpenAI function-calling
agent. patch_openai() auto-traces every API call with cost tracking,
while LoopGuard and BudgetGuard prevent runaway behavior.

Requirements:
    pip install agentguard47 openai

Usage:
    export OPENAI_API_KEY=sk-...
    python openai_agents_with_guards.py
"""

import json
import openai

from agentguard import (
    Tracer,
    BudgetGuard,
    LoopGuard,
    JsonlFileSink,
    LoopDetected,
    BudgetExceeded,
)
from agentguard.instrument import patch_openai

# --- 1. Set up AgentGuard ---

tracer = Tracer(
    sink=JsonlFileSink("openai_traces.jsonl"),
    service="openai-agent",
)
budget_guard = BudgetGuard(max_cost_usd=1.00, max_calls=20)
loop_guard = LoopGuard(max_repeats=3, window=6)

# Auto-trace all OpenAI API calls with cost tracking
patch_openai(tracer)

# --- 2. Define tools ---

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The city name"},
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search documentation for an answer",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query"},
                },
                "required": ["query"],
            },
        },
    },
]


def execute_tool(name: str, args: dict) -> str:
    """Simulate tool execution. Replace with real implementations."""
    if name == "get_weather":
        return json.dumps({"city": args["city"], "temp": "72F", "condition": "sunny"})
    elif name == "search_docs":
        return json.dumps({"results": [f"Documentation about: {args['query']}"]})
    return json.dumps({"error": "Unknown tool"})


# --- 3. Agent loop with guards ---

def run_agent(user_message: str, max_turns: int = 10):
    client = openai.OpenAI()
    messages = [
        {"role": "system", "content": "You are a helpful assistant. Use tools when needed."},
        {"role": "user", "content": user_message},
    ]

    with tracer.trace("agent.run", data={"input": user_message}) as span:
        for turn in range(max_turns):
            # Check budget before each API call
            budget_guard.consume(calls=1)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            message = response.choices[0].message
            messages.append(message)

            # If no tool calls, we're done
            if not message.tool_calls:
                span.event("agent.complete", data={"turns": turn + 1})
                return message.content

            # Execute each tool call
            for tool_call in message.tool_calls:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                # Loop guard checks for repeated identical calls
                loop_guard.check(name, tool_args=args)

                with span.span(f"tool.{name}") as tool_span:
                    result = execute_tool(name, args)
                    tool_span.event("tool.result", data={"result": result})

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        span.event("agent.max_turns", data={"turns": max_turns})
        return "Agent reached maximum turns."


# --- 4. Run it ---

if __name__ == "__main__":
    try:
        answer = run_agent("What's the weather in San Francisco and New York?")
        print("\nAnswer:", answer)
    except LoopDetected as e:
        print(f"\nLoop detected: {e}")
    except BudgetExceeded as e:
        print(f"\nBudget exceeded: {e}")

    print(f"\nBudget used: ${budget_guard.state.cost_used:.4f}")
    print(f"API calls: {budget_guard.state.calls_used}")
    print("Traces saved to openai_traces.jsonl")
