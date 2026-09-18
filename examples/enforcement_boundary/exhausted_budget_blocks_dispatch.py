"""Exhausted recorded budget must not dispatch the next mock provider call.

This is the AG-01 reproduction for recorded-budget preflight. The provider is
mocked. The AgentGuard patch and BudgetGuard are real. There is no network.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

from agentguard import BudgetExceeded, BudgetGuard, Tracer
from agentguard.instrument import _patch_openai_instance


class Sink:
    def emit(self, event):
        pass


def main() -> None:
    sent = []

    def create(**kwargs):
        sent.append(kwargs)
        return SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2)
        )

    endpoint = SimpleNamespace(create=create)
    client = SimpleNamespace(chat=SimpleNamespace(completions=endpoint))
    guard = BudgetGuard(max_calls=1)
    _patch_openai_instance(client, Tracer(sink=Sink()), guard)

    first = endpoint.create(model="gpt-4o-mini")
    blocked = 0
    for _ in range(2):
        try:
            endpoint.create(model="gpt-4o-mini")
        except BudgetExceeded:
            blocked += 1

    print(json.dumps({
        "call_limit": 1,
        "first_response": first is not None,
        "mock_provider_requests": len(sent),
        "budget_exceptions": blocked,
        "recorded_calls": guard.state.calls_used,
        "network_calls": 0,
        "next_dispatch_prevented": len(sent) == 1 and blocked == 2,
    }, indent=2))
    if len(sent) != 1 or blocked != 2:
        raise SystemExit("exhausted recorded budget still dispatched")


if __name__ == "__main__":
    main()
