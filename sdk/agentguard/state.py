"""Persistent, cross-process state backends for AgentGuard guards.

In-memory guards lose their counters when the process exits. Agents that run as
repeated short-lived invocations (cron jobs, serverless functions, CI steps, Windows
scheduled tasks) cannot enforce a ceiling that way: every new process starts at zero.

A :class:`StateStore` lets a guard persist its accumulator so the ceiling holds across
separate processes. The default :class:`JsonFileStateStore` writes one JSON file,
guarded by a cross-process lock so concurrent processes do not lose updates.

Usage::

    from agentguard import BudgetGuard, JsonFileStateStore

    # Enforce 400 calls/day across many separate scheduled subprocess invocations:
    guard = BudgetGuard(
        max_calls=400,
        store=JsonFileStateStore("agent-budget.json"),
        key="fleet",
        period="day",
    )
    guard.consume(calls=1)
"""
from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Protocol, runtime_checkable

from .guards import AgentGuardError


class StateStoreError(AgentGuardError):
    """Raised when a StateStore cannot read or persist state.

    A corrupt or unreadable store raises this rather than silently resetting to zero -
    a guard that quietly forgets its budget is worse than no guard.
    """


@runtime_checkable
class StateStore(Protocol):
    """Pluggable persistent state backend for guards.

    Implementations must make :meth:`update` an atomic read-modify-write so two
    processes sharing the same store and key never lose an increment.
    """

    def read(self, key: str) -> Optional[Dict[str, Any]]:
        """Return the state dict stored at ``key``, or None if absent."""
        ...

    def update(
        self, key: str, mutator: Callable[[Optional[Dict[str, Any]]], Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Atomically load ``key``, apply ``mutator``, persist, and return the new state."""
        ...

    def clear(self, key: str) -> None:
        """Remove the state stored at ``key``."""
        ...


class _CrossProcessLock:
    """Portable advisory lock using an exclusive lock file.

    Acquired by creating a lock file with ``O_CREAT | O_EXCL``. A stale lock left by a
    crashed holder (older than ``stale_after`` seconds) is broken so the system cannot
    deadlock forever. Works on both POSIX and Windows.
    """

    def __init__(
        self,
        path: Path,
        *,
        timeout: float = 10.0,
        poll: float = 0.01,
        stale_after: float = 60.0,
    ) -> None:
        self._path = Path(path)
        self._timeout = timeout
        self._poll = poll
        self._stale_after = stale_after
        self._fd: Optional[int] = None

    def acquire(self) -> None:
        deadline = time.monotonic() + self._timeout
        while True:
            try:
                self._fd = os.open(str(self._path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self._fd, str(os.getpid()).encode("ascii"))
                return
            except FileExistsError:
                # Break a stale lock whose holder likely died. On Windows the held lock
                # file is open and unlink raises, so a live holder keeps the lock.
                try:
                    age = time.time() - self._path.stat().st_mtime
                    if age > self._stale_after:
                        os.unlink(self._path)
                        continue
                except OSError:
                    pass
                if time.monotonic() >= deadline:
                    raise StateStoreError(
                        f"timed out acquiring lock {self._path} after {self._timeout}s"
                    ) from None
                time.sleep(self._poll)

    def release(self) -> None:
        if self._fd is not None:
            try:
                os.close(self._fd)
            finally:
                self._fd = None
        try:
            os.unlink(self._path)
        except OSError:
            pass

    def __enter__(self) -> "_CrossProcessLock":
        self.acquire()
        return self

    def __exit__(self, *exc: Any) -> bool:
        self.release()
        return False


class JsonFileStateStore:
    """File-backed :class:`StateStore`.

    One JSON file holds a mapping of ``key -> state dict``. Writes are atomic (temp file
    + ``os.replace``) and serialized by a cross-process lock so concurrent processes do
    not lose updates. A corrupt store raises :class:`StateStoreError`.

    Args:
        path: Path to the JSON state file. Parent directories are created.
        lock_timeout: Seconds to wait for the cross-process lock before raising.
    """

    def __init__(self, path: Any, *, lock_timeout: float = 10.0) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self._path.with_name(self._path.name + ".lock")
        self._lock = _CrossProcessLock(lock_path, timeout=lock_timeout)

    def _read_all(self) -> Dict[str, Any]:
        if not self._path.exists():
            return {}
        try:
            raw = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StateStoreError(f"cannot read state file {self._path}: {exc}") from exc
        if not raw.strip():
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StateStoreError(
                f"state file {self._path} is corrupt: {exc}. Refusing to silently reset "
                f"to zero; fix or delete the file."
            ) from exc
        if not isinstance(data, dict):
            raise StateStoreError(
                f"state file {self._path} has unexpected shape: {type(data).__name__}"
            )
        return data

    def _write_all(self, data: Dict[str, Any]) -> None:
        fd, tmp = tempfile.mkstemp(
            dir=str(self._path.parent), prefix=self._path.name + ".", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(data, fh)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, self._path)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

    def read(self, key: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._read_all().get(key)

    def update(
        self, key: str, mutator: Callable[[Optional[Dict[str, Any]]], Dict[str, Any]]
    ) -> Dict[str, Any]:
        with self._lock:
            data = self._read_all()
            new_value = mutator(data.get(key))
            if not isinstance(new_value, dict):
                raise StateStoreError(
                    f"mutator must return a dict, got {type(new_value).__name__}"
                )
            data[key] = new_value
            self._write_all(data)
            return new_value

    def clear(self, key: str) -> None:
        with self._lock:
            data = self._read_all()
            if key in data:
                del data[key]
                self._write_all(data)

    def __repr__(self) -> str:
        return f"JsonFileStateStore({self._path!r})"
