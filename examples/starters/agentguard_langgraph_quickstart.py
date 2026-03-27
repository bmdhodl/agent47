from __future__ import annotations

from agentguard import BudgetGuard, JsonlFileSink, LoopGuard, Tracer
from agentguard.integrations.langgraph import guard_node


def main() -> None:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise SystemExit(
            "Install with: pip install agentguard47[langgraph] langgraph"
        ) from exc

    tracer = Tracer(
        sink=JsonlFileSink("traces.jsonl"),
        service="my-agent",
    )
    loop_guard = LoopGuard(max_repeats=3, window=6)
    budget_guard = BudgetGuard(max_cost_usd=5.00, max_calls=20)

    def research_node(state: dict) -> dict:
        question = state["question"]
        return {"question": question, "answer": f"local answer for {question}"}

    builder = StateGraph(dict)
    builder.add_node(
        "research",
        guard_node(
            research_node,
            tracer=tracer,
            loop_guard=loop_guard,
            budget_guard=budget_guard,
        ),
    )
    builder.add_edge(START, "research")
    builder.add_edge("research", END)

    graph = builder.compile()
    result = graph.invoke({"question": "What is AgentGuard?"})
    print(result["answer"])
    print("Traces saved to traces.jsonl")


if __name__ == "__main__":
    main()
