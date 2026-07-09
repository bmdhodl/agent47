"""Tests for goal-level metering (BudgetGuard.goal)."""
from __future__ import annotations

import threading
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


def test_plain_thread_without_submitted_context_is_not_attributed() -> None:
    """Unrelated threads do not inherit the active goal by guard-wide fallback."""
    guard = BudgetGuard(max_cost_usd=10.0)

    with guard.goal("main-thread-goal", verifier=lambda: True) as g:
        g.attempt()
        worker = threading.Thread(
            target=lambda: guard.consume(tokens=10, calls=1, cost_usd=0.04)
        )
        worker.start()
        worker.join()

    assert g.succeeded is True
    assert g.cost_usd == pytest.approx(0.0)
    assert len(g.calls) == 0
    assert guard.state.cost_used == pytest.approx(0.04)


def test_concurrent_goal_blocks_keep_threadpool_attribution_separate() -> None:
    """Concurrent goals on one guard propagate their own submitted context."""
    guard = BudgetGuard(max_cost_usd=10.0)
    barrier = threading.Barrier(2)
    costs = {}

    def run_goal(name: str, cost_usd: float) -> None:
        with guard.goal(name, verifier=lambda: True) as g:
            g.attempt()
            barrier.wait()
            with ThreadPoolExecutor(max_workers=1) as executor:
                executor.submit(
                    lambda: guard.consume(tokens=10, calls=1, cost_usd=cost_usd)
                ).result()
        costs[name] = g.cost_usd

    thread_a = threading.Thread(target=run_goal, args=("goal-a", 0.03))
    thread_b = threading.Thread(target=run_goal, args=("goal-b", 0.07))
    thread_a.start()
    thread_b.start()
    thread_a.join()
    thread_b.join()

    assert costs == {"goal-a": pytest.approx(0.03), "goal-b": pytest.approx(0.07)}
    assert guard.state.cost_used == pytest.approx(0.10)


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


def test_goal_max_cost_usd_raises() -> None:
    """Per-goal hard cap raises even when session budget still has headroom."""
    from agentguard import BudgetExceeded

    guard = BudgetGuard(max_cost_usd=50.0)
    with pytest.raises(BudgetExceeded, match="Goal 'tiny-task' cost budget exceeded"):
        with guard.goal("tiny-task", verifier=lambda: True, max_cost_usd=0.50) as g:
            g.attempt()
            guard.consume(cost_usd=0.40)
            guard.consume(cost_usd=0.20)  # 0.60 > 0.50 goal; session still under 50
    # Attribution-before-raise: ledger includes the tripping call.
    assert g.cost_usd == pytest.approx(0.60)
    # Session state also advanced (same consume path).
    assert guard.state.cost_used == pytest.approx(0.60)


def test_goal_under_cap_completes() -> None:
    guard = BudgetGuard(max_cost_usd=10.0)
    with guard.goal("ok", verifier=lambda: True, max_cost_usd=1.0) as g:
        g.attempt()
        guard.consume(cost_usd=0.25, tokens=10, calls=1)
    assert g.succeeded is True
    assert g.cost_usd == pytest.approx(0.25)


def test_session_cap_lower_than_goal_cap() -> None:
    """Whichever limit trips first wins — session can still stop first."""
    from agentguard import BudgetExceeded

    guard = BudgetGuard(max_cost_usd=0.30)
    with pytest.raises(BudgetExceeded) as ei:
        with guard.goal("roomy", verifier=lambda: True, max_cost_usd=5.0) as g:
            g.attempt()
            guard.consume(cost_usd=0.20)
            guard.consume(cost_usd=0.20)
    # Session message does not use Goal prefix.
    assert "Goal " not in str(ei.value)
    assert "Cost budget exceeded" in str(ei.value)


