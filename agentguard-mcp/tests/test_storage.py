from __future__ import annotations

import threading
from datetime import datetime, timezone

import pytest

from agentguard_mcp.storage import BudgetStore


def test_record_call_increments_every_matching_scope(tmp_path):
    store = BudgetStore(tmp_path / "state.db")
    store.set_budget("global", 1_000, 1.0, "day")
    store.set_budget("server:github", 1_000, 1.0, "day")
    store.set_budget("tool:github.create_issue", 1_000, 1.0, "day")
    store.set_budget("session:abc", 1_000, 1.0, "session")

    result = store.record_call("github", "create_issue", 10, 15, 0.25, "abc")

    assert result["allowed"] is True
    assert store.check_remaining("global")["tokens_used"] == 25
    assert store.check_remaining("server:github")["tokens_used"] == 25
    assert store.check_remaining("tool:github.create_issue")["usd_used"] == 0.25
    assert store.check_remaining("session:abc")["tokens_used"] == 25


def test_kill_switch_blocks_before_limit_hit(tmp_path):
    store = BudgetStore(tmp_path / "state.db")
    store.set_budget("server:github", 10_000, 100.0, "day")
    store.kill_switch("server:github", True)

    result = store.record_call("github", "create_issue", 1, 1, 0.01, None)

    assert result["allowed"] is False
    assert result["reasons"] == ["server:github is blocked by kill_switch"]
    assert store.check_remaining("server:github")["tokens_used"] == 0


def test_budget_rollover_at_day_boundary(tmp_path):
    store = BudgetStore(tmp_path / "state.db")
    store.set_budget("global", 100, 1.0, "day")
    before_midnight = datetime(2026, 5, 4, 23, 59, tzinfo=timezone.utc)
    after_midnight = datetime(2026, 5, 5, 0, 1, tzinfo=timezone.utc)

    store.record_call("github", "create_issue", 40, 20, 0.2, None, now=before_midnight)

    assert store.check_remaining("global", before_midnight)["tokens_used"] == 60
    assert store.check_remaining("global", after_midnight)["tokens_used"] == 0


def test_record_call_returns_block_when_limit_exceeded(tmp_path):
    store = BudgetStore(tmp_path / "state.db")
    store.set_budget("tool:github.create_issue", 10, None, "day")

    result = store.record_call("github", "create_issue", 6, 5, 0.01, None)

    assert result["allowed"] is False
    assert result["reasons"] == [
        "tool:github.create_issue token budget exceeded: 11 > 10",
    ]
    assert store.check_remaining("tool:github.create_issue")["tokens_used"] == 0


def test_record_call_allows_exact_limit_and_persists(tmp_path):
    store = BudgetStore(tmp_path / "state.db")
    store.set_budget("global", 10, None, "day")

    result = store.record_call("github", "create_issue", 6, 4, 0.01, None)

    assert result["allowed"] is True
    assert store.check_remaining("global")["tokens_used"] == 10


def test_set_budget_rejects_empty_limits(tmp_path):
    store = BudgetStore(tmp_path / "state.db")

    with pytest.raises(ValueError, match="set at least one"):
        store.set_budget("global", None, None, "day")


def test_concurrent_record_calls_never_overrun_budget(tmp_path):
    """record_call must not let concurrent writers exceed the token budget.

    The budget check and the usage write must be atomic. Without that,
    two writers can both read "room available", both write, and push
    usage past the limit (a TOCTOU race).
    """
    store = BudgetStore(tmp_path / "state.db")
    store.set_budget("global", 1_000, None, "session")

    allowed: list[int] = []
    lock = threading.Lock()
    barrier = threading.Barrier(20)

    def worker() -> None:
        barrier.wait()
        result = store.record_call("srv", "tool", 100, 0, 0.0, None)
        if result["allowed"]:
            with lock:
                allowed.append(1)

    threads = [threading.Thread(target=worker) for _ in range(20)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    final_tokens = store.check_remaining("global")["tokens_used"]
    # Budget is 1000 tokens, each call costs 100 -> at most 10 may pass.
    assert final_tokens <= 1_000, (
        f"budget overrun: {final_tokens} tokens recorded, limit is 1000"
    )
    assert len(allowed) == 10, (
        f"expected exactly 10 allowed calls, got {len(allowed)}"
    )
