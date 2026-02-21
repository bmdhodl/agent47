"""crewai_example.py — Trace a CrewAI crew with AgentGuard.

CrewAI is built on LangChain, so our LangChain callback handler works
out of the box. This example shows how to wire it up.

Setup:
  pip install agentguard47[langchain] crewai crewai-tools

Run:
  export OPENAI_API_KEY=sk-...       # CrewAI uses OpenAI by default
  export AGENTGUARD_KEY=ag_...       # Optional: stream to dashboard
  python crewai_example.py
"""
from __future__ import annotations

import os

# --- AgentGuard setup (do this BEFORE importing CrewAI) ---
from agentguard import Tracer, LoopGuard, BudgetGuard
from agentguard.tracing import JsonlFileSink
from agentguard.integrations.langchain import AgentGuardCallbackHandler

# Sinks: local file + optional dashboard
sinks = []
here = os.path.dirname(os.path.abspath(__file__))
local_sink = JsonlFileSink(os.path.join(here, "crewai_traces.jsonl"))

dashboard_key = os.environ.get("AGENTGUARD_KEY")
if dashboard_key:
    from agentguard.sinks.http import HttpSink
    url = os.environ.get("AGENTGUARD_URL", "https://app.agentguard47.com/api/ingest")
    http_sink = HttpSink(url=url, api_key=dashboard_key)
    # Use a multiplex sink if you have both
    from dev_agent import MultiplexSink
    sink = MultiplexSink([local_sink, http_sink])
    print("[agentguard] Tracing → dashboard + crewai_traces.jsonl")
else:
    sink = local_sink
    print("[agentguard] Tracing → crewai_traces.jsonl")

tracer = Tracer(sink=sink, service="crewai-demo")
guard = LoopGuard(max_repeats=5)
budget = BudgetGuard(max_tokens=100_000, max_calls=50)

# The callback handler that bridges CrewAI → AgentGuard
handler = AgentGuardCallbackHandler(
    tracer=tracer,
    loop_guard=guard,
    budget_guard=budget,
)

# --- CrewAI setup ---
try:
    from crewai import Agent, Task, Crew
except ImportError:
    print("Install CrewAI first: pip install crewai crewai-tools")
    raise SystemExit(1)


researcher = Agent(
    role="Senior Research Analyst",
    goal="Find and summarize key information about agent observability",
    backstory="You're an expert at analyzing developer tools and agent frameworks.",
    verbose=True,
    callbacks=[handler],  # <-- AgentGuard traces every step
)

writer = Agent(
    role="Technical Writer",
    goal="Write a concise summary of the research findings",
    backstory="You turn complex technical research into clear, actionable prose.",
    verbose=True,
    callbacks=[handler],  # <-- AgentGuard traces every step
)

research_task = Task(
    description="Research the current state of observability tools for AI agents. "
    "What tools exist? What are the gaps? Focus on tracing, loop detection, and cost control.",
    expected_output="A bullet-point summary of findings with at least 5 key insights.",
    agent=researcher,
)

write_task = Task(
    description="Based on the research, write a 200-word summary explaining why "
    "agent observability matters and what the ideal solution looks like.",
    expected_output="A clear 200-word summary suitable for a blog post intro.",
    agent=writer,
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    verbose=True,
)

if __name__ == "__main__":
    print("[crewai] Starting crew...\n")
    result = crew.kickoff()
    print("\n" + "=" * 60)
    print(result)
    print("=" * 60)
    print(f"\n[agentguard] Trace saved. Run: agentguard report {here}/crewai_traces.jsonl")
