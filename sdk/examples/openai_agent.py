"""openai_agent.py — Trace an OpenAI function-calling agent with AgentGuard.

The simplest possible agent: OpenAI + tools + a loop. AgentGuard traces
every step so you can see exactly what happened.

Setup:
  pip install agentguard47 openai

Run:
  export OPENAI_API_KEY=sk-...
  python openai_agent.py "What's the weather in Tokyo and NYC?"
"""
from __future__ import annotations

import json
import os
import sys
import time

from agentguard import Tracer, LoopGuard, BudgetGuard
from agentguard.tracing import JsonlFileSink
from agentguard.instrument import patch_openai

try:
    import openai
except ImportError:
    print("Install openai first: pip install openai")
    raise SystemExit(1)

# --- Tracing setup ---
here = os.path.dirname(os.path.abspath(__file__))
sink = JsonlFileSink(os.path.join(here, "openai_traces.jsonl"))

dashboard_key = os.environ.get("AGENTGUARD_KEY")
if dashboard_key:
    from agentguard.sinks.http import HttpSink
    from dev_agent import MultiplexSink
    url = os.environ.get("AGENTGUARD_URL", "https://dashboard-brown-pi-97.vercel.app/api/ingest")
    sink = MultiplexSink([sink, HttpSink(url=url, api_key=dashboard_key)])

tracer = Tracer(sink=sink, service="openai-agent")
loop_guard = LoopGuard(max_repeats=3)
budget = BudgetGuard(max_tokens=50_000, max_calls=20)

# Auto-instrument OpenAI — all completions.create calls get traced
patch_openai(tracer)

# --- Fake tools (replace with real ones) ---
def get_weather(city: str) -> str:
    """Fake weather lookup."""
    weather = {"tokyo": "72F, sunny", "nyc": "58F, cloudy", "london": "52F, rainy"}
    return weather.get(city.lower(), f"Unknown city: {city}")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    }
]

TOOL_MAP = {"get_weather": get_weather}


# --- Agent loop ---
def run(task: str) -> str:
    client = openai.OpenAI()
    messages = [{"role": "user", "content": task}]

    with tracer.trace("agent.openai_demo", data={"task": task}) as ctx:
        for step in range(10):
            ctx.event("reasoning.step", data={"step": step + 1})
            budget.consume(calls=1)

            # LLM call (auto-traced by patch_openai)
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS,
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                ctx.event("agent.complete", data={"answer": msg.content[:500]})
                return msg.content or ""

            messages.append(msg)

            for call in msg.tool_calls:
                fn_name = call.function.name
                fn_args = json.loads(call.function.arguments)

                loop_guard.check(fn_name, fn_args)

                with ctx.span(f"tool.{fn_name}", data=fn_args):
                    result = TOOL_MAP[fn_name](**fn_args)
                    ctx.event("tool.result", data={"result": result})

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })

    return "Max steps reached"


if __name__ == "__main__":
    task = " ".join(sys.argv[1:]) or "What's the weather in Tokyo and NYC?"
    print(f"[agent] {task}\n")
    answer = run(task)
    print(f"\n{answer}")
    time.sleep(2)  # flush HttpSink
    print(f"\n[agentguard] Trace saved: {here}/openai_traces.jsonl")
