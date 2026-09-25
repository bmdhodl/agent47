"""Two workers can both pass check() and both dispatch.

This characterizes in-memory BudgetGuard overshoot. It is not the store-backed
OpenAI path. That path is reserved_one_dispatch.py. There is no network.
"""
from __future__ import annotations

import json
import threading

from agentguard import BudgetExceeded, BudgetGuard


def main() -> None:
    guard = BudgetGuard(max_calls=1)
    workers = 2
    barrier = threading.Barrier(workers)
    lock = threading.Lock()
    dispatched = []
    consume_ok = []
    consume_blocked = []

    def worker() -> None:
        guard.check()
        barrier.wait()
        with lock:
            dispatched.append(1)
        try:
            guard.consume(calls=1)
            with lock:
                consume_ok.append(1)
        except BudgetExceeded:
            with lock:
                consume_blocked.append(1)

    threads = [threading.Thread(target=worker) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    payload = {
        "limit_calls": 1,
        "workers": workers,
        "dispatched": len(dispatched),
        "consume_succeeded": len(consume_ok),
        "consume_blocked": len(consume_blocked),
        "recorded_calls": guard.state.calls_used,
        "overshoot": len(dispatched) > 1 and guard.state.calls_used > 1,
        "fixed": False,
        "note": (
            "check() does not reserve. consume() increments then raises, "
            "so recorded_calls can exceed limit_calls while consume_blocked is 1."
        ),
    }
    print(json.dumps(payload, indent=2))
    if not payload["overshoot"]:
        raise SystemExit("expected current overshoot was not observed")


if __name__ == "__main__":
    main()
