"""Richard discussion #108 — task-level budget claims on shipped APIs.

Source: https://github.com/bmdhodl/agent47/discussions/108#discussioncomment-17567352

These scenarios call real ``BudgetGuard.goal`` / ``consume`` only (no reimplementation).
"""
from __future__ import annotations

import pytest

from agentguard import BudgetExceeded, BudgetGuard


def test_richard_task_level_hard_enforcement() -> None:
    """Claim A: enforcement at task level, not only session API totals."""
    guard = BudgetGuard(max_cost_usd=50.0)  # session still has headroom
    with pytest.raises(BudgetExceeded, match="Goal 'agent-task' cost budget exceeded"):
        with guard.goal("agent-task", verifier=lambda: True, max_cost_usd=0.50) as g:
            g.attempt()
            guard.consume(cost_usd=0.40)
            guard.consume(cost_usd=0.20)
    assert g.cost_usd == pytest.approx(0.60)
    assert guard.state.cost_used == pytest.approx(0.60)


def test_richard_retries_tools_subtasks_visible_on_ledger() -> None:
    """Claim B: retries / sub-tasks make cost visible via goal ledger + failure_cost."""
    done = {"ok": False}
    guard = BudgetGuard(max_cost_usd=10.0)
    with guard.goal("multi-step", verifier=lambda: done["ok"], max_cost_usd=5.0) as parent:
        parent.attempt()
        guard.consume(cost_usd=0.10, tokens=50, calls=1)  # dead-end attempt
        parent.attempt()
        guard.consume(cost_usd=0.12, tokens=60, calls=1)  # another dead-end
        with guard.goal("delegated-tool", verifier=lambda: True) as child:
            child.attempt()
            guard.consume(cost_usd=0.05, tokens=20, calls=1)
        parent.attempt()
        guard.consume(cost_usd=0.08, tokens=40, calls=1)
        done["ok"] = True
    assert parent.succeeded is True
    assert parent.attempts == 3
    assert parent.failure_cost == pytest.approx(0.22)
    assert parent.cost_usd == pytest.approx(0.35)
    assert len(parent.sub_goals) == 1
    assert parent.sub_goals[0].cost_usd == pytest.approx(0.05)
    assert len(parent.calls) == 3  # direct only; child not double-counted


def test_richard_fallback_signal_when_task_crosses_threshold() -> None:
    """Claim C: fallback rules hook when a task crosses a budget threshold."""
    signals = []

    def on_task_budget(goal, msg: str) -> None:
        # Caller-owned fallback: e.g. stop new tools, switch model, wrap up.
        signals.append((goal.name, msg))

    guard = BudgetGuard(max_cost_usd=20.0)
    with guard.goal(
        "wrap-task",
        verifier=lambda: True,
        max_cost_usd=1.0,
        warn_at_pct=0.8,
        on_warning=on_task_budget,
    ) as g:
        g.attempt()
        guard.consume(cost_usd=0.70)
        assert signals == []
        guard.consume(cost_usd=0.15)  # soft signal only
        assert len(signals) == 1
        assert signals[0][0] == "wrap-task"
        assert "Goal 'wrap-task'" in signals[0][1]
        guard.consume(cost_usd=0.04)
        assert len(signals) == 1  # once per goal
    assert g.succeeded is True
    assert g.cost_usd == pytest.approx(0.89)
