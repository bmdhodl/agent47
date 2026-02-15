"""HTTP sink for sending trace events to a remote endpoint.

Usage::

    from agentguard import Tracer, HttpSink

    sink = HttpSink(url="https://app.agentguard47.com/api/ingest", api_key="ag_...")
    tracer = Tracer(sink=sink, service="my-agent")
"""
from __future__ import annotations

import atexit
import gzip
import ipaddress
import json
import logging
import socket
import threading
import time
import urllib.request
import uuid
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError
from urllib.parse import urlparse

from agentguard.tracing import TraceSink

logger = logging.getLogger("agentguard.sinks.http")


# Private/reserved IP ranges that should never be used as sink endpoints
# Includes 169.254.169.254 (AWS/GCP/Azure metadata endpoint) via 169.254.0.0/16
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),      # loopback
    ipaddress.ip_network("10.0.0.0/8"),        # RFC 1918
    ipaddress.ip_network("172.16.0.0/12"),     # RFC 1918
    ipaddress.ip_network("192.168.0.0/16"),    # RFC 1918
    ipaddress.ip_network("169.254.0.0/16"),    # link-local + cloud metadata
    ipaddress.ip_network("0.0.0.0/8"),         # "this" network
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 unique local
    ipaddress.ip_network("fe80::/10"),         # IPv6 link-local
]


def _validate_url(url: str, allow_private: bool = False) -> None:
    """Validate a URL is safe for use as a sink endpoint.

    Args:
        url: URL to validate.
        allow_private: If True, skip private IP checks (for testing).

    Raises:
        ValueError: If the URL is invalid or points to a private/reserved IP.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"URL scheme must be http or https, got {parsed.scheme!r}"
        )
    if not parsed.hostname:
        raise ValueError("URL must include a hostname")

    if allow_private:
        return

    # IDN/Punycode normalization: reject non-ASCII hostnames that could bypass
    # string-based checks (e.g. Unicode lookalikes like "localhost")
    hostname = parsed.hostname
    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError) as err:
        raise ValueError(
            f"URL hostname {hostname!r} contains invalid characters "
            f"(failed IDNA encoding)"
        ) from err
    if ascii_hostname.lower() != hostname.lower():
        raise ValueError(
            f"URL hostname {hostname!r} contains non-ASCII characters "
            f"(IDNA-encoded: {ascii_hostname!r}). Use the ASCII form."
        )

    # Resolve hostname and check against blocked networks
    try:
        addr = ipaddress.ip_address(hostname)
    except ValueError:
        # It's a hostname, not an IP — resolve it
        try:
            resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC)
            addrs = {ipaddress.ip_address(r[4][0]) for r in resolved}
        except (socket.gaierror, OSError):
            # Can't resolve — allow it (may be valid later)
            return
        for addr in addrs:
            for network in _BLOCKED_NETWORKS:
                if addr in network:
                    raise ValueError(
                        f"URL resolves to private/reserved IP {addr} "
                        f"({network}). Use a public endpoint."
                    ) from None
        return

    # Direct IP address in URL
    for network in _BLOCKED_NETWORKS:
        if addr in network:
            raise ValueError(
                f"URL points to private/reserved IP {addr} "
                f"({network}). Use a public endpoint."
            )


def _validate_api_key(api_key: str) -> None:
    """Validate an API key does not contain header injection characters.

    Args:
        api_key: The API key to validate.

    Raises:
        ValueError: If the key contains newline or carriage return characters.
    """
    if "\n" in api_key or "\r" in api_key:
        raise ValueError(
            "API key must not contain newline or carriage return characters "
            "(possible HTTP header injection)"
        )


class _SsrfSafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler that re-validates redirect targets against SSRF checks.

    Prevents redirect-based SSRF where an attacker controls a public URL
    that redirects to an internal endpoint (e.g., cloud metadata at
    169.254.169.254).
    """

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> Optional[urllib.request.Request]:
        _validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


# Build an opener that uses our SSRF-safe redirect handler
_opener = urllib.request.build_opener(_SsrfSafeRedirectHandler)


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
    - SSRF protection on redirects

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
        max_buffer_size: Maximum events to buffer before dropping oldest. Default 10000.
    """

    def __init__(
        self,
        url: str,
        api_key: Optional[str] = None,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        compress: bool = True,
        max_retries: int = 3,
        max_buffer_size: int = 10_000,
        _allow_private: bool = False,
    ) -> None:
        _validate_url(url, allow_private=_allow_private)
        if api_key:
            _validate_api_key(api_key)
        if api_key and url.startswith("http://"):
            logger.warning(
                "HttpSink: sending API key over plain HTTP (%s). "
                "Use HTTPS to protect credentials in transit.",
                url,
            )
        # Reject URLs with credentials in query string
        if "?" in url:
            query = url.split("?", 1)[1]
            for param in ("key=", "api_key=", "token=", "secret=", "password="):
                if param in query.lower():
                    raise ValueError(
                        f"HttpSink: URL contains credentials in query string ({param}...). "
                        f"Use the api_key parameter instead."
                    )
        self._url = url
        self._api_key = api_key
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._compress = compress
        self._max_retries = max_retries
        self._max_buffer_size = max_buffer_size
        self._dropped_count = 0

        self._buffer: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._stop = threading.Event()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        atexit.register(self.shutdown)

    def emit(self, event: Dict[str, Any]) -> None:
        batch = None
        with self._lock:
            if len(self._buffer) >= self._max_buffer_size:
                # Drop oldest events to prevent OOM
                drop = len(self._buffer) - self._max_buffer_size + 1
                self._buffer = self._buffer[drop:]
                self._dropped_count += drop
                logger.warning(
                    "HttpSink buffer full (%d max), dropped %d oldest event(s). "
                    "Total dropped: %d",
                    self._max_buffer_size, drop, self._dropped_count,
                )
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
                with _opener.open(req, timeout=10) as resp:
                    resp.read()
                return  # success
            except HTTPError as e:
                if e.code == 429:
                    # Respect Retry-After header (may be seconds or HTTP-date)
                    retry_after = e.headers.get("Retry-After")
                    wait = 2 ** attempt  # default fallback
                    if retry_after:
                        try:
                            wait = float(retry_after)
                        except ValueError:
                            pass  # HTTP-date or unparseable — use default backoff
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
