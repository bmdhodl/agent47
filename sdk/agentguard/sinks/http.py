"""HTTP sink for sending trace events to a remote endpoint.

Usage::

    from agentguard import Tracer, HttpSink

    sink = HttpSink(url="https://app.agentguard47.com/api/ingest", api_key="ag_...")
    tracer = Tracer(sink=sink, service="my-agent")
"""
from __future__ import annotations

import atexit
import gzip
import json
import logging
import threading
import time
import urllib.request
import uuid
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError

from agentguard.tracing import TraceSink

logger = logging.getLogger("agentguard.sinks.http")


class HttpSink(TraceSink):
    """Batched HTTP sink that POSTs JSONL trace events to a remote endpoint.

    Uses only stdlib (urllib.request). Events are buffered and flushed
    periodically in a background thread. Network failures are logged
    but never crash the calling agent.

    Features:
    - Gzip compression (stdlib gzip)
    - Retry with exponential backoff (3 attempts, 1s/2s/4s)
    - UUID idempotency keys per batch
    - Respects 429 + Retry-After header

    Usage::

        sink = HttpSink(
            url="https://app.agentguard47.com/api/ingest",
            api_key="ag_...",
            batch_size=10,
            flush_interval=5.0,
        )
        tracer = Tracer(sink=sink, service="my-agent")

    Args:
        url: Endpoint URL to POST events to.
        api_key: Optional API key sent as Bearer token.
        batch_size: Flush when this many events are buffered.
        flush_interval: Flush every N seconds regardless of buffer size.
        compress: Enable gzip compression. Default True.
        max_retries: Maximum retry attempts on failure. Default 3.
    """

    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        compress: bool = True,
        max_retries: int = 3,
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
        self._compress = compress
        self._max_retries = max_retries

        self._buffer: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        atexit.register(self.shutdown)

    def emit(self, event: Dict[str, Any]) -> None:
        """Buffer an event, flushing if batch_size is reached."""
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
        body_str = "\n".join(json.dumps(e, sort_keys=True) for e in batch)
        body = body_str.encode("utf-8")

        headers: Dict[str, str] = {"Content-Type": "application/x-ndjson"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        # Idempotency key
        idempotency_key = uuid.uuid4().hex
        headers["Idempotency-Key"] = idempotency_key

        # Gzip compression
        if self._compress:
            body = gzip.compress(body)
            headers["Content-Encoding"] = "gzip"

        # Retry with exponential backoff
        for attempt in range(self._max_retries):
            try:
                req = urllib.request.Request(
                    self._url, data=body, headers=headers, method="POST"
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp.read()
                return  # success
            except HTTPError as e:
                if e.code == 429:
                    # Respect Retry-After header
                    retry_after = e.headers.get("Retry-After")
                    wait = float(retry_after) if retry_after else (2 ** attempt)
                    logger.warning(
                        "Rate limited (429) by %s, retrying in %.1fs",
                        self._url, wait,
                    )
                    time.sleep(wait)
                    continue
                if e.code >= 500:
                    # Server error — retry
                    wait = 2 ** attempt
                    logger.warning(
                        "Server error (%d) from %s, retrying in %.1fs",
                        e.code, self._url, wait,
                    )
                    time.sleep(wait)
                    continue
                # Client error (4xx except 429) — don't retry
                logger.warning(
                    "Client error (%d) sending to %s, not retrying",
                    e.code, self._url,
                )
                return
            except Exception:
                if attempt < self._max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "Failed to send trace batch to %s (attempt %d/%d), "
                        "retrying in %.1fs",
                        self._url, attempt + 1, self._max_retries, wait,
                        exc_info=True,
                    )
                    time.sleep(wait)
                else:
                    logger.warning(
                        "Failed to send trace batch to %s after %d attempts",
                        self._url, self._max_retries,
                        exc_info=True,
                    )

    def shutdown(self) -> None:
        """Flush remaining events and stop the background thread."""
        self._stop.set()
        self._flush()
        self._thread.join(timeout=5)

    def __repr__(self) -> str:
        return f"HttpSink(url={self._url!r})"
