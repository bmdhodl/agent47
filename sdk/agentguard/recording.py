from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import json
import time


class Recorder:
    def __init__(self, path: str) -> None:
        self._path = path

    def record_call(
        self,
        name: str,
        request: Dict[str, Any],
        response: Dict[str, Any],
        meta: Optional[Dict[str, Any]] = None,
    ) -> None:
        event = {
            "ts": time.time(),
            "name": name,
            "request": request,
            "response": response,
            "meta": meta or {},
        }
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, sort_keys=True) + "\n")


@dataclass
class ReplayEntry:
    name: str
    request_key: str
    response: Dict[str, Any]


class Replayer:
    def __init__(self, path: str) -> None:
        self._entries = _load_entries(path)

    def replay_call(self, name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        key = (name, _stable_json(request))
        if key not in self._entries:
            raise KeyError(f"No replay entry for {name}")
        return self._entries[key]


def _load_entries(path: str) -> Dict[Tuple[str, str], Dict[str, Any]]:
    entries: Dict[Tuple[str, str], Dict[str, Any]] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
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
