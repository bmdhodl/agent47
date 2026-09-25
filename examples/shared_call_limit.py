"""Two workers, one shared local call, one simulated provider send.

Install the published package, then run this file. It does not read the
repository checkout. Each run uses a new temporary store, so a previous run
cannot make this one fail.

POSIX:
    python examples/shared_call_limit.py

PowerShell:
    python examples/shared_call_limit.py

The provider is simulated. No API key, billable request, or network call.
This is one shared local key, not a provider invoice cap and not a
cross-machine budget. Spawn is the start method. This environment records
Linux results and does not execute Windows.
"""
from __future__ import annotations

import json
import multiprocessing
import queue as queue_module
import sys
import tempfile
import types
from pathlib import Path


def _install_simulated_openai(log_path: str) -> None:
    """Register a local OpenAI stand-in so patch_openai has a client to wrap."""
    module = types.ModuleType("openai")

    class Completions:
        def create(self, **_kwargs: object) -> types.SimpleNamespace:
            with open(log_path, "a", encoding="utf-8") as handle:
                handle.write("1\n")
            usage = types.SimpleNamespace(prompt_tokens=1, completion_tokens=1, total_tokens=2)
            return types.SimpleNamespace(usage=usage)

    class Chat:
        def __init__(self) -> None:
            self.completions = Completions()

    class OpenAI:
        def __init__(self, **_kwargs: object) -> None:
            self.chat = Chat()

    module.OpenAI = OpenAI
    sys.modules["openai"] = module


def _worker(store_path: str, log_path: str, barrier: multiprocessing.Barrier, queue: multiprocessing.Queue) -> None:
    _install_simulated_openai(log_path)
    from agentguard import BudgetExceeded, BudgetGuard, JsonFileStateStore, Tracer, patch_openai
    import openai

    class _Drop:
        def emit(self, _event: object) -> None:
            return None

    guard = BudgetGuard(max_calls=1, store=JsonFileStateStore(store_path), key="fleet")
    tracer = Tracer(sink=_Drop(), service="shared-call-limit", watermark=False)
    patch_openai(tracer, budget_guard=guard)
    client = openai.OpenAI(api_key="simulated")
    try:
        barrier.wait(30)
        client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "ping"}],
        )
    except BudgetExceeded:
        queue.put("stopped")
    except Exception as exc:
        queue.put(f"error:{type(exc).__name__}:{exc}")
    else:
        queue.put("sent")


def main() -> dict:
    ctx = multiprocessing.get_context("spawn")
    with tempfile.TemporaryDirectory() as directory:
        store_path = str(Path(directory) / "budget.json")
        log_path = str(Path(directory) / "sent.txt")
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
        for _ in procs:
            try:
                results.append(queue.get(timeout=10))
            except queue_module.Empty:
                results.append("missing")
        from agentguard import BudgetGuard, JsonFileStateStore

        totals = BudgetGuard(
            max_calls=1, store=JsonFileStateStore(store_path), key="fleet"
        ).reservation_totals()
        dispatched = Path(log_path).read_text(encoding="utf-8").count("1")
        payload = {
            "dispatched": dispatched,
            "results": results,
            "stopped": results.count("stopped"),
            "settled_calls": totals["settled"]["calls"],
            "reserved_calls": totals["reserved"]["calls"],
            "unresolved_calls": totals["unresolved"]["calls"],
            "workers": 2,
            "start_method": "spawn",
            "exit_codes": exit_codes,
            "network_calls": 0,
            "provider": "simulated",
            "store": "fresh-temporary",
            "fixed": dispatched == 1 and results.count("stopped") == 1 and totals["settled"]["calls"] == 1,
        }
    print("Shared local limit: one simulated call was sent. The other worker was stopped before send.")
    print("Boundary: one shared local key. Not a provider invoice cap. Not a cross-machine budget.")
    print("Next: run this script again. It creates a fresh temporary store, so the last run does not block it.")
    print("RESULT " + json.dumps(payload))
    if not payload["fixed"] or any(code != 0 for code in exit_codes):
        raise SystemExit(1)
    return payload


if __name__ == "__main__":
    main()
