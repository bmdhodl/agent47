"""Record and replay agent interactions for deterministic testing.

Usage::

    from agentguard import Recorder, Replayer

    recorder = Recorder("runs.jsonl")
    recorder.record_call("llm", {"prompt": "hi"}, {"text": "hello"})

    replayer = Replayer("runs.jsonl")
    resp = replayer.replay_call("llm", {"prompt": "hi"})
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


class Recorder:
    """Record agent call/response pairs to a JSONL file.

    Usage::

        recorder = Recorder("runs.jsonl")
        recorder.record_call("llm", {"prompt": "hi"}, {"text": "hello"})

    Args:
        path: Path to the output JSONL file.
    """

    def __init__(self, path: str) -> None:
        self._path = path

    def record_call(
        self,
        name: str,
        request: Dict[str, Any],
        response: Dict[str, Any],
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a single call/response pair.

        Args:
            name: Identifier for this call type (e.g. "llm", "search").
            request: The request data.
            response: The response data.
            meta: Optional metadata.
        """
        event = {
            "ts": time.time(),
            "name": name,
            "request": request,
            "response": response,
            "meta": meta or {},
        }
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")

    def __repr__(self) -> str:
        return f"Recorder({self._path!r})"


@dataclass
class ReplayEntry:
    name: str
    request_key: str
    response: Dict[str, Any]


class Replayer:
    """Replay recorded call/response pairs for deterministic testing.

    Usage::

        replayer = Replayer("runs.jsonl")
        resp = replayer.replay_call("llm", {"prompt": "hi"})

    Args:
        path: Path to the recorded JSONL file.
    """

    def __init__(self, path: str) -> None:
        self._path = path
        self._entries = _load_entries(path)

    def replay_call(self, name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Look up a recorded response for the given call.

        Args:
            name: Call identifier used during recording.
            request: The request data (must match exactly).

        Returns:
            The recorded response dict.

        Raises:
            KeyError: If no matching recording is found.
        """
        key = (name, _stable_json(request))
        if key not in self._entries:
            raise KeyError(f"No replay entry for {name}")
        return self._entries[key]

    def __repr__(self) -> str:
        return f"Replayer({self._path!r})"


def _load_entries(path: str) -> Dict[Tuple[str, str], Dict[str, Any]]:
    entries: Dict[Tuple[str, str], Dict[str, Any]] = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                name = data.get("name")
                request = data.get("request")
                response = data.get("response")
                if not name or request is None or response is None:
                    continue
                entries[(name, _stable_json(request))] = response
    except FileNotFoundError:
        return {}
    return entries


def _stable_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"))
