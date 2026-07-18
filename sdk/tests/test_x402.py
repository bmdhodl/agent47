"""Tests for X402SpendGuard: x402/USDC micropayment spend caps."""
import math

import pytest

from agentguard import BudgetExceeded, X402SpendGuard


def make_pay(ledger):
    def pay(amount, endpoint):
        ledger.append((amount, endpoint))
        return "paid"
    return pay


def test_requires_at_least_one_cap():
    with pytest.raises(ValueError):
        X402SpendGuard()


def test_at_cap_allowed_above_refused():
    guard = X402SpendGuard(max_total_usd=5.00)
    paid = []
    assert guard.charge(5.00, "https://a.example/x", make_pay(paid), 5.00, "a") == "paid"
    assert len(paid) == 1
    with pytest.raises(BudgetExceeded):
        guard.charge(0.01, "https://a.example/x", make_pay(paid), 0.01, "a")
    assert len(paid) == 1  # refused payment never ran
    assert guard.total_spent_usd == 5.00


def test_per_call_ceiling_refuses_before_paying():
    guard = X402SpendGuard(max_per_call_usd=0.10)
    paid = []
    with pytest.raises(BudgetExceeded, match="per-call ceiling"):
        guard.charge(0.25, "https://a.example/x", make_pay(paid), 0.25, "a")
    assert paid == []
    assert guard.total_spent_usd == 0.0


def test_per_endpoint_isolation():
    guard = X402SpendGuard(max_per_endpoint_usd=1.00)
    paid = []
    guard.charge(1.00, "https://a.example/x", make_pay(paid), 1.00, "a")
    with pytest.raises(BudgetExceeded, match="endpoint budget"):
        guard.charge(0.01, "https://a.example/x", make_pay(paid), 0.01, "a")
    # a different endpoint still has its own full budget
    guard.charge(1.00, "https://b.example/y", make_pay(paid), 1.00, "b")
    assert guard.endpoint_spent_usd("https://a.example/x") == 1.00
    assert guard.endpoint_spent_usd("https://b.example/y") == 1.00


def test_rollback_on_payment_failure():
    guard = X402SpendGuard(max_total_usd=1.00)

    def failing_pay():
        raise ConnectionError("facilitator unreachable")

    with pytest.raises(ConnectionError):
        guard.charge(0.50, "https://a.example/x", failing_pay)
    assert guard.total_spent_usd == 0.0
    assert guard.endpoint_spent_usd("https://a.example/x") == 0.0


def test_period_day_resets_at_utc_boundary():
    clock = [1_753_000_000.0]  # fixed epoch
    guard = X402SpendGuard(max_total_usd=1.00, period="day", now=lambda: clock[0])
    paid = []
    guard.charge(1.00, "https://a.example/x", make_pay(paid), 1.00, "a")
    with pytest.raises(BudgetExceeded):
        guard.check(0.01, "https://a.example/x")
    clock[0] += 86_400  # next UTC day
    assert guard.total_spent_usd == 0.0
    guard.charge(1.00, "https://a.example/x", make_pay(paid), 1.00, "a")
    assert len(paid) == 2


def test_check_records_nothing():
    guard = X402SpendGuard(max_total_usd=1.00)
    guard.check(0.50, "https://a.example/x")
    assert guard.total_spent_usd == 0.0


def test_record_matches_budget_guard_semantics():
    guard = X402SpendGuard(max_total_usd=1.00)
    guard.record(0.75, "https://a.example/x")
    # recorded first, then raises: the settled spend stays on the books
    with pytest.raises(BudgetExceeded):
        guard.record(0.50, "https://a.example/x")
    assert guard.total_spent_usd == 1.25


def test_record_enforces_per_call_ceiling():
    guard = X402SpendGuard(max_per_call_usd=0.10)
    with pytest.raises(BudgetExceeded, match="per-call"):
        guard.record(5.00, "https://a.example/x")
    assert guard.total_spent_usd == 5.00  # settled spend stays on the books


def test_warning_fires_once_at_threshold():
    warnings = []
    guard = X402SpendGuard(max_total_usd=1.00, warn_at_pct=0.8, on_warning=warnings.append)
    paid = []
    guard.charge(0.50, "https://a.example/x", make_pay(paid), 0.50, "a")
    assert warnings == []
    guard.charge(0.30, "https://a.example/x", make_pay(paid), 0.30, "a")
    assert len(warnings) == 1
    guard.charge(0.10, "https://a.example/x", make_pay(paid), 0.10, "a")
    assert len(warnings) == 1  # one-shot


def test_invalid_amounts_raise_loudly():
    guard = X402SpendGuard(max_total_usd=1.00)
    with pytest.raises(ValueError):
        guard.check(-0.01, "https://a.example/x")
    with pytest.raises(ValueError):
        guard.check(math.nan, "https://a.example/x")
    with pytest.raises(TypeError):
        guard.check("0.01", "https://a.example/x")


def test_refusal_is_budget_exceeded_and_agentguard_error():
    from agentguard import AgentGuardError

    guard = X402SpendGuard(max_per_call_usd=0.01)
    with pytest.raises(AgentGuardError):
        guard.check(1.00, "https://a.example/x")
