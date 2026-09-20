"""Barrier two-worker first-use against the AG-03 reservation model.

This is the contract proof, not a BudgetGuard fix. Current check()/consume()
still overshoots; see examples/enforcement_boundary/two_worker_overshoot.py.
"""
from __future__ import annotations

import json
import sys
import threading
from pathlib import Path

_SDK = Path(__file__).resolve().parents[2] / "sdk"
if str(_SDK) not in sys.path:
    sys.path.insert(0, str(_SDK))

from agentguard import BudgetExceeded
from agentguard._reservation_contract import ReservationLedger


def main() -> None:
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
                ledger = ReservationLedger.from_store_state(state.get("k"), max_calls=1)
                ledger.reserve(reservation_id, calls=1)
                state["k"] = ledger.to_store_state()
            with hold:
                admitted.append(reservation_id)
        except BudgetExceeded:
            with hold:
                blocked.append(reservation_id)

    threads = [threading.Thread(target=worker, args=(name,)) for name in ("a", "b")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    payload = {
        "limit_calls": 1,
        "workers": 2,
        "admitted": len(admitted),
        "blocked": len(blocked),
        "held_calls": ReservationLedger.from_store_state(
            state.get("k"), max_calls=1
        ).held()["calls"],
        "wired_into_budget_guard": False,
    }
    print(json.dumps(payload, indent=2))
    if payload["admitted"] != 1 or payload["blocked"] != 1:
        raise SystemExit("expected exactly one admitted reserve")


if __name__ == "__main__":
    main()