def test_nested_goal_child_cap_independent() -> None:
    from agentguard import BudgetExceeded

    guard = BudgetGuard(max_cost_usd=100.0)
    with guard.goal("parent", verifier=lambda: True, max_cost_usd=10.0) as parent:
        parent.attempt()
        guard.consume(cost_usd=0.10)
        with pytest.raises(BudgetExceeded, match="Goal 'child-a'"):
            with guard.goal("child-a", verifier=lambda: True, max_cost_usd=0.20) as child:
                child.attempt()
                guard.consume(cost_usd=0.15)
                guard.consume(cost_usd=0.15)
        # Sibling can still run under its own cap after child exceeded.
        with guard.goal("child-b", verifier=lambda: True, max_cost_usd=1.0) as child_b:
            child_b.attempt()
            guard.consume(cost_usd=0.05)
        assert child_b.cost_usd == pytest.approx(0.05)
    # Parent rollup includes child-a tripping call + child-b + own.
    assert parent.cost_usd == pytest.approx(0.10 + 0.30 + 0.05)


def test_goal_token_and_call_caps() -> None:
    from agentguard import BudgetExceeded

    guard = BudgetGuard(max_tokens=10_000, max_calls=100)
    with pytest.raises(BudgetExceeded, match="token budget exceeded"):
        with guard.goal("tok", verifier=lambda: True, max_tokens=50) as g:
            g.attempt()
            guard.consume(tokens=40, calls=1, cost_usd=0.0)
            guard.consume(tokens=20, calls=1, cost_usd=0.0)
    with pytest.raises(BudgetExceeded, match="call budget exceeded"):
        with guard.goal("calls", verifier=lambda: True, max_calls=2) as g:
            g.attempt()
            guard.consume(calls=1, cost_usd=0.0)
            guard.consume(calls=1, cost_usd=0.0)
            guard.consume(calls=1, cost_usd=0.0)


def test_goal_failure_cost_with_cap() -> None:
    """Multi-attempt success still attributes failure_cost when under cap."""
    guard = BudgetGuard(max_cost_usd=10.0)
    ok = {"v": False}
    with guard.goal("retry", verifier=lambda: ok["v"], max_cost_usd=5.0) as g:
        g.attempt()
        guard.consume(cost_usd=0.10)
        g.attempt()
        guard.consume(cost_usd=0.10)
        g.attempt()
        guard.consume(cost_usd=0.05)
        ok["v"] = True
    assert g.succeeded is True
    assert g.failure_cost == pytest.approx(0.20)
    assert g.cost_usd == pytest.approx(0.25)


def test_goal_negative_limit_rejected() -> None:
    guard = BudgetGuard(max_cost_usd=1.0)
    with pytest.raises(ValueError, match="max_cost_usd"):
        guard.goal("bad", verifier=lambda: True, max_cost_usd=-1.0)


def test_goal_limit_fuzz_under_never_raises() -> None:
    """Random sequences under both caps never raise BudgetExceeded."""
    import random

    rng = random.Random(42)
    for _ in range(30):
        # Fresh session budget each trial so session total does not accumulate.
        guard = BudgetGuard(max_cost_usd=10.0)
        with guard.goal("fuzz", verifier=lambda: True, max_cost_usd=1.0) as g:
            g.attempt()
            spent = 0.0
            for _step in range(20):
                c = rng.random() * 0.05
                if spent + c > 0.95:
                    break
                guard.consume(cost_usd=c)
                spent += c
        assert g.succeeded is True


def test_goal_limit_fuzz_over_always_raises() -> None:
    import random
    from agentguard import BudgetExceeded

    rng = random.Random(7)
    guard = BudgetGuard(max_cost_usd=100.0)
    for _ in range(20):
        raised = False
        try:
            with guard.goal("blow", verifier=lambda: True, max_cost_usd=0.10) as g:
                g.attempt()
                for _step in range(50):
                    guard.consume(cost_usd=rng.uniform(0.03, 0.08))
        except BudgetExceeded as e:
            raised = True
            assert "Goal " in str(e)
        assert raised, "expected BudgetExceeded within 50 consumes"


def test_goal_rejects_nonfinite_max_cost() -> None:
    guard = BudgetGuard(max_cost_usd=1.0)
    with pytest.raises(ValueError, match="finite"):
        guard.goal("x", verifier=lambda: True, max_cost_usd=float("nan"))


