"""Optional usage-event sync hook for hosted control-plane integrations."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore
from typing import Any


class SyncHook:
    """POST usage events when AGENTGUARD_SYNC_URL is configured."""

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        timeout_seconds: float = 2.0,
        max_workers: int = 1,
        max_pending: int = 64,
    ) -> None:
        self.url = url if url is not None else os.environ.get("AGENTGUARD_SYNC_URL")
        self.token = token if token is not None else os.environ.get("AGENTGUARD_SYNC_TOKEN")
        self.timeout_seconds = timeout_seconds
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="agentguard-sync")
        self._pending = BoundedSemaphore(max_pending)

    def record(self, event: Mapping[str, Any]) -> None:
        if not self.url:
            return
        if not self._pending.acquire(blocking=False):
            return
        self._executor.submit(self._post_and_release, dict(event))

    def _post_and_release(self, event: dict[str, Any]) -> None:
        try:
            self._post(event)
        finally:
            self._pending.release()

    def _post(self, event: dict[str, Any]) -> None:
        if not self.url:
            return
        body = json.dumps(event, separators=(",", ":")).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(self.url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds):
                return
        except (OSError, urllib.error.URLError, TimeoutError):
            return
