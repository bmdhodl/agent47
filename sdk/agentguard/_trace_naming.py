"""Internal trace naming helpers shared by sync and async tracers."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger("agentguard.tracing")

MAX_NAME_LENGTH = 1000


def truncate_name(name: str) -> str:
    """Truncate a trace/service/event name to the supported size limit."""
    if len(name) <= MAX_NAME_LENGTH:
        return name
    logger.warning(
        "Name truncated from %d to %d chars: %s...",
        len(name), MAX_NAME_LENGTH, name[:50],
    )
    return name[:MAX_NAME_LENGTH]


def normalize_session_id(session_id: Optional[str]) -> Optional[str]:
    """Normalize runtime session correlation identifiers."""
    if session_id is None:
        return None
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("session_id must be a non-empty string")
    return truncate_name(session_id.strip())
