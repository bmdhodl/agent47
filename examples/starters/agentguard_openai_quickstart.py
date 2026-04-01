from __future__ import annotations

import os

import agentguard


def main() -> None:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit("Install with: pip install agentguard47 openai") from exc

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set OPENAI_API_KEY before running this starter.")

    agentguard.init(
        profile="coding-agent",
        service="my-agent",
        budget_usd=5.00,
        trace_file=".agentguard/traces.jsonl",
        local_only=True,
    )

    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": "Give me a one-line summary of AgentGuard.",
                }
            ],
        )
        print(response.choices[0].message.content)
    finally:
        agentguard.shutdown()

    print("Traces saved to .agentguard/traces.jsonl")


if __name__ == "__main__":
    main()
