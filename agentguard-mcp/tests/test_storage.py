from __future__ import annotations

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
