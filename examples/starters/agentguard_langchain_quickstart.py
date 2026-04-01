from __future__ import annotations

import os

from agentguard import BudgetGuard, JsonlFileSink, LoopGuard, Tracer
from agentguard.integrations.langchain import AgentGuardCallbackHandler


def main() -> None:
    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:
        raise SystemExit(
            "Install with: pip install agentguard47[langchain] langchain langchain-openai"
        ) from exc

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY before running this starter.")

    tracer = Tracer(
        sink=JsonlFileSink(".agentguard/traces.jsonl"),
        service="my-agent",
    )
    loop_guard = LoopGuard(max_repeats=3, window=6)
    budget_guard = BudgetGuard(max_cost_usd=5.00, max_calls=20)
    handler = AgentGuardCallbackHandler(
        tracer=tracer,
        loop_guard=loop_guard,
        budget_guard=budget_guard,
    )

    response = ChatOpenAI(model="gpt-4o-mini", temperature=0).invoke(
        "Give me a one-line summary of AgentGuard.",
        config={"callbacks": [handler]},
    )
    print(response.content)
    print("Traces saved to .agentguard/traces.jsonl")


if __name__ == "__main__":
    main()
