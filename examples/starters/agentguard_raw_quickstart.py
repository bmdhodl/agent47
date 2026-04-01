from __future__ import annotations

import agentguard


def main() -> None:
    tracer = agentguard.init(
        profile="coding-agent",
        service="my-agent",
        budget_usd=5.00,
        trace_file=".agentguard/traces.jsonl",
        local_only=True,
        auto_patch=False,
    )

    @agentguard.trace_tool(tracer)
    def search_docs(query: str) -> str:
        return f"results for {query}"

    try:
        with tracer.trace("agent.run") as span:
            result = search_docs("agentguard starter")
            span.event("agent.answer", data={"result": result})
    finally:
        agentguard.shutdown()

    print("Completed local raw starter run.")
    print("Traces saved to .agentguard/traces.jsonl")


if __name__ == "__main__":
    main()
