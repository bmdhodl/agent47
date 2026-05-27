"""Tests for goal-level metering (BudgetGuard.goal)."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from agentguard import BudgetGuard, Goal


def test_happy_path_single_attempt_succeeds() -> None:
    """One attempt, verifier returns True, no failure cost."""
    guard = BudgetGuard(max_cost_usd=10.0)
    verified = {"ok": True}

    with guard.goal("simple-goal", verifier=lambda: verified["ok"]) as g:
        g.attempt()
        guard.consume(tokens=100, calls=1, cost_usd=0.05)
        guard.consume(tokens=50, calls=1, cost_usd=0.02)

    assert isinstance(g, Goal)
    assert g.succeeded is True
    assert g.attempts == 1
    assert g.cost_usd == pytest.approx(0.07)
    assert g.failure_cost == pytest.approx(0.0)
    assert len(g.calls) == 2
    assert g.duration_sec >= 0


def test_three_attempts_then_success_attributes_failure_cost() -> None:
    """3 attempts, last succeeds. Cost of first two attempts is failure cost."""
    guard = BudgetGuard(max_cost_usd=10.0)
    succeeded_flag = {"ok": False}

    with guard.goal("retry-goal", verifier=lambda: succeeded_flag["ok"]) as g:
        # Attempt 1 - fails (the verifier won't see this, but the attempt
        # counter accumulates calls under attempt_idx=1).
        g.attempt()
        guard.consume(tokens=100, calls=1, cost_usd=0.10)

        # Attempt 2 - fails.
        g.attempt()
        guard.consume(tokens=120, calls=1, cost_usd=0.12)

        # Attempt 3 - succeeds.
        g.attempt()
        guard.consume(tokens=80, calls=1, cost_usd=0.08)
        succeeded_flag["ok"] = True

    assert g.succeeded is True
    assert g.attempts == 3
    assert g.cost_usd == pytest.approx(0.30)
    # Failure cost = cost of attempts 1 and 2 = 0.10 + 0.12 = 0.22
    assert g.failure_cost == pytest.approx(0.22)
    assert len(g.calls) == 3
    assert [c.attempt_idx for c in g.calls] == [1, 2, 3]


def test_failed_goal_all_cost_is_failure_cost() -> None:
    """Verifier returns False. All direct calls count as failure cost."""
    guard = BudgetGuard(max_cost_usd=10.0)

    with guard.goal("doomed", verifier=lambda: False) as g:
        g.attempt()
        guard.consume(tokens=50, calls=1, cost_usd=0.05)
        g.attempt()
        guard.consume(tokens=50, calls=1, cost_usd=0.05)

    assert g.succeeded is False
    assert g.cost_usd == pytest.approx(0.10)
    assert g.failure_cost == pytest.approx(0.10)


def test_nested_goals_no_double_count() -> None:
    """Parent total = own calls + sub-goal totals, with no double-counting."""
    guard = BudgetGuard(max_cost_usd=10.0)

    with guard.goal("parent", verifier=lambda: True) as parent:
        parent.attempt()
        guard.consume(tokens=10, calls=1, cost_usd=0.01)  # parent direct

        with guard.goal("child-a", verifier=lambda: True) as child_a:
            child_a.attempt()
            guard.consume(tokens=20, calls=1, cost_usd=0.02)  # child-a only

        with guard.goal("child-b", verifier=lambda: True) as child_b:
            child_b.attempt()
            guard.consume(tokens=30, calls=1, cost_usd=0.03)  # child-b only

        guard.consume(tokens=5, calls=1, cost_usd=0.005)  # parent direct (post-child)

    assert child_a.cost_usd == pytest.approx(0.02)
    assert child_b.cost_usd == pytest.approx(0.03)
    assert parent.own_cost_usd == pytest.approx(0.015)
    # Total = 0.015 (parent direct) + 0.02 + 0.03 = 0.065
    assert parent.cost_usd == pytest.approx(0.065)
    # Child calls must not also appear in parent.calls (no double count).
    assert len(parent.calls) == 2
    assert len(child_a.calls) == 1
    assert len(child_b.calls) == 1
    # All sub-goals succeeded so failure cost rolls up to 0.
    assert parent.failure_cost == pytest.approx(0.0)


def test_verifier_must_be_callable() -> None:
    guard = BudgetGuard(max_cost_usd=1.0)
    with pytest.raises(TypeError):
        guard.goal("bad", verifier="not-callable")  # type: ignore[arg-type]


def test_exception_inside_block_marks_goal_failed() -> None:
    """If the block exits with an exception, succeeded=False and verifier
    is NOT called (fail loudly is upstream's job)."""
    guard = BudgetGuard(max_cost_usd=1.0)
    verifier_called = {"called": False}

    def verifier() -> bool:
        verifier_called["called"] = True
        return True

    with pytest.raises(ValueError):
        with guard.goal("crash", verifier=verifier) as g:
            g.attempt()
            guard.consume(tokens=10, calls=1, cost_usd=0.01)
            raise ValueError("boom")

    assert g.succeeded is False
    assert verifier_called["called"] is False
    # Cost still recorded.
    assert g.cost_usd == pytest.approx(0.01)


def test_consume_outside_goal_is_unaffected() -> None:
    """The hook is a pure no-op when no goal is active. Budget guard semantics
    unchanged."""
    guard = BudgetGuard(max_cost_usd=10.0)
    guard.consume(tokens=100, calls=1, cost_usd=0.05)
    assert guard.state.cost_used == pytest.approx(0.05)
    assert guard.state.calls_used == 1


def test_threadpool_consume_records_active_goal() -> None:
    """Worker-thread consume calls are attributed to the active goal."""
    guard = BudgetGuard(max_cost_usd=10.0)

    with guard.goal("threadpool-goal", verifier=lambda: True) as g:
        g.attempt()
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(
                lambda: guard.consume(tokens=10, calls=1, cost_usd=0.03)
            ).result()

    assert g.succeeded is True
    assert g.cost_usd == pytest.approx(0.03)
    assert len(g.calls) == 1
    assert guard.state.cost_used == pytest.approx(0.03)


def test_concurrent_threadpool_consumes_record_active_goal() -> None:
    """Concurrent worker-thread consume calls keep the goal ledger complete."""
    guard = BudgetGuard(max_cost_usd=10.0)

    with guard.goal("concurrent-threadpool-goal", verifier=lambda: True) as g:
        g.attempt()
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    lambda: guard.consume(tokens=10, calls=1, cost_usd=0.01)
                )
                for _ in range(20)
            ]
            for future in futures:
                future.result()

    assert g.succeeded is True
    assert g.cost_usd == pytest.approx(0.20)
    assert len(g.calls) == 20
    assert guard.state.cost_used == pytest.approx(0.20)


def test_to_dict_is_json_serializable() -> None:
    import json

    guard = BudgetGuard(max_cost_usd=1.0)
    with guard.goal("serialize-me", verifier=lambda: True) as g:
        g.attempt()
        guard.consume(tokens=10, calls=1, cost_usd=0.01)

    payload = g.to_dict()
    # Must round-trip through JSON without error.
    serialized = json.dumps(payload)
    parsed = json.loads(serialized)
    assert parsed["name"] == "serialize-me"
    assert parsed["succeeded"] is True
    assert parsed["attempts"] == 1
    assert parsed["cost_usd"] == pytest.approx(0.01)
    assert len(parsed["calls"]) == 1
