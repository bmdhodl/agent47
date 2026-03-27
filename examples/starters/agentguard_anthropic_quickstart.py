from __future__ import annotations

import os

import agentguard


def main() -> None:
    try:
        from anthropic import Anthropic
    except ImportError as exc:
        raise SystemExit("Install with: pip install agentguard47 anthropic") from exc

    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise SystemExit("Set ANTHROPIC_API_KEY before running this starter.")

    agentguard.init(
        service="my-agent",
        budget_usd=5.00,
        trace_file="traces.jsonl",
        local_only=True,
    )

    try:
        client = Anthropic()
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=128,
            messages=[
                {
                    "role": "user",
                    "content": "Give me a one-line summary of AgentGuard.",
                }
            ],
        )
        print(response.content[0].text)
    finally:
        agentguard.shutdown()

    print("Traces saved to traces.jsonl")


if __name__ == "__main__":
    main()
