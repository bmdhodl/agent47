"""Local token-efficiency and savings helpers for trace files."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, Tuple

from agentguard.cost import estimate_cost
from agentguard.evaluation import _extract_cost, _load_events

_OPENAI_CACHED_INPUT_PRICES_PER_1K: Dict[str, float] = {
    "gpt-4o": 0.00125,
    "gpt-4o-mini": 0.000075,
}
_ANTHROPIC_CACHE_READ_MULTIPLIER = 0.1
_GUARD_REASON_ORDER = (
    ("guard.loop_detected", "loop_prevented"),
    ("guard.retry_limit_exceeded", "retry_storm_stopped"),
    ("guard.budget_exceeded", "budget_overrun_stopped"),
)


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

    if resolved_provider == "anthropic":
        normalized = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens + cache_read_input_tokens + cache_creation_input_tokens,
        }
        if cache_read_input_tokens:
            normalized["cached_input_tokens"] = cache_read_input_tokens
            normalized["cache_read_input_tokens"] = cache_read_input_tokens
        if cache_creation_input_tokens:
            normalized["cache_write_input_tokens"] = cache_creation_input_tokens
            normalized["cache_creation_input_tokens"] = cache_creation_input_tokens
        return normalized

    if looks_openai:
        normalized = {
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

    if looks_anthropic:
        normalized = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens + cache_read_input_tokens + cache_creation_input_tokens,
        }
        if cache_read_input_tokens:
            normalized["cached_input_tokens"] = cache_read_input_tokens
            normalized["cache_read_input_tokens"] = cache_read_input_tokens
        if cache_creation_input_tokens:
            normalized["cache_write_input_tokens"] = cache_creation_input_tokens
            normalized["cache_creation_input_tokens"] = cache_creation_input_tokens
        return normalized

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


def summarize_savings(path_or_events: Any) -> Dict[str, Any]:
    """Summarize exact and estimated savings from a JSONL trace or event list."""
    if isinstance(path_or_events, str):
        events = _load_events(path_or_events)
    elif isinstance(path_or_events, list):
        events = path_or_events
    else:
        raise TypeError(
            f"Expected str (file path) or list of events, got {type(path_or_events).__name__}"
        )

    reasons: DefaultDict[Tuple[str, str], Dict[str, Any]] = defaultdict(
        lambda: {"occurrences": 0, "tokens_saved": 0, "usd_saved": 0.0}
    )
    exact_tokens_saved = 0
    estimated_tokens_saved = 0
    exact_usd_saved = 0.0
    estimated_usd_saved = 0.0

    for event in events:
        usage = extract_normalized_usage(event)
        if usage is None:
            continue
        cached_tokens = usage.get("cached_input_tokens", 0)
        if cached_tokens <= 0:
            continue
        model = _extract_model(event)
        provider = _extract_provider(event)
        usd_saved = _estimate_cached_input_savings_usd(model, provider, cached_tokens)
        exact_tokens_saved += cached_tokens
        exact_usd_saved += usd_saved
        bucket = reasons[("provider_prompt_cache_hit", "exact")]
        bucket["occurrences"] += 1
        bucket["tokens_saved"] += cached_tokens
        bucket["usd_saved"] += usd_saved

    for trace_events in _group_events(events).values():
        reason_name, tokens_saved, usd_saved = _estimate_guard_trace_savings(trace_events)
        if reason_name is None:
            continue
        estimated_tokens_saved += tokens_saved
        estimated_usd_saved += usd_saved
        bucket = reasons[(reason_name, "estimated")]
        bucket["occurrences"] += 1
        bucket["tokens_saved"] += tokens_saved
        bucket["usd_saved"] += usd_saved

    return {
        "exact_tokens_saved": exact_tokens_saved,
        "estimated_tokens_saved": estimated_tokens_saved,
        "exact_usd_saved": round(exact_usd_saved, 4),
        "estimated_usd_saved": round(estimated_usd_saved, 4),
        "reasons": [
            {
                "kind": kind,
                "confidence": confidence,
                "occurrences": values["occurrences"],
                "tokens_saved": values["tokens_saved"],
                "usd_saved": round(values["usd_saved"], 4),
            }
            for (kind, confidence), values in sorted(reasons.items())
        ],
    }


def extract_normalized_usage(event: Dict[str, Any]) -> Optional[Dict[str, int]]:
    """Extract normalized usage from an event payload when present."""
    data = event.get("data", {})
    if not isinstance(data, dict):
        return None
    provider = _extract_provider(event)
    usage = data.get("usage") or data.get("token_usage")
    return normalize_usage(usage, provider=provider)


def _estimate_guard_trace_savings(events: List[Dict[str, Any]]) -> Tuple[Optional[str], int, float]:
    guard_reason = None
    guard_index = None
    for event_name, reason_name in _GUARD_REASON_ORDER:
        for idx, event in enumerate(events):
            if event.get("name") == event_name:
                guard_reason = reason_name
                guard_index = idx
                break
        if guard_reason is not None:
            break

    if guard_reason is None or guard_index is None:
        return None, 0, 0.0

    for idx in range(guard_index - 1, -1, -1):
        baseline_event = events[idx]
        usage = extract_normalized_usage(baseline_event)
        tokens_saved = usage.get("total_tokens", 0) if usage else 0
        usd_saved = _extract_cost(baseline_event)
        if usd_saved is None:
            usd_saved = _estimate_event_cost(baseline_event, usage)
        if tokens_saved <= 0 and (usd_saved is None or usd_saved <= 0):
            continue
        return guard_reason, tokens_saved, round(float(usd_saved or 0.0), 4)

    return None, 0, 0.0


def _estimate_event_cost(
    event: Dict[str, Any],
    usage: Optional[Dict[str, int]] = None,
) -> float:
    if usage is None:
        usage = extract_normalized_usage(event)
    if usage is None:
        return 0.0
    model = _extract_model(event)
    if not model:
        return 0.0
    provider = _extract_provider(event)
    return estimate_cost(
        model,
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        provider=provider,
    )


def _estimate_cached_input_savings_usd(
    model: str,
    provider: Optional[str],
    cached_tokens: int,
) -> float:
    if cached_tokens <= 0 or not model:
        return 0.0

    resolved_provider = provider or infer_provider(model)
    if resolved_provider is None:
        return 0.0

    base_input_cost = estimate_cost(
        model,
        input_tokens=cached_tokens,
        output_tokens=0,
        provider=resolved_provider,
    )
    if base_input_cost <= 0:
        return 0.0

    if resolved_provider == "openai":
        cached_input_price = _OPENAI_CACHED_INPUT_PRICES_PER_1K.get(model)
        if cached_input_price is None:
            return 0.0
        cached_cost = (cached_tokens * cached_input_price) / 1000.0
        return max(base_input_cost - cached_cost, 0.0)

    if resolved_provider == "anthropic":
        cached_cost = base_input_cost * _ANTHROPIC_CACHE_READ_MULTIPLIER
        return max(base_input_cost - cached_cost, 0.0)

    return 0.0


def _group_events(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    if any(isinstance(event.get("trace_id"), str) and event.get("trace_id") for event in events):
        for index, event in enumerate(events):
            trace_id = event.get("trace_id")
            grouped[str(trace_id or f"__orphan__:{index}")].append(event)
        return dict(grouped)
    return {"__global__": list(events)}


def _extract_model(event: Dict[str, Any]) -> str:
    data = event.get("data", {})
    if isinstance(data, dict):
        model = data.get("model")
        if isinstance(model, str):
            return model
    name = event.get("name", "")
    if isinstance(name, str) and name.startswith("llm.") and "." in name:
        return name.rsplit(".", 1)[-1]
    return ""


def _extract_provider(event: Dict[str, Any]) -> Optional[str]:
    data = event.get("data", {})
    if isinstance(data, dict):
        provider = data.get("provider")
        if isinstance(provider, str) and provider:
            return provider
    model = _extract_model(event)
    return infer_provider(model)


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
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return 0
