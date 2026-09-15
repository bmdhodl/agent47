"""Real provider clients, mocked HTTP, installed AgentGuard. No paid requests."""
import asyncio
import json
from importlib.metadata import version

import anthropic
import httpx2
import openai

from agentguard import AsyncTracer, BudgetExceeded, BudgetGuard, Tracer, instrument


class Sink:
    def emit(self, event):
        pass


async def run(provider, asynchronous):
    requests = []

    def handle(request):
        requests.append(request)
        if provider == "openai":
            body = {"id": "chatcmpl-demo", "object": "chat.completion", "created": 0,
                    "model": "gpt-4o-mini", "choices": [],
                    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}}
        else:
            body = {"id": "msg-demo", "type": "message", "role": "assistant",
                    "model": "claude-sonnet-4-20250514", "content": [],
                    "stop_reason": "end_turn", "stop_sequence": None,
                    "usage": {"input_tokens": 3, "output_tokens": 2}}
        return httpx2.Response(200, json=body)

    guard = BudgetGuard(max_calls=1)
    suffix = "_async" if asynchronous else ""
    tracer = (AsyncTracer if asynchronous else Tracer)(sink=Sink())
    getattr(instrument, f"patch_{provider}{suffix}")(tracer, budget_guard=guard)
    transport = httpx2.MockTransport(handle)
    http = (httpx2.AsyncClient if asynchronous else httpx2.Client)(transport=transport)
    cls = ((openai.AsyncOpenAI if asynchronous else openai.OpenAI) if provider == "openai"
           else (anthropic.AsyncAnthropic if asynchronous else anthropic.Anthropic))
    client = cls(api_key="local-test-placeholder", http_client=http, max_retries=0)
    endpoint = client.chat.completions if provider == "openai" else client.messages
    model = "gpt-4o-mini" if provider == "openai" else "claude-sonnet-4-20250514"
    stopped = 0
    try:
        for _ in range(3):
            try:
                result = endpoint.create(model=model, messages=[{"role": "user", "content": "test"}], max_tokens=5)
                if asynchronous:
                    await result
            except BudgetExceeded:
                stopped += 1
    finally:
        if asynchronous:
            await client.close()
        else:
            client.close()
        getattr(instrument, f"unpatch_{provider}{suffix}")()
    assert len(requests) == 1, (provider, asynchronous, len(requests))
    assert stopped == 2
    assert guard.state.calls_used == 1
    assert guard.state.tokens_used == 5
    return {"provider": provider, "async": asynchronous, "http_dispatches": 1,
            "blocked_retries": 2, "recorded_tokens": 5}


async def main():
    results = [await run(p, a) for p in ("openai", "anthropic") for a in (False, True)]
    print(json.dumps({"agentguard47": version("agentguard47"),
                      "openai": version("openai"), "anthropic": version("anthropic"),
                      "network": "MockTransport only", "results": results}, indent=2))


asyncio.run(main())
