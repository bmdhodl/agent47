from __future__ import annotations

import atexit
import json
import logging
import threading
import urllib.request
from typing import Any, Dict, List, Optional

from agentguard.tracing import TraceSink

logger = logging.getLogger("agentguard.sinks.http")


class HttpSink(TraceSink):
    """Batched HTTP sink that POSTs JSONL trace events to a remote endpoint.

    Uses only stdlib (urllib.request). Events are buffered and flushed
    periodically in a background thread. Network failures are logged
    but never crash the calling agent.
    """

    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        batch_size: int = 10,
        flush_interval: float = 5.0,
    ) -> None:
        if api_key and url.startswith("http://"):
            logger.warning(
                "HttpSink: sending API key over plain HTTP (%s). "
                "Use HTTPS to protect credentials in transit.",
                url,
            )
        self._url = url
        self._api_key = api_key
        self._batch_size = batch_size
        self._flush_interval = flush_interval

        self._buffer: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        atexit.register(self.shutdown)

    def emit(self, event: Dict[str, Any]) -> None:
        batch = None
        with self._lock:
            self._buffer.append(event)
            if len(self._buffer) >= self._batch_size:
                batch = self._buffer[:]
                self._buffer.clear()
        if batch:
            self._send(batch)

    def _run(self) -> None:
        while not self._stop.wait(self._flush_interval):
            self._flush()

    def _flush(self) -> None:
        with self._lock:
            if not self._buffer:
                return
            batch = self._buffer[:]
            self._buffer.clear()
        self._send(batch)

    def _send(self, batch: List[Dict[str, Any]]) -> None:
        if not batch:
            return
        body = "\n".join(json.dumps(e, sort_keys=True) for e in batch).encode("utf-8")
        headers: Dict[str, str] = {"Content-Type": "application/x-ndjson"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        req = urllib.request.Request(self._url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                resp.read()
        except Exception:
            logger.warning("Failed to send trace batch to %s", self._url, exc_info=True)

    def shutdown(self) -> None:
        """Flush remaining events and stop the background thread."""
        self._stop.set()
        self._flush()
        self._thread.join(timeout=5)
