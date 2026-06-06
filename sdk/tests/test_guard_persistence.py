"""Tests for persistent, cross-process guard state (BudgetGuard store=).

The headline test is two real OS processes sharing one store file: if the cross-process
lock is wrong, increments are lost and the combined count overshoots the ceiling. The
suite also proves state survives process death, that a corrupt store raises instead of
silently resetting, that period='day' resets deterministically via an injected clock,
and that the in-memory default is unchanged.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from agentguard import (
    AgentGuardError,
    BudgetExceeded,
    BudgetGuard,
    JsonFileStateStore,
    StateStoreError,
)

_SDK_DIR = Path(__file__).resolve().parents[1]


def test_in_memory_default_unchanged_without_store():
    # Backward compatibility: no store -> exact original behavior.
    guard = BudgetGuard(max_calls=2)
    guard.consume(calls=1)
    guard.consume(calls=1)
    with pytest.raises(BudgetExceeded):
        guard.consume(calls=1)


def test_store_requires_key(tmp_path):
    with pytest.raises(ValueError, match="key is required"):
        BudgetGuard(max_calls=5, store=JsonFileStateStore(tmp_path / "s.json"))


def test_period_requires_store():
    with pytest.raises(ValueError, match="period requires a store"):
        BudgetGuard(max_calls=5, period="day")


def test_persists_across_instances(tmp_path):
    path = tmp_path / "budget.json"
    g1 = BudgetGuard(max_calls=3, store=JsonFileStateStore(path), key="fleet")
    g1.consume(calls=1)
    g1.consume(calls=1)
    del g1  # the process/object goes away

    # A brand new guard from the same store + key sees the prior usage.
    g2 = BudgetGuard(max_calls=3, store=JsonFileStateStore(path), key="fleet")
    g2.consume(calls=1)  # 3rd call total - at the limit, still ok
    with pytest.raises(BudgetExceeded):
        g2.consume(calls=1)  # 4th call total - over the ceiling


def test_overflow_is_durable(tmp_path):
    # The increment that trips the limit must still be persisted.
    path = tmp_path / "budget.json"
    g = BudgetGuard(max_calls=1, store=JsonFileStateStore(path), key="k")
    g.consume(calls=1)
    with pytest.raises(BudgetExceeded):
        g.consume(calls=1)
    stored = JsonFileStateStore(path).read("k")
    assert stored["calls_used"] == 2  # the overflow call was recorded


def test_corrupt_store_raises_not_silent_reset(tmp_path):
    path = tmp_path / "budget.json"
    path.write_text("{not valid json", encoding="utf-8")
    guard = BudgetGuard(max_calls=5, store=JsonFileStateStore(path), key="k")
    with pytest.raises(StateStoreError):
        guard.consume(calls=1)
    # StateStoreError is an AgentGuardError, so callers catching the base type see it.
    assert issubclass(StateStoreError, AgentGuardError)


def test_period_day_resets_on_rollover(tmp_path):
    path = tmp_path / "budget.json"
    clock = {"t": 0.0}  # 1970-01-01 UTC

    def now():
        return clock["t"]

    guard = BudgetGuard(
        max_calls=2, store=JsonFileStateStore(path), key="fleet", period="day", now=now
    )
    guard.consume(calls=1)
    guard.consume(calls=1)
    with pytest.raises(BudgetExceeded):
        guard.consume(calls=1)  # day 1 ceiling hit

    clock["t"] = 86_400.0  # advance to the next UTC day
    guard.consume(calls=1)  # fresh bucket -> allowed again
    guard.consume(calls=1)
    with pytest.raises(BudgetExceeded):
        guard.consume(calls=1)


def test_reset_clears_persisted_state(tmp_path):
    path = tmp_path / "budget.json"
    store = JsonFileStateStore(path)
    guard = BudgetGuard(max_calls=2, store=store, key="k")
    guard.consume(calls=1)
    guard.consume(calls=1)
    guard.reset()
    guard.consume(calls=1)  # ceiling restarted
    assert store.read("k")["calls_used"] == 1


_WORKER = textwrap.dedent(
    """
    import sys
    from agentguard import BudgetGuard, JsonFileStateStore, BudgetExceeded
    path, ceiling, attempts = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    guard = BudgetGuard(max_calls=ceiling, store=JsonFileStateStore(path), key="fleet")
    ok = 0
    for _ in range(attempts):
        try:
            guard.consume(calls=1)
            ok += 1
        except BudgetExceeded:
            break
    print(ok)
    """
)


def test_two_processes_share_one_ceiling_no_lost_updates(tmp_path):
    # Two real OS processes hammer the same store. With a correct cross-process lock the
    # combined number of successful consumes equals the ceiling exactly. A broken lock
    # loses updates and lets MORE than `ceiling` calls succeed.
    path = tmp_path / "budget.json"
    ceiling = 20
    attempts = 15  # 2 * 15 = 30 attempts against a ceiling of 20

    env = {**os.environ, "PYTHONPATH": str(_SDK_DIR)}

    procs = [
        subprocess.Popen(
            [sys.executable, "-c", _WORKER, str(path), str(ceiling), str(attempts)],
            stdout=subprocess.PIPE,
            text=True,
            env=env,
        )
        for _ in range(2)
    ]
    outs = [p.communicate(timeout=60)[0] for p in procs]
    assert all(p.returncode == 0 for p in procs), outs

    successes = sum(int(o.strip().splitlines()[-1]) for o in outs)
    assert successes == ceiling, f"expected exactly {ceiling} successful consumes, got {successes}"

    final = JsonFileStateStore(path).read("fleet")
    assert final["calls_used"] >= ceiling


def test_high_contention_no_crashes_or_lost_updates(tmp_path):
    # Heavier contention than the two-process case. This is the regression guard for the
    # Windows "delete pending" race: a concurrent release made an exclusive lock create
    # fail with PermissionError (not FileExistsError), crashing the acquirer. With the
    # lock hardened, every worker exits 0 and the combined successes still equal the
    # ceiling exactly (the lock never loses or double-counts an increment).
    path = tmp_path / "budget.json"
    ceiling = 30
    workers = 6
    attempts = 10  # 6 * 10 = 60 attempts against a ceiling of 30

    env = {**os.environ, "PYTHONPATH": str(_SDK_DIR)}
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", _WORKER, str(path), str(ceiling), str(attempts)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        for _ in range(workers)
    ]
    results = [p.communicate(timeout=60) for p in procs]
    crashed = [(i, procs[i].returncode, results[i][1]) for i in range(workers) if procs[i].returncode != 0]
    assert not crashed, f"workers crashed (lock not contention-safe): {crashed}"

    successes = sum(int(out.strip().splitlines()[-1]) for out, _ in results)
    assert successes == ceiling, f"expected exactly {ceiling} successful consumes, got {successes}"
