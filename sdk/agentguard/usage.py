"""Shared provider inference and token-usage normalization helpers."""
from __future__ import annotations

from typing import Any, Dict, Optional


def infer_provider(model: str) -> Optional[str]:
    """Infer a provider from a model name when explicit provider data is missing."""
    lowered = model.lower()
    if lowered.startswith(("gpt-", "o1", "o3", "o4")):
        return "openai"
    if lowered.startswith("claude"):
        return "anthropic"
    if lowered.startswith("gemini"):
        return "google"
    if lowered.startswith("mistral"):
        return "mistral"
    if lowered.startswith("llama"):
        return "meta"
    return None


def normalize_usage(usage: Any, provider: Optional[str] = None) -> Optional[Dict[str, int]]:
    """Normalize provider-specific usage payloads into a stable SDK shape."""
    if usage is None:
        return None

    prompt_tokens = _as_int(_nested_get(usage, "prompt_tokens"))
    completion_tokens = _as_int(_nested_get(usage, "completion_tokens"))
    total_tokens = _as_int(_nested_get(usage, "total_tokens"))
    input_tokens = _as_int(_nested_get(usage, "input_tokens"))
    output_tokens = _as_int(_nested_get(usage, "output_tokens"))
    cached_tokens = _as_int(_nested_get(usage, "prompt_tokens_details", "cached_tokens"))
    reasoning_tokens = _as_int(
        _nested_get(usage, "completion_tokens_details", "reasoning_tokens")
    )
    cache_read_input_tokens = _as_int(_nested_get(usage, "cache_read_input_tokens"))
    cache_creation_input_tokens = _as_int(_nested_get(usage, "cache_creation_input_tokens"))

    looks_openai = bool(
        prompt_tokens
        or completion_tokens
        or cached_tokens
        or reasoning_tokens
    )
    looks_anthropic = bool(
        input_tokens
        or output_tokens
        or cache_read_input_tokens
        or cache_creation_input_tokens
    )

    resolved_provider = provider
    if resolved_provider is None:
        if looks_openai:
            resolved_provider = "openai"
        elif looks_anthropic:
            resolved_provider = "anthropic"

    if resolved_provider == "openai":
        return _normalize_openai_usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
        )

    if resolved_provider == "anthropic":
        return _normalize_anthropic_usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cache_read_input_tokens,
            cache_creation_input_tokens=cache_creation_input_tokens,
        )

    if looks_openai:
        return _normalize_openai_usage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cached_tokens=cached_tokens,
            reasoning_tokens=reasoning_tokens,
        )

    if looks_anthropic:
        return _normalize_anthropic_usage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_read_input_tokens=cache_read_input_tokens,
            cache_creation_input_tokens=cache_creation_input_tokens,
        )

    if isinstance(usage, dict):
        generic_total = _as_int(usage.get("total_tokens"))
        generic_input = _as_int(usage.get("input_tokens"))
        generic_output = _as_int(usage.get("output_tokens"))
        if generic_total or generic_input or generic_output:
            normalized = {
                "input_tokens": generic_input,
                "output_tokens": generic_output,
                "total_tokens": generic_total or (generic_input + generic_output),
            }
            cached_input = _as_int(usage.get("cached_input_tokens"))
            cache_write = _as_int(usage.get("cache_write_input_tokens"))
            reasoning = _as_int(usage.get("reasoning_tokens"))
            if cached_input:
                normalized["cached_input_tokens"] = cached_input
            if cache_write:
                normalized["cache_write_input_tokens"] = cache_write
            if reasoning:
                normalized["reasoning_tokens"] = reasoning
            return normalized
    return None


def _nested_get(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            current = getattr(current, key, None)
        if current is None:
            return None
    return current


def _as_int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def _normalize_openai_usage(
    *,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cached_tokens: int,
    reasoning_tokens: int,
) -> Dict[str, int]:
    normalized: Dict[str, int] = {
        "input_tokens": prompt_tokens,
        "output_tokens": completion_tokens,
        "total_tokens": total_tokens or (prompt_tokens + completion_tokens),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
    if cached_tokens:
        normalized["cached_input_tokens"] = cached_tokens
    if reasoning_tokens:
        normalized["reasoning_tokens"] = reasoning_tokens
    return normalized


def _normalize_anthropic_usage(
    *,
    input_tokens: int,
    output_tokens: int,
    cache_read_input_tokens: int,
    cache_creation_input_tokens: int,
) -> Dict[str, int]:
    normalized = {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": (
            input_tokens + output_tokens + cache_read_input_tokens + cache_creation_input_tokens
        ),
    }
    if cache_read_input_tokens:
        normalized["cached_input_tokens"] = cache_read_input_tokens
        normalized["cache_read_input_tokens"] = cache_read_input_tokens
    if cache_creation_input_tokens:
        normalized["cache_write_input_tokens"] = cache_creation_input_tokens
        normalized["cache_creation_input_tokens"] = cache_creation_input_tokens
    return normalized
