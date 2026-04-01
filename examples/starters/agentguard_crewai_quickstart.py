from __future__ import annotations

import os

from agentguard import BudgetGuard, JsonlFileSink, LoopGuard, Tracer
from agentguard.integrations.crewai import AgentGuardCrewHandler


def main() -> None:
    try:
        from crewai import Agent, Crew, Task
    except ImportError as exc:
        raise SystemExit(
            "Install with: pip install agentguard47[crewai] crewai"
        ) from exc

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY before running this starter.")

    tracer = Tracer(
        sink=JsonlFileSink(".agentguard/traces.jsonl"),
        service="my-agent",
    )
    loop_guard = LoopGuard(max_repeats=3, window=6)
    budget_guard = BudgetGuard(max_cost_usd=5.00, max_calls=20)
    handler = AgentGuardCrewHandler(
        tracer=tracer,
        loop_guard=loop_guard,
        budget_guard=budget_guard,
    )

    agent = Agent(
        role="researcher",
        goal="Answer one short question clearly.",
        backstory="You are concise and careful.",
        llm="gpt-4o-mini",
        step_callback=handler.step_callback,
        verbose=True,
    )
    task = Task(
        description="Explain what AgentGuard does in one short paragraph.",
        agent=agent,
        callback=handler.task_callback,
    )

    result = Crew(agents=[agent], tasks=[task], verbose=True).kickoff()
    print(result)
    print("Traces saved to .agentguard/traces.jsonl")


if __name__ == "__main__":
    main()
