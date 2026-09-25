"""AG-04: one store-backed OpenAI reservation path."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from agentguard import BudgetExceeded, BudgetGuard, JsonFileStateStore, Tracer
from agentguard._reservation_contract import MissingBound, ReservationContractError
from agentguard._reservation_path import traced_openai_reserved
from agentguard.instrument import _patch_anthropic_instance, _traced_openai_create
from agentguard.state import StateStoreError

ROOT = Path(__file__).resolve().parents[2]
_SDK = Path(__file__).resolve().parents[1]


class _Sink:
    def __init__(self):
        self.events = []

    def emit(self, event):
        self.events.append(event)


class _FailStore:
    def __init__(self, inner, fail_after):
        self._inner = inner
        self._fail_after = fail_after
        self.updates = 0

    def read(self, key):
        return self._inner.read(key)

    def update(self, key, mutator):
        if self.updates >= self._fail_after:
            raise StateStoreError("storage failure")
        self.updates += 1
        return self._inner.update(key, mutator)

    def clear(self, key):
        self._inner.clear(key)


def _usage_response():
    return SimpleNamespace(
        usage=SimpleNamespace(prompt_tokens=3, completion_tokens=2, total_tokens=5)
    )


def _guard(tmp_path, **limits):
    options = {"max_calls": 1, "store": JsonFileStateStore(tmp_path / "budget.json"), "key": "fleet"}
    options.update(limits)
    return BudgetGuard(**options)


def test_in_memory_guard_has_no_reservation_methods_without_store():
    guard = BudgetGuard(max_calls=1)
    with pytest.raises(ValueError, match="StateStore"):
        guard.reserve_for_dispatch("a", calls=1)
    assert guard.reservation_totals()["reserved"]["calls"] == 0


def test_barrier_threads_dispatch_once(tmp_path):
    store = JsonFileStateStore(tmp_path / "budget.json")
    barrier = threading.Barrier(2)
    lock = threading.Lock()
    sent = []
    results = []

    def create(**_kwargs):
        with lock:
            sent.append(1)
        return _usage_response()

    def worker():
        guard = BudgetGuard(max_calls=1, store=store, key="fleet")
        tracer = Tracer(sink=_Sink(), watermark=False)
        barrier.wait(5)
        try:
            _traced_openai_create(create, tracer, guard, model="gpt-4o-mini")
        except BudgetExceeded:
            with lock:
                results.append("blocked")
        else:
            with lock:
                results.append("ok")

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(10)
    assert sorted(results) == ["blocked", "ok"]
    assert sent == [1]
    totals = BudgetGuard(max_calls=1, store=store, key="fleet").reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["reserved"]["calls"] == 0
    assert totals["settled"]["tokens"] == 5


def test_cancel_before_dispatch_frees_the_slot(tmp_path):
    guard = _guard(tmp_path)
    calls = []

    def create(**_kwargs):
        calls.append(1)
        return _usage_response()

    def abort():
        raise RuntimeError("abort before send")

    with pytest.raises(RuntimeError, match="abort"):
        traced_openai_reserved(
            create,
            Tracer(sink=_Sink(), watermark=False),
            guard,
            (),
            {"model": "gpt-4o-mini"},
            before_send=abort,
        )
    assert calls == []
    assert guard.reservation_totals()["reserved"]["calls"] == 0
    _traced_openai_create(
        create, Tracer(sink=_Sink(), watermark=False), guard, model="gpt-4o-mini"
    )
    assert calls == [1]
    assert guard.reservation_totals()["settled"]["calls"] == 1


def test_provider_exception_keeps_the_hold(tmp_path):
    guard = _guard(tmp_path)

    def create(**_kwargs):
        raise TimeoutError("timed out")

    with pytest.raises(TimeoutError):
        _traced_openai_create(
            create, Tracer(sink=_Sink(), watermark=False), guard, model="gpt-4o-mini"
        )
    totals = guard.reservation_totals()
    assert totals["unresolved"]["calls"] == 1
    assert totals["settled"]["calls"] == 0
    with pytest.raises(BudgetExceeded):
        _traced_openai_create(
            create, Tracer(sink=_Sink(), watermark=False), guard, model="gpt-4o-mini"
        )


def test_duplicate_commit_is_idempotent(tmp_path):
    guard = _guard(tmp_path, max_calls=2)
    guard.reserve_for_dispatch("same", calls=1)
    first = guard.commit_reservation("same", tokens=4, cost_usd=0.0, calls=1)
    second = guard.commit_reservation("same", tokens=4, cost_usd=0.0, calls=1)
    assert first["status"] == second["status"] == "committed"
    assert guard.reservation_totals()["settled"]["calls"] == 1
    with pytest.raises(ReservationContractError, match="different usage"):
        guard.commit_reservation("same", tokens=9, cost_usd=0.0, calls=1)


def test_restart_keeps_the_hold_until_recover(tmp_path):
    path = tmp_path / "budget.json"
    env = {**os.environ, "PYTHONPATH": str(_SDK)}
    script = (
        "from agentguard import BudgetGuard, JsonFileStateStore\n"
        "import sys\n"
        "guard = BudgetGuard(max_calls=1, store=JsonFileStateStore(sys.argv[1]), key='fleet')\n"
        "guard.reserve_for_dispatch('dead', calls=1)\n"
        "print('reserved')\n"
    )
    proc = subprocess.run(
        [sys.executable, "-c", script, str(path)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    restarted = BudgetGuard(max_calls=1, store=JsonFileStateStore(path), key="fleet")
    assert restarted.reservation_totals()["reserved"]["calls"] == 1
    restarted.recover_reservation("dead")
    assert restarted.reservation_totals()["unresolved"]["calls"] == 1
    with pytest.raises(BudgetExceeded):
        restarted.reserve_for_dispatch("next", calls=1)


def test_storage_failure_does_not_dispatch_or_drop_a_hold(tmp_path):
    inner = JsonFileStateStore(tmp_path / "budget.json")
    blocked = BudgetGuard(max_calls=1, store=_FailStore(inner, 0), key="fleet")
    calls = []

    def create(**_kwargs):
        calls.append(1)
        return _usage_response()

    with pytest.raises(StateStoreError, match="storage failure"):
        _traced_openai_create(
            create, Tracer(sink=_Sink(), watermark=False), blocked, model="gpt-4o-mini"
        )
    assert calls == []
    assert inner.read("fleet") is None

    flaky = _FailStore(inner, 1)
    guard = BudgetGuard(max_calls=1, store=flaky, key="fleet")
    with pytest.raises(StateStoreError, match="storage failure"):
        _traced_openai_create(
            create, Tracer(sink=_Sink(), watermark=False), guard, model="gpt-4o-mini"
        )
    assert calls == [1]
    stored = inner.read("fleet")
    record = next(iter(stored["reservations"].values()))
    assert record["status"] == "reserved"
    assert stored["calls_used"] == 0


def test_old_persistent_fixture_stays_readable(tmp_path):
    path = tmp_path / "budget.json"
    path.write_text(
        json.dumps({"fleet": {"tokens_used": 2, "calls_used": 1, "cost_used": 0.25}}),
        encoding="utf-8",
    )
    guard = BudgetGuard(max_calls=2, store=JsonFileStateStore(path), key="fleet")
    totals = guard.reservation_totals()
    assert totals["settled"] == {"calls": 1, "tokens": 2, "cost": 0.25}
    assert totals["reserved"]["calls"] == 0
    guard.reserve_for_dispatch("new", calls=1)
    guard.consume(calls=0)
    stored = JsonFileStateStore(path).read("fleet")
    assert stored["calls_used"] == 1
    assert stored["reservations"]["new"]["status"] == "reserved"


def test_corrupt_store_refuses_reserve(tmp_path):
    path = tmp_path / "budget.json"
    path.write_text("{not json", encoding="utf-8")
    guard = BudgetGuard(max_calls=1, store=JsonFileStateStore(path), key="fleet")
    with pytest.raises(StateStoreError):
        guard.reserve_for_dispatch("a", calls=1)


def test_check_ignores_holds(tmp_path):
    guard = _guard(tmp_path)
    guard.reserve_for_dispatch("held", calls=1)
    guard.check()


def test_missing_token_bound_does_not_send(tmp_path):
    guard = _guard(tmp_path, max_calls=None, max_tokens=10)
    calls = []

    def create(**_kwargs):
        calls.append(1)
        return _usage_response()

    with pytest.raises(MissingBound):
        _traced_openai_create(
            create, Tracer(sink=_Sink(), watermark=False), guard, model="gpt-4o-mini"
        )
    assert calls == []
    _traced_openai_create(
        create,
        Tracer(sink=_Sink(), watermark=False),
        guard,
        model="gpt-4o-mini",
        max_tokens=4,
    )
    assert calls == [1]
    assert guard.reservation_totals()["reserved"]["calls"] == 0


def test_dollar_bound_falls_back_when_the_price_table_omits_the_rate(tmp_path, monkeypatch):
    from agentguard import _reservation_path

    monkeypatch.setitem(_reservation_path.DEFAULT_PRICE_TABLE, "overestimate", {})
    guard = _guard(tmp_path, max_calls=None, max_cost_usd=0.01)
    calls = []

    def create(**_kwargs):
        calls.append(1)
        return _usage_response()

    with pytest.raises(BudgetExceeded):
        _traced_openai_create(
            create,
            Tracer(sink=_Sink(), watermark=False),
            guard,
            model="gpt-4o-mini",
            max_tokens=1_000_000,
        )
    assert calls == []


def test_dollar_bound_refuses_when_the_estimate_does_not_fit(tmp_path):
    guard = _guard(tmp_path, max_calls=None, max_cost_usd=0.01)
    calls = []

    def create(**_kwargs):
        calls.append(1)
        return _usage_response()

    with pytest.raises(BudgetExceeded):
        _traced_openai_create(
            create,
            Tracer(sink=_Sink(), watermark=False),
            guard,
            model="gpt-4o-mini",
            max_tokens=1_000_000,
        )
    assert calls == []


def test_commit_enforces_while_guard_lock_is_held(tmp_path):
    guard = _guard(tmp_path, max_calls=None, max_tokens=1)
    guard.reserve_for_dispatch("over", calls=1, tokens_bound=1)
    seen = {}
    original = guard._enforce_limits

    def wrapped(*args, **kwargs):
        seen["locked"] = guard._lock.locked()
        return original(*args, **kwargs)

    guard._enforce_limits = wrapped
    with pytest.raises(BudgetExceeded):
        guard.commit_reservation("over", tokens=5, cost_usd=0.0, calls=1)
    assert seen["locked"] is True
    assert guard.reservation_totals()["settled"]["tokens"] == 5


def test_commit_records_estimate_overrun(tmp_path):
    guard = _guard(tmp_path, max_calls=None, max_cost_usd=1.0)
    guard.reserve_for_dispatch("over", calls=1, cost_bound=0.1, price_table_version="2026.07.15")
    record = guard.commit_reservation("over", tokens=10, cost_usd=0.4, calls=1)
    assert record["estimate_overrun"] is True
    assert guard.reservation_totals()["settled"]["cost"] == 0.4


def test_stream_reserves_and_anthropic_non_stream_does_not(tmp_path):
    store = JsonFileStateStore(tmp_path / "budget.json")
    guard = BudgetGuard(max_calls=2, store=store, key="fleet")
    _traced_openai_create(
        lambda **_kwargs: SimpleNamespace(),
        Tracer(sink=_Sink(), watermark=False),
        guard,
        model="gpt-4o-mini",
        stream=True,
    )
    assert guard.reservation_totals()["reserved"]["calls"] == 1

    plain = JsonFileStateStore(tmp_path / "plain.json")
    anthropic_guard = BudgetGuard(max_calls=2, store=plain, key="fleet")

    def create(**_kwargs):
        return SimpleNamespace(usage=SimpleNamespace(input_tokens=1, output_tokens=1))

    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    _patch_anthropic_instance(client, Tracer(sink=_Sink(), watermark=False), anthropic_guard)
    client.messages.create(model="claude-test")
    stored = plain.read("fleet")
    assert "reservations" not in stored
    assert stored["calls_used"] == 1


def test_spawn_race_script_dispatches_once():
    script = ROOT / "examples" / "enforcement_boundary" / "reserved_one_dispatch.py"
    env = {**os.environ, "PYTHONPATH": str(_SDK), "NO_COLOR": "1"}
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    assert payload["fixed"] is True
    assert payload["dispatched"] == 1
    assert payload["blocked"] == 1
    assert payload["settled_calls"] == 1
    assert payload["network_calls"] == 0
    assert payload["start_method"] == "spawn"


def test_missing_usage_settles_one_call_and_zero_tokens(tmp_path):
    guard = _guard(tmp_path)
    _traced_openai_create(
        lambda **_kwargs: SimpleNamespace(),
        Tracer(sink=_Sink(), watermark=False),
        guard,
        model="gpt-4o-mini",
    )
    totals = guard.reservation_totals()
    assert totals["settled"]["calls"] == 1
    assert totals["settled"]["tokens"] == 0


def test_commit_emits_one_warning(tmp_path):
    warnings = []
    guard = BudgetGuard(
        max_calls=1,
        warn_at_pct=0.5,
        on_warning=warnings.append,
        store=JsonFileStateStore(tmp_path / "budget.json"),
        key="fleet",
    )
    guard.reserve_for_dispatch("a", calls=1)
    guard.commit_reservation("a", tokens=1, cost_usd=0.0, calls=1)
    assert len(warnings) == 1


def test_operator_can_release_an_unresolved_hold(tmp_path):
    guard = _guard(tmp_path)
    guard.reserve_for_dispatch("a", calls=1)
    guard.mark_reservation_unresolved("a", reason="timeout")
    with pytest.raises(ReservationContractError, match="attest"):
        guard.cancel_reservation("a")
    guard.cancel_reservation("a", operator_attests_never_dispatched=True)
    totals = guard.reservation_totals()
    assert totals["unresolved"]["calls"] == 0
    guard.reserve_for_dispatch("b", calls=1)


def test_actual_cost_above_cap_settles_then_raises(tmp_path):
    guard = _guard(tmp_path, max_calls=None, max_cost_usd=0.3)

    def create(**_kwargs):
        return SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2),
            cost_usd=0.5,
        )

    with pytest.raises(BudgetExceeded):
        _traced_openai_create(
            create,
            Tracer(sink=_Sink(), watermark=False),
            guard,
            model="gpt-4o-mini",
            max_tokens=10,
        )
    totals = guard.reservation_totals()
    assert totals["settled"]["cost"] == 0.5
    assert totals["unresolved"]["calls"] == 0
    assert totals["reserved"]["calls"] == 0


def test_reset_clears_holds(tmp_path):
    guard = _guard(tmp_path)
    guard.reserve_for_dispatch("a", calls=1)
    guard.reset()
    assert guard.reservation_totals()["reserved"]["calls"] == 0
    guard.reserve_for_dispatch("b", calls=1)


def test_ag04_proof_is_plain_text():
    folder = ROOT / "proof" / "ag-04-reservation-path"
    assert (folder / "race.json").is_file()
    for path in folder.iterdir():
        if path.suffix not in {".txt", ".json", ".md", ".py"}:
            continue
        assert b"\x1b" not in path.read_bytes(), path.name


def test_invoice_cap_stays_unclaimable():
    from agentguard._reservation_contract import can_claim_invoice_cap

    assert can_claim_invoice_cap() is False
