"""Behavioral regressions found during the September SDK release audit."""
import threading
from urllib.request import Request

import pytest

from agentguard import BudgetExceeded, BudgetGuard, TimeoutGuard, X402SpendGuard
from agentguard.sinks.http import _SsrfSafeRedirectHandler, _validate_url


@pytest.mark.parametrize("field", ["max_tokens", "max_calls", "max_cost_usd"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True, "5"])
def test_budget_rejects_invalid_caps(field, value):
    # REGRESSION: NaN limits silently disabled enforcement.
    with pytest.raises((TypeError, ValueError)):
        BudgetGuard(**{field: value})


@pytest.mark.parametrize("field", ["max_total_usd", "max_per_endpoint_usd", "max_per_call_usd"])
@pytest.mark.parametrize("value", [float("nan"), float("inf"), -1, True, "5"])
def test_payment_rejects_invalid_caps(field, value):
    with pytest.raises((TypeError, ValueError)):
        X402SpendGuard(**{field: value})


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True])
def test_timeout_rejects_invalid_cap(value):
    with pytest.raises((TypeError, ValueError)):
        TimeoutGuard(value)


@pytest.mark.parametrize("field", ["max_tokens", "max_calls", "max_cost_usd"])
def test_zero_budget_allows_zero_usage_with_warning(field):
    # REGRESSION: a zero cap divided by zero in the warning calculation.
    guard = BudgetGuard(**{field: 0}, warn_at_pct=0.8)
    guard.consume()


def test_warning_callback_can_reenter_guard():
    # REGRESSION: callback ran under a non-reentrant lock and hung forever.
    called = []
    guard = BudgetGuard(max_calls=5, warn_at_pct=0.5,
                        on_warning=lambda _: (called.append(True), guard.consume(calls=1)))
    thread = threading.Thread(target=lambda: guard.consume(calls=3), daemon=True)
    thread.start()
    thread.join(timeout=2)
    assert not thread.is_alive(), "warning callback deadlocked"
    assert called == [True]
    assert guard.state.calls_used == 4


@pytest.mark.parametrize("rollover", [True, False])
def test_old_payment_failure_does_not_refund_new_period(rollover):
    # REGRESSION: a failed in-flight charge refunded unrelated new-period spend.
    clock = [1_753_000_000.0]
    guard = X402SpendGuard(max_total_usd=1, period="day", now=lambda: clock[0])

    def failing_payment():
        if rollover:
            clock[0] += 86400
        else:
            guard.reset()
        guard.charge(0.75, "endpoint", lambda: None)
        raise ConnectionError("old payment failed")

    with pytest.raises(ConnectionError):
        guard.charge(0.5, "endpoint", failing_payment)
    assert guard.total_spent_usd == 0.75
    with pytest.raises(BudgetExceeded):
        guard.charge(0.5, "endpoint", lambda: pytest.fail("over-cap payment ran"))


@pytest.mark.parametrize("host", ["[::ffff:127.0.0.1]", "[::ffff:169.254.169.254]"])
def test_ipv4_mapped_private_addresses_are_blocked(host):
    # REGRESSION: IPv4-mapped IPv6 bypassed IPv4 network checks.
    with pytest.raises(ValueError):
        _validate_url("https://" + host + "/ingest")


def test_cross_origin_redirect_does_not_forward_credentials():
    # REGRESSION: urllib copied Authorization onto another origin's request.
    request = Request("https://8.8.8.8/ingest", headers={"Authorization": "Bearer test"})
    with pytest.raises(ValueError):
        _SsrfSafeRedirectHandler().redirect_request(
            request, None, 302, "Found", {}, "https://1.1.1.1/collect")
