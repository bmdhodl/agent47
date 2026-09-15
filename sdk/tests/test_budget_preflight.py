"""REGRESSION: caught budget stops must not dispatch another provider request."""
import asyncio
from types import SimpleNamespace

import pytest

from agentguard import AsyncTracer, BudgetExceeded, BudgetGuard, JsonFileStateStore, Tracer
from agentguard import instrument


class Sink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


@pytest.mark.parametrize("provider", ["openai", "anthropic"])
@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize("limit,usage", [
    ({"max_calls": 1}, {"calls": 1}),
    ({"max_tokens": 10}, {"tokens": 10}),
    ({"max_cost_usd": 1}, {"cost_usd": 1}),
    ({"max_calls": 0}, {}),
])
def test_exhausted_budget_never_dispatches(provider, asynchronous, limit, usage):
    guard = BudgetGuard(**limit)
    guard.consume(**usage)
    calls = []

    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1))

    async def async_create(**kwargs):
        return create(**kwargs)

    endpoint = SimpleNamespace(create=async_create if asynchronous else create)
    client = SimpleNamespace(chat=SimpleNamespace(completions=endpoint), messages=endpoint)
    sink = Sink()
    tracer = (AsyncTracer if asynchronous else Tracer)(sink=sink)
    suffix = "_async" if asynchronous else ""
    getattr(instrument, f"_patch_{provider}{suffix}_instance")(client, tracer, guard)
    for _ in range(2):
        with pytest.raises(BudgetExceeded):
            result = endpoint.create(model="gpt-4o-mini")
            if asynchronous:
                asyncio.run(result)
    assert calls == []
    assert guard.state.calls_used == usage.get("calls", 0)
    assert any(e.get("name") == "guard.budget_exceeded" for e in sink.events)


def test_preflight_reads_shared_store_and_current_day(tmp_path):
    store = JsonFileStateStore(str(tmp_path / "budget.json"))
    clock = [1700000000.0]
    options = dict(max_calls=1, store=store, key="shared", period="day", now=lambda: clock[0])
    reader, writer = BudgetGuard(**options), BudgetGuard(**options)
    reader.check()
    writer.consume(calls=1)
    with pytest.raises(BudgetExceeded):
        reader.check()
    clock[0] += 86400
    reader.check()
    assert reader.state.calls_used == 0


def test_check_does_not_charge_or_warn_and_reset_reopens():
    warnings = []
    guard = BudgetGuard(max_calls=1, warn_at_pct=0, on_warning=warnings.append)
    guard.check()
    guard.check()
    assert guard.state.calls_used == 0
    assert warnings == []
    guard.consume(calls=1)
    with pytest.raises(BudgetExceeded):
        guard.check()
    guard.reset()
    guard.check()
