"""Runtime-only billing declarations for exact OpenAI client instances."""
from __future__ import annotations

import weakref
from typing import Any, Iterable, Optional, Tuple


def client_entries(clients: Iterable[Any]) -> Tuple[Any, ...]:
    """Materialize the caller's iterable once, with a clear boundary error."""
    try:
        entries = tuple(clients)
    except TypeError as exc:
        raise TypeError("free_local_clients must be an iterable of OpenAI clients") from exc
    return entries


def validate_free_local_clients(
    clients: Iterable[Any], sdk: Any, *, asynchronous: Optional[bool] = None
) -> Tuple[Any, ...]:
    """Validate the entire iterable before any patch or setup side effect."""
    entries = client_entries(clients)
    names = ("AsyncOpenAI",) if asynchronous else ("OpenAI",)
    if asynchronous is None:
        names = ("OpenAI", "AsyncOpenAI")
    classes = tuple(c for n in names if isinstance(c := getattr(sdk, n, None), type))
    for client in entries:
        if not classes or not isinstance(client, classes):
            raise TypeError("free_local_clients entries must be " + " or ".join(names) + " instances")
        try:
            weakref.ref(client)
        except TypeError as exc:
            raise TypeError("free_local_clients entries must support weak references") from exc
        chat = getattr(getattr(client, "chat", None), "completions", None)
        responses = getattr(client, "responses", None)
        if chat is None or any(
            getattr(resource, "_client", None) is not client
            for resource in (chat, responses) if resource is not None
        ):
            raise TypeError("free_local_clients requires standard SDK resource owner references")
    return entries


class FreeLocalClients:
    """Immutable weak references, compared by identity rather than user equality."""

    def __init__(self, clients: Iterable[Any]) -> None:
        self._clients = tuple(weakref.ref(client) for client in clients)

    def billing(self, original: Any, args: tuple) -> Tuple[str, bool]:
        """Read the real resource owner's identity for this dispatch."""
        resource = args[0] if args else getattr(original, "__self__", None)
        client = getattr(resource, "_client", None)
        if client is not None and any(ref() is client for ref in self._clients):
            return "local", True
        return "openai", False


def split_free_local_clients(clients: Iterable[Any]) -> Tuple[tuple, tuple]:
    """Partition one validated setup iterable without retaining it in global state."""
    entries = client_entries(clients)
    if not entries:
        return (), ()
    import openai

    entries = validate_free_local_clients(entries, openai)
    return (tuple(c for c in entries if isinstance(c, openai.OpenAI)),
            tuple(c for c in entries if isinstance(c, openai.AsyncOpenAI)))
