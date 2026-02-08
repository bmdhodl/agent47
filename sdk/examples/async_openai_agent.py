"""Example: async OpenAI agent with AgentGuard tracing and budget guard.

Requires: pip install openai agentguard47

Usage:
    export OPENAI_API_KEY=sk-...
    python async_openai_agent.py
"""
import asyncio

from agentguard import (
    AsyncTracer,
    BudgetGuard,
    JsonlFileSink,
    LoopGuard,
    patch_openai_async,
)
from agentguard.instrument import async_trace_agent, async_trace_tool

# Set up tracing with guards
sink = JsonlFileSink("async_traces.jsonl")
tracer = AsyncTracer(
    sink=sink,
    service="async-agent",
    guards=[
        LoopGuard(max_repeats=3),
        BudgetGuard(max_cost_usd=1.00),
    ],
)

# Patch async OpenAI client (safe if openai not installed)
patch_openai_async(tracer)


@async_trace_tool(tracer)
async def search(query: str) -> str:
    """Simulated async search tool."""
    await asyncio.sleep(0.01)
    return f"Results for: {query}"


@async_trace_agent(tracer)
async def agent(query: str) -> str:
    """Simple async agent that searches and responds."""
    results = await search(query)
    return f"Based on search: {results}"


async def main():
    result = await agent("how to detect agent loops")
    print(result)
    print("\nTrace written to async_traces.jsonl")
    print("Run: agentguard view async_traces.jsonl")


if __name__ == "__main__":
    asyncio.run(main())
