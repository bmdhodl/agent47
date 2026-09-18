"""Version-pinned streaming regression: mock provider, real patch and budget.

Applications should use the public patch_openai API. This demo uses the private
instance hook so it can run without the openai package. The provider is mocked;
the installed AgentGuard patch, stream wrapper, and budget consume path are real.
"""
import json
from importlib.metadata import version
from types import SimpleNamespace

from agentguard import BudgetGuard, Tracer
from agentguard.instrument import _patch_openai_instance


class Sink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


class MockStream:
    def __init__(self, chunks):
        self._chunks = list(chunks)
        self.usage = None

    def __iter__(self):
        return iter(self._chunks)


def _chunks():
    usage = SimpleNamespace(prompt_tokens=120, completion_tokens=80, total_tokens=200)
    return [
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="a"))], usage=None),
        SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="b"))], usage=None),
        SimpleNamespace(choices=[], usage=usage),
    ]


def main():
    sent = []
    chunks = _chunks()

    def create(**kwargs):
        sent.append(kwargs)
        return MockStream(chunks)

    endpoint = SimpleNamespace(create=create)
    client = SimpleNamespace(chat=SimpleNamespace(completions=endpoint))
    guard = BudgetGuard(max_tokens=10_000, max_calls=10)
    sink = Sink()
    _patch_openai_instance(client, Tracer(sink=sink), guard)
    stream = endpoint.create(model="gpt-4o-mini", stream=True)
    received = list(stream)
    results = [event for event in sink.events if event.get("name") == "llm.result"]
    include_usage = None
    if sent:
        options = sent[0].get("stream_options") or {}
        include_usage = options.get("include_usage")
    print(json.dumps({
        "version": version("agentguard47"),
        "stream_chunks": len(received),
        "recorded_tokens": guard.state.tokens_used,
        "recorded_calls": guard.state.calls_used,
        "llm_result_events": len(results),
        "include_usage": include_usage,
        "network_calls": 0,
        "mock_provider_requests": len(sent),
    }, indent=2))


if __name__ == "__main__":
    main()
