"""Optional usage-event sync hook for hosted control-plane integrations."""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Any


class SyncHook:
    """POST usage events when AGENTGUARD_SYNC_URL is configured."""

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        timeout_seconds: float = 2.0,
    ) -> None:
        self.url = url if url is not None else os.environ.get("AGENTGUARD_SYNC_URL")
        self.token = token if token is not None else os.environ.get("AGENTGUARD_SYNC_TOKEN")
        self.timeout_seconds = timeout_seconds

    def record(self, event: Mapping[str, Any]) -> None:
        if not self.url:
            return
        thread = threading.Thread(target=self._post, args=(dict(event),), daemon=True)
        thread.start()

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
