"""Two processes, one remaining call, one mock dispatch.

Store-backed sync OpenAI Chat Completions (non-stream) reserves before send.
The other worker is refused before its mock runs. In-memory ``check()`` still
overshoots; see ``two_worker_overshoot.py``. No network. Spawn is the start
method so the same script is the Windows and Linux entrypoint. This
environment records Linux results; it does not execute Windows.
"""
from __future__ import annotations

import json
import multiprocessing
import tempfile
from pathlib import Path
from types import SimpleNamespace


def _worker(store_path: str, log_path: str, barrier: multiprocessing.Barrier, queue: multiprocessing.Queue) -> None:
    from agentguard import BudgetExceeded, BudgetGuard, JsonFileStateStore, Tracer
    from agentguard.instrument import _traced_openai_create

    class _Drop:
        def emit(self, _event: object) -> None:
            return None

    def original(*_args: object, **_kwargs: object) -> SimpleNamespace:
        with open(log_path, "a", encoding="utf-8") as handle:
            handle.write("1\n")
        return SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2)
        )

    guard = BudgetGuard(max_calls=1, store=JsonFileStateStore(store_path), key="fleet")
    tracer = Tracer(sink=_Drop(), service="reservation-race", watermark=False)
    try:
        barrier.wait(30)
        _traced_openai_create(original, tracer, guard, model="gpt-4o-mini")
    except BudgetExceeded:
        queue.put("blocked")
    except Exception as exc:
        queue.put(f"error:{type(exc).__name__}:{exc}")
    else:
        queue.put("dispatched")


def main() -> dict:
    ctx = multiprocessing.get_context("spawn")
    with tempfile.TemporaryDirectory() as directory:
        store_path = str(Path(directory) / "budget.json")
        log_path = str(Path(directory) / "dispatched.txt")
        Path(log_path).write_text("", encoding="utf-8")
        barrier = ctx.Barrier(2)
        queue: multiprocessing.Queue = ctx.Queue()
        procs = [
            ctx.Process(target=_worker, args=(store_path, log_path, barrier, queue))
            for _ in range(2)
        ]
        for proc in procs:
            proc.start()
        for proc in procs:
            proc.join(60)
        exit_codes = [proc.exitcode for proc in procs]
        results = []
        while not queue.empty():
            results.append(queue.get())
        from agentguard import BudgetGuard, JsonFileStateStore

        totals = BudgetGuard(
            max_calls=1, store=JsonFileStateStore(store_path), key="fleet"
        ).reservation_totals()
        dispatched = Path(log_path).read_text(encoding="utf-8").count("1")
        payload = {
            "dispatched": dispatched,
            "results": results,
            "blocked": results.count("blocked"),
            "settled_calls": totals["settled"]["calls"],
            "reserved_calls": totals["reserved"]["calls"],
            "unresolved_calls": totals["unresolved"]["calls"],
            "workers": 2,
            "start_method": "spawn",
            "exit_codes": exit_codes,
            "network_calls": 0,
            "path": "openai-sync-non-stream-statestore",
            "fixed": dispatched == 1 and results.count("blocked") == 1 and totals["settled"]["calls"] == 1,
        }
    if not payload["fixed"] or any(code != 0 for code in exit_codes):
        raise SystemExit(json.dumps(payload))
    return payload


if __name__ == "__main__":
    print(json.dumps(main()))