def test_goal_warning_fires_once() -> None:
    msgs = []
    goals = []

    def on_warn(g, msg: str) -> None:
        goals.append(g.name)
        msgs.append(msg)

    guard = BudgetGuard(max_cost_usd=50.0)
    with guard.goal(
        "warn-me",
        verifier=lambda: True,
        max_cost_usd=1.0,
        warn_at_pct=0.8,
        on_warning=on_warn,
    ) as g:
        g.attempt()
        guard.consume(cost_usd=0.70)
        assert msgs == []
        guard.consume(cost_usd=0.15)
        assert len(msgs) == 1
        assert "Goal 'warn-me'" in msgs[0]
        assert goals == ["warn-me"]
        guard.consume(cost_usd=0.04)
        assert len(msgs) == 1
    assert g.succeeded is True


def test_goal_warning_does_not_raise() -> None:
    from agentguard import BudgetExceeded

    msgs = []
    guard = BudgetGuard(max_cost_usd=50.0)
    with pytest.raises(BudgetExceeded, match="Goal 'hard'"):
        with guard.goal(
            "hard",
            verifier=lambda: True,
            max_cost_usd=0.50,
            warn_at_pct=0.5,
            on_warning=lambda g, m: msgs.append(m),
        ) as g:
            g.attempt()
            guard.consume(cost_usd=0.30)
            guard.consume(cost_usd=0.30)
    assert len(msgs) == 1
    assert abs(g.cost_usd - 0.60) < 1e-9


def test_goal_and_session_warnings_independent() -> None:
    session_msgs = []
    goal_msgs = []
    guard = BudgetGuard(
        max_cost_usd=10.0,
        warn_at_pct=0.9,
        on_warning=lambda m: session_msgs.append(m),
    )
    with guard.goal(
        "g2",
        verifier=lambda: True,
        max_cost_usd=1.0,
        warn_at_pct=0.5,
        on_warning=lambda g, m: goal_msgs.append(m),
    ) as g:
        g.attempt()
        guard.consume(cost_usd=0.55)
        assert len(goal_msgs) == 1
        assert session_msgs == []


def test_nested_goal_child_warning_isolated() -> None:
    parent_msgs = []
    child_msgs = []
    guard = BudgetGuard(max_cost_usd=50.0)
    with guard.goal(
        "parent",
        verifier=lambda: True,
        max_cost_usd=10.0,
        warn_at_pct=0.8,
        on_warning=lambda g, m: parent_msgs.append(m),
    ) as parent:
        parent.attempt()
        with guard.goal(
            "child",
            verifier=lambda: True,
            max_cost_usd=1.0,
            warn_at_pct=0.5,
            on_warning=lambda g, m: child_msgs.append(m),
        ) as child:
            child.attempt()
            guard.consume(cost_usd=0.60)
            assert len(child_msgs) == 1
            assert parent_msgs == []


def test_goal_warn_requires_max() -> None:
    guard = BudgetGuard(max_cost_usd=5.0)
    with pytest.raises(ValueError, match="warn_at_pct requires"):
        guard.goal("x", verifier=lambda: True, warn_at_pct=0.8)


def test_goal_on_warning_exception_propagates() -> None:
    def boom(g, msg: str) -> None:
        raise RuntimeError("callback failed")

    guard = BudgetGuard(max_cost_usd=50.0)
    with pytest.raises(RuntimeError, match="callback failed"):
        with guard.goal(
            "x",
            verifier=lambda: True,
            max_cost_usd=1.0,
            warn_at_pct=0.5,
            on_warning=boom,
        ) as g:
            g.attempt()
            guard.consume(cost_usd=0.60)


def test_goal_warn_fuzz_under_threshold_no_callback() -> None:
    import random

    rng = random.Random(1)
    for _ in range(25):
        msgs = []
        guard = BudgetGuard(max_cost_usd=20.0)
        with guard.goal(
            "f",
            verifier=lambda: True,
            max_cost_usd=1.0,
            warn_at_pct=0.8,
            on_warning=lambda g, m: msgs.append(m),
        ) as g:
            g.attempt()
            spent = 0.0
            for _s in range(30):
                c = rng.random() * 0.05
                if spent + c >= 0.79:
                    break
                guard.consume(cost_usd=c)
                spent += c
        assert msgs == []
