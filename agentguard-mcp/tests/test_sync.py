from __future__ import annotations

import time

from agentguard_mcp.sync import SyncHook


def test_sync_hook_is_fire_and_forget(monkeypatch):
    calls: list[dict] = []

    def slow_post(event: dict) -> None:
        time.sleep(0.2)
        calls.append(event)

    hook = SyncHook(url="https://example.invalid/sync")
    monkeypatch.setattr(hook, "_post", slow_post)

    start = time.perf_counter()
    hook.record({"server": "github"})
    elapsed = time.perf_counter() - start

    assert elapsed < 0.05
    for _ in range(20):
        if calls:
            break
        time.sleep(0.02)
    assert calls == [{"server": "github"}]
