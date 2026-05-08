from __future__ import annotations

import agentguard


def main() -> None:
    try:
        from pydantic_ai import Agent
        from pydantic_ai.models.test import TestModel
    except ImportError as exc:
        raise SystemExit(
            "Install with: pip install agentguard47 pydantic-ai"
        ) from exc

    tracer = agentguard.init(
        profile="coding-agent",
        service="my-agent",
        budget_usd=5.00,
        trace_file=".agentguard/traces.jsonl",
        local_only=True,
        auto_patch=False,
    )

    # TestModel lets this starter run without API keys or network calls.
    agent = Agent(
        TestModel(
            custom_output_text="Add AgentGuard around the agent run and inspect the local trace."
        ),
        instructions="Return one practical next step for adding runtime controls.",
    )

    try:
        with tracer.trace("pydantic_ai.agent.run") as span:
            result = agent.run_sync("How should I guard this agent?")
            span.event("agent.answer", data={"output": result.output})
            print(result.output)
    finally:
        agentguard.shutdown()

    print("Traces saved to .agentguard/traces.jsonl")


if __name__ == "__main__":
    main()
