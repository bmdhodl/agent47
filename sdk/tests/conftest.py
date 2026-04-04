"""Shared pytest fixtures: local ingest server mirroring the hosted ingest API."""
from __future__ import annotations

import gzip
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

import pytest

# Force pytest to import the SDK from this checkout, not a different editable install.
SDK_ROOT = Path(__file__).resolve().parents[1]
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))

EXPECTED_API_KEY = "ag_test_key_e2e"

REQUIRED_STRING_FIELDS = {"service", "phase", "trace_id", "span_id", "name"}
VALID_KINDS = {"span", "event"}
VALID_PHASES = {"start", "end", "emit"}
INVALID_KIND_ERROR = 'Invalid option: expected one of "span"|"event"'


class IngestHandler(BaseHTTPRequestHandler):
    """Local ingest server that validates events like the hosted API."""

    events: ClassVar[List[Dict[str, Any]]] = []
    idempotency_keys: ClassVar[List[str]] = []
    requests: ClassVar[List[Dict[str, Any]]] = []
    _lock = threading.Lock()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/ingest":
            self._handle_ingest()
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/events":
            self._handle_query()
        elif path == "/api/v1/traces":
            self._handle_traces()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_ingest(self) -> None:
        # Auth check
        auth = self.headers.get("Authorization", "")
        if auth != f"Bearer {EXPECTED_API_KEY}":
            self.send_response(401)
            self.end_headers()
            self.wfile.write(json.dumps({"error": "unauthorized"}).encode())
            return

        # Read body
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        # Decompress if gzip
        if self.headers.get("Content-Encoding") == "gzip":
            body = gzip.decompress(body)

        # Record idempotency key
        idem_key = self.headers.get("Idempotency-Key", "")

        # Parse NDJSON
        accepted = 0
        rejected = 0
        details: List[Dict[str, Any]] = []

        for line_number, line in enumerate(body.decode("utf-8").split("\n")):
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                rejected += 1
                details.append({"line": line_number, "error": "invalid JSON"})
                continue

            # Validate required fields
            validation_error = _validate_event(event)
            if validation_error:
                rejected += 1
                details.append({"line": line_number, "error": validation_error})
                continue

            with self.__class__._lock:
                self.__class__.events.append(event)
            accepted += 1

        status = 200
        payload: Dict[str, Any] = {
            "accepted": accepted,
            "rejected": rejected,
            "details": details,
        }
        if accepted == 0 and rejected > 0:
            status = 400
            payload = {"error": "No valid events", "details": details}

        if idem_key:
            with self.__class__._lock:
                self.__class__.idempotency_keys.append(idem_key)
        with self.__class__._lock:
            self.__class__.requests.append(
                {
                    "status": status,
                    "accepted": accepted,
                    "rejected": rejected,
                    "details": list(details),
                    "idempotency_key": idem_key,
                }
            )

        resp = json.dumps(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(resp.encode())

    def _handle_query(self) -> None:
        qs = parse_qs(urlparse(self.path).query)

        with self.__class__._lock:
            result = list(self.__class__.events)

        # Apply filters
        if "trace_id" in qs:
            tid = qs["trace_id"][0]
            result = [e for e in result if e.get("trace_id") == tid]
        if "name" in qs:
            name = qs["name"][0]
            result = [e for e in result if e.get("name") == name]
        if "kind" in qs:
            kind = qs["kind"][0]
            result = [e for e in result if e.get("kind") == kind]

        resp = json.dumps(result)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(resp.encode())

    def _handle_traces(self) -> None:
        """Aggregate stored events by trace_id, return trace summaries."""
        qs = parse_qs(urlparse(self.path).query)

        with self.__class__._lock:
            all_events = list(self.__class__.events)

        # Group by trace_id
        traces: Dict[str, List[Dict[str, Any]]] = {}
        for e in all_events:
            tid = e.get("trace_id", "unknown")
            traces.setdefault(tid, []).append(e)

        # Optional filter
        if "trace_id" in qs:
            tid = qs["trace_id"][0]
            traces = {tid: traces[tid]} if tid in traces else {}

        result = []
        for tid, events in traces.items():
            total_cost = 0.0
            for e in events:
                cost = e.get("cost_usd")
                if cost is None and isinstance(e.get("data"), dict):
                    cost = e["data"].get("cost_usd")
                if isinstance(cost, (int, float)):
                    total_cost += cost
            result.append({
                "trace_id": tid,
                "event_count": len(events),
                "total_cost": total_cost,
            })

        resp = json.dumps({"traces": result})
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(resp.encode())

    def log_message(self, *args) -> None:
        pass  # suppress request logging

    # ---- Class-level helpers for test assertions ----

    @classmethod
    def reset(cls) -> None:
        with cls._lock:
            cls.events.clear()
            cls.idempotency_keys.clear()
            cls.requests.clear()

    @classmethod
    def event_count(cls) -> int:
        with cls._lock:
            return len(cls.events)

    @classmethod
    def events_with_cost(cls) -> List[Dict[str, Any]]:
        with cls._lock:
            return [
                e for e in cls.events
                if e.get("cost_usd") is not None
                or (isinstance(e.get("data"), dict) and e["data"].get("cost_usd") is not None)
            ]

    @classmethod
    def events_with_metadata(cls) -> List[Dict[str, Any]]:
        with cls._lock:
            return [e for e in cls.events if "metadata" in e]

    @classmethod
    def request_log(cls) -> List[Dict[str, Any]]:
        with cls._lock:
            return [dict(request) for request in cls.requests]

    @classmethod
    def failed_requests(cls) -> List[Dict[str, Any]]:
        with cls._lock:
            return [
                dict(request)
                for request in cls.requests
                if request.get("status", 200) >= 400 or request.get("rejected", 0) > 0
            ]


def _validate_event(event: Dict[str, Any]) -> Optional[str]:
    """Validate event schema. Returns error string or None."""
    kind = event.get("kind")
    event_type = event.get("type")
    if not isinstance(kind, str) or kind not in VALID_KINDS:
        return INVALID_KIND_ERROR
    if not isinstance(event_type, str) or event_type not in VALID_KINDS:
        return INVALID_KIND_ERROR
    if kind != event_type:
        return f"kind/type mismatch: {kind}/{event_type}"

    for field in REQUIRED_STRING_FIELDS:
        if field not in event or not isinstance(event[field], str):
            return f"missing or invalid field: {field}"

    if event.get("phase") not in VALID_PHASES:
        return f"invalid phase: {event.get('phase')}"

    if "ts" not in event or not isinstance(event["ts"], (int, float)):
        return "missing or invalid ts"

    return None


# ---- Pytest fixtures ----

@pytest.fixture(scope="session")
def ingest_server():
    """Start local ingest server once per test session."""
    IngestHandler.reset()
    server = HTTPServer(("127.0.0.1", 0), IngestHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield ("127.0.0.1", port)
    server.shutdown()


@pytest.fixture
def ingest_url(ingest_server):
    """Return ingest URL and reset stored events between tests."""
    host, port = ingest_server
    IngestHandler.reset()
    return f"http://{host}:{port}/api/ingest"
