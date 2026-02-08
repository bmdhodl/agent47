"""
AgentGuard + CrewAI Multi-Agent with Tracing and Guards

This example shows how to add AgentGuard observability to a CrewAI
multi-agent workflow. Each agent and task gets traced, and budget
limits prevent runaway costs across the entire crew.

Requirements:
    pip install agentguard47 crewai crewai-tools

Usage:
    export OPENAI_API_KEY=sk-...
    python crewai_with_guards.py
"""

from crewai import Agent, Task, Crew

from agentguard import (
    Tracer,
    BudgetGuard,
    LoopGuard,
    JsonlFileSink,
    trace_agent,
    trace_tool,
)
from agentguard.instrument import patch_openai

# --- 1. Set up AgentGuard ---

tracer = Tracer(
    sink=JsonlFileSink("crewai_traces.jsonl"),
    service="crewai-demo",
)
budget_guard = BudgetGuard(max_cost_usd=5.00, max_calls=100)
loop_guard = LoopGuard(max_repeats=3, window=6)

# Auto-trace all OpenAI calls (CrewAI uses OpenAI under the hood)
patch_openai(tracer)

# --- 2. Define CrewAI agents ---

researcher = Agent(
    role="Research Analyst",
    goal="Find key information about AI agent observability trends",
    backstory="You are an expert at analyzing technology trends in AI.",
    verbose=True,
    allow_delegation=False,
)

writer = Agent(
    role="Technical Writer",
    goal="Write a concise summary of the research findings",
    backstory="You turn complex technical topics into clear, readable content.",
    verbose=True,
    allow_delegation=False,
)

# --- 3. Define tasks ---

research_task = Task(
    description=(
        "Research the current state of AI agent observability. "
        "Focus on: What tools exist? What problems do developers face? "
        "What's missing from current solutions?"
    ),
    expected_output="A bullet-point list of key findings about AI agent observability.",
    agent=researcher,
)

writing_task = Task(
    description=(
        "Using the research findings, write a 3-paragraph summary "
        "about the state of AI agent observability and where the "
        "industry is headed."
    ),
    expected_output="A 3-paragraph technical summary.",
    agent=writer,
)

# --- 4. Run the crew with AgentGuard watching ---

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, writing_task],
    verbose=True,
)

if __name__ == "__main__":
    with tracer.trace("crew.kickoff") as span:
        try:
            # Check budget before each major step
            budget_guard.consume(calls=1)

            result = crew.kickoff()

            span.event("crew.complete", data={"output_length": len(str(result))})
            print("\n--- Crew Output ---")
            print(result)

        except Exception as e:
            span.event("crew.error", data={"error": str(e)})
            print(f"\nCrew stopped: {e}")

    print(f"\nBudget used: ${budget_guard.state.cost_used:.4f}")
    print(f"API calls: {budget_guard.state.calls_used}")
    print("Traces saved to crewai_traces.jsonl")
