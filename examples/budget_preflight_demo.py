"""Run against an installed SDK: mock provider dispatch, real patch and budget."""
import json
from importlib.metadata import version
from types import SimpleNamespace

from agentguard import BudgetExceeded, BudgetGuard, Tracer
from agentguard.instrument import _patch_openai_instance


class Sink:
    def emit(self, event):
        pass


def main():
    sent = []

    def create(**kwargs):
        sent.append(kwargs)
        return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2))

    endpoint = SimpleNamespace(create=create)
    client = SimpleNamespace(chat=SimpleNamespace(completions=endpoint))
    guard = BudgetGuard(max_calls=1)
    _patch_openai_instance(client, Tracer(sink=Sink()), guard)
    stopped = 0
    for _ in range(3):
        try:
            endpoint.create(model="gpt-4o-mini")
        except BudgetExceeded:
            stopped += 1
    print(json.dumps({
        "version": version("agentguard47"), "attempts": 3,
        "call_limit": 1, "mock_provider_requests": len(sent),
        "budget_exceptions": stopped, "recorded_calls": guard.state.calls_used,
        "network_calls": 0,
    }, indent=2))


if __name__ == "__main__":
    main()
