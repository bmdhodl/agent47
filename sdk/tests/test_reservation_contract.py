"""AG-03: local reservation and reconciliation contract (design only)."""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import agentguard
from agentguard import BudgetExceeded, StateStoreError
from agentguard._reservation_contract import (
    MissingBound,
    ReservationContractError,
    ReservationLedger,
    can_claim_invoice_cap,
)

ROOT = Path(__file__).resolve().parents[2]
ADR = ROOT / "docs" / "guides" / "reservation-contract.md"
MODEL = ROOT / "sdk" / "agentguard" / "_reservation_contract.py"


def _ledger(**kwargs):
    defaults = {"max_calls": 1}
    defaults.update(kwargs)
    return ReservationLedger(**defaults)


def test_reservation_contract_is_not_public_api():
    assert "ReservationLedger" not in agentguard.__all__
    assert "MissingBound" not in agentguard.__all__
    assert not hasattr(agentguard, "ReservationLedger")


def test_cannot_claim_invoice_cap():
    assert can_claim_invoice_cap() is False


def test_concurrent_first_use_admits_one():
    lock = threading.Lock()
    state = {}
    barrier = threading.Barrier(2)
    admitted = []
    blocked = []
    hold = threading.Lock()

    def worker(reservation_id: str) -> None:
        barrier.wait()
        try:
            with lock:
                ledger = ReservationLedger.from_store_state(
                    state.get("k"), max_calls=1
                )
                ledger.reserve(reservation_id, calls=1)
                state["k"] = ledger.to_store_state()
            with hold:
                admitted.append(reservation_id)
        except BudgetExceeded:
            with hold:
                blocked.append(reservation_id)

    threads = [
        threading.Thread(target=worker, args=(name,))
        for name in ("a", "b")
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(admitted) == 1
    assert len(blocked) == 1
    ledger = ReservationLedger.from_store_state(state["k"], max_calls=1)
    assert ledger.held()["calls"] == 1
    assert ledger.calls_used == 0


def test_zero_budget_refuses_without_record():
    ledger = _ledger(max_calls=0)
    with pytest.raises(BudgetExceeded):
        ledger.reserve("a", calls=1)
    assert ledger.reservations == {}


def test_exactly_at_limit_refuses_next_reserve():
    ledger = _ledger(max_calls=1)
    ledger.reserve("a", calls=1)
    ledger.commit("a", tokens=0, cost_usd=0.0)
    assert ledger.calls_used == 1
    with pytest.raises(BudgetExceeded):
        ledger.reserve("b", calls=1)


def test_process_death_does_not_free_funds():
    ledger = _ledger(max_calls=1)
    ledger.reserve("a", calls=1)
    ledger.recover_crash("a")
    rec = ledger.reservations["a"]
    assert rec["status"] == "unresolved"
    assert rec["unresolved_reason"] == "process_death"
    assert ledger.held()["calls"] == 1
    with pytest.raises(ReservationContractError, match="cannot silently free"):
        ledger.cancel("a")
    with pytest.raises(BudgetExceeded):
        ledger.reserve("b", calls=1)


def test_timeout_holds_unresolved():
    ledger = _ledger(max_calls=1)
    ledger.reserve("a", calls=1)
    ledger.mark_unresolved("a", reason="timeout")
    assert ledger.reservations["a"]["status"] == "unresolved"
    assert ledger.held()["calls"] == 1


def test_cancel_before_send_releases_hold():
    ledger = _ledger(max_calls=1)
    ledger.reserve("a", calls=1)
    ledger.cancel("a", dispatch_never_sent=True)
    assert ledger.reservations["a"]["status"] == "cancelled"
    assert ledger.held()["calls"] == 0
    ledger.reserve("b", calls=1)
    assert "b" in ledger.reservations


def test_operator_may_cancel_unresolved_only_with_attestation():
    ledger = _ledger(max_calls=1)
    ledger.reserve("a", calls=1)
    ledger.mark_unresolved("a", reason="timeout")
    ledger.cancel("a", operator_attests_never_dispatched=True)
    assert ledger.held()["calls"] == 0


def test_old_state_without_reservations_is_readable():
    ledger = ReservationLedger.from_store_state(
        {"tokens_used": 2, "calls_used": 1, "cost_used": 0.01},
        max_calls=2,
    )
    assert ledger.calls_used == 1
    assert ledger.reservations == {}
    ledger.reserve("a", calls=1)
    assert ledger.held()["calls"] == 1


def test_corrupt_state_fails_closed():
    with pytest.raises(StateStoreError):
        ReservationLedger.from_store_state(
            {"calls_used": "nope"},
            max_calls=1,
        )
    with pytest.raises(StateStoreError):
        ReservationLedger.from_store_state(
            {"calls_used": 0, "reservations": []},
            max_calls=1,
        )


def test_cost_cap_requires_bound():
    ledger = ReservationLedger(max_cost_usd=1.0)
    with pytest.raises(MissingBound, match="dollar stop"):
        ledger.reserve("a", calls=1)
    ledger.reserve("a", calls=1, cost_bound=0.40, price_table_version="2026.07.15")
    rec = ledger.commit("a", tokens=10, cost_usd=0.50)
    assert rec["estimate_overrun"] is True
    assert ledger.cost_used == 0.50


def test_double_settlement_is_idempotent_then_conflict():
    ledger = _ledger(max_calls=2)
    ledger.reserve("a", calls=1)
    ledger.commit("a", tokens=3, cost_usd=0.01)
    again = ledger.commit("a", tokens=3, cost_usd=0.01)
    assert again["status"] == "committed"
    with pytest.raises(ReservationContractError, match="different usage"):
        ledger.commit("a", tokens=9, cost_usd=0.01)
    with pytest.raises(ReservationContractError, match="committed"):
        ledger.cancel("a", dispatch_never_sent=True)


def test_period_buckets_do_not_copy_unresolved():
    day1 = ReservationLedger(max_calls=1, period_bucket="fleet:2026-09-20")
    day1.reserve("a", calls=1)
    day1.recover_crash("a")
    day2 = ReservationLedger.from_store_state(
        None, max_calls=1, period_bucket="fleet:2026-09-21"
    )
    day2.reserve("b", calls=1)
    assert day1.held()["calls"] == 1
    assert day2.held()["calls"] == 1
    assert day1.reservations["a"]["period_bucket"] == "fleet:2026-09-20"


def test_adr_transition_table_and_native_alternative():
    text = ADR.read_text(encoding="utf-8")
    for needle in (
        "Unknown provider outcome cannot silently free funds",
        "Native-first alternative",
        "can_claim_invoice_cap()",
        "dispatch_never_sent=True",
        "operator_attests_never_dispatched=True",
        "JsonFileStateStore",
        "AG-04",
        "Viewport and host allow/deny",
        "LiteLLM budget reservation",
        "max_list_cost",
        "max_turns",
    ):
        assert needle in text, needle
    assert "No public SDK API is added" in text


def test_protocol_edges_fail_closed():
    with pytest.raises(ValueError, match="Provide"):
        ReservationLedger()
    ledger = _ledger(max_calls=2, max_tokens=100, max_cost_usd=1.0)
    with pytest.raises(ReservationContractError, match="reservation_id"):
        ledger.reserve("", calls=1, tokens_bound=1, cost_bound=0.1)
    with pytest.raises(ReservationContractError, match="at least 1"):
        ledger.reserve("z", calls=0, tokens_bound=1, cost_bound=0.1)
    with pytest.raises(ReservationContractError, match="must be a number"):
        ledger.reserve("z", calls="1", tokens_bound=1, cost_bound=0.1)  # type: ignore[arg-type]
    with pytest.raises(ReservationContractError, match="finite"):
        ledger.reserve("z", calls=1, tokens_bound=1, cost_bound=float("nan"))
    with pytest.raises(ReservationContractError, match="non-negative"):
        ledger.reserve("z", calls=1, tokens_bound=-1, cost_bound=0.1)
    with pytest.raises(MissingBound, match="token stop"):
        ReservationLedger(max_tokens=10).reserve("z", calls=1)
    ledger.reserve("a", calls=1, tokens_bound=10, cost_bound=0.1)
    same = ledger.reserve("a", calls=1, tokens_bound=10, cost_bound=0.1)
    assert same["status"] == "reserved"
    with pytest.raises(ReservationContractError, match="different bounds"):
        ledger.reserve("a", calls=1, tokens_bound=20, cost_bound=0.1)
    with pytest.raises(BudgetExceeded, match="Token budget"):
        ledger.reserve("b", calls=1, tokens_bound=1000, cost_bound=0.1)
    with pytest.raises(BudgetExceeded, match="Cost budget"):
        ledger.reserve("c", calls=1, tokens_bound=1, cost_bound=5.0)
    ledger.cancel("a", dispatch_never_sent=True)
    assert ledger.cancel("a", dispatch_never_sent=True)["status"] == "cancelled"
    with pytest.raises(ReservationContractError, match="cancelled"):
        ledger.commit("a")
    with pytest.raises(ReservationContractError, match="is cancelled"):
        ledger.reserve("a", calls=1, tokens_bound=1, cost_bound=0.1)
    with pytest.raises(ReservationContractError, match="unknown reservation"):
        ledger.commit("missing")
    with pytest.raises(ReservationContractError, match="mark unresolved"):
        ledger.mark_unresolved("a", reason="timeout")
    with pytest.raises(StateStoreError, match="must be an object"):
        ReservationLedger.from_store_state(
            {"calls_used": 0, "reservations": {"x": "nope"}},
            max_calls=1,
        )
    with pytest.raises(StateStoreError, match="status is invalid"):
        ReservationLedger.from_store_state(
            {"calls_used": 0, "reservations": {"x": {"status": "nope", "calls": 1}}},
            max_calls=1,
        )
    with pytest.raises(StateStoreError, match="price_table_version"):
        ReservationLedger.from_store_state(
            {
                "calls_used": 0,
                "reservations": {
                    "x": {"status": "reserved", "calls": 1, "price_table_version": 1}
                },
            },
            max_calls=1,
        )
    old = ReservationLedger.from_store_state(
        {"calls_used": 0, "reservations": None},
        max_calls=1,
    )
    assert old.reservations == {}
    hold = _ledger(max_calls=2)
    hold.reservations["u"] = {
        "status": "unresolved",
        "calls": 1,
        "tokens_bound": None,
        "cost_bound": None,
    }
    held = hold.held()
    assert held["unbounded_tokens"] is True
    assert held["unbounded_cost"] is True
    hold.mark_unresolved("u", reason="timeout-again")
    assert hold.reservations["u"]["unresolved_reason"] == "timeout-again"


def test_unresolved_commit_settles_actual_usage():
    ledger = _ledger(max_calls=1)
    ledger.reserve("a", calls=1)
    ledger.mark_unresolved("a", reason="timeout")
    ledger.commit("a", tokens=4, cost_usd=0.02)
    assert ledger.calls_used == 1
    assert ledger.held()["calls"] == 0
    assert ledger.reservations["a"]["status"] == "committed"


def test_budget_guard_still_overshoots_without_this_model():
    from agentguard import BudgetGuard

    guard = BudgetGuard(max_calls=1)
    barrier = threading.Barrier(2)
    dispatched = []
    hold = threading.Lock()

    def worker() -> None:
        guard.check()
        barrier.wait()
        with hold:
            dispatched.append(1)
        try:
            guard.consume(calls=1)
        except BudgetExceeded:
            pass

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(dispatched) == 2
    assert guard.state.calls_used > 1


@pytest.mark.integration
def test_reservation_model_runs_from_installed_distribution(tmp_path):
    target = tmp_path / "site-packages"
    install = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            str(ROOT / "sdk"),
            "--target",
            str(target),
            "--no-deps",
            "--disable-pip-version-check",
        ],
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stderr or install.stdout
    env = os.environ.copy()
    env["PYTHONPATH"] = str(target)
    env.pop("PYTHONHOME", None)
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import pathlib, agentguard, agentguard._reservation_contract as rc;"
                "assert 'ReservationLedger' not in agentguard.__all__;"
                "ledger=rc.ReservationLedger(max_calls=1);"
                "ledger.reserve('a', calls=1);"
                "ledger.recover_crash('a');"
                "assert ledger.held()['calls']==1;"
                "print(pathlib.Path(rc.__file__).resolve());"
                "print('HELD')"
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr
    lines = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
    installed = Path(lines[0]).resolve()
    assert lines[1] == "HELD"
    assert target.resolve() in installed.parents or installed.parent == target.resolve()
    assert installed != MODEL.resolve()


def test_proof_artifacts_are_plain_text():
    folder = ROOT / "proof" / "ag-03-reservation-contract"
    for path in folder.iterdir():
        if path.suffix not in {".txt", ".json", ".md", ".py"}:
            continue
        data = path.read_bytes()
        assert b"\x1b" not in data, path.name


def test_showwork_snapshots_suppress_git_diff():
    """Keep Claude review under the 200k `gh pr diff` cap.

    Snapshot JSON is still stored as LF text; `-diff` only hides the body
    from patches so `_reservation_contract.py` stays visible.
    """
    attrs = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert ".showwork/snapshots/*.json text eol=lf -diff" in attrs
    probe = subprocess.run(
        [
            "git",
            "check-attr",
            "diff",
            "text",
            "eol",
            "--",
            ".showwork/snapshots/ag-03-reservation-contract.json",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "diff: unset" in probe.stdout
    assert "text: set" in probe.stdout
    assert "eol: lf" in probe.stdout
