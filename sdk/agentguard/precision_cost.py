"""Maximum-precision billable cost resolution for AgentGuard.

LIMITATION (read carefully):
    AgentGuard does NOT fetch live prices and does NOT read provider invoices.
    ``resolve_billable_cost`` produces the closest *runtime* approximation of
    spend under the ordered rules below. Dollar caps are only as accurate as
    the ``cost_usd`` you (or this helper) pass to ``BudgetGuard.consume``.
    This is not a substitute for reconciling provider invoices.

Cost resolution order (per LLM response / billable event)
    A. Provider-reported numeric cost on response or usage
       (``cost`` / ``cost_usd`` / ``total_cost`` / ``total_cost_usd``)
    B. Documented provider-specific billed fields (gateway markup included)
    C. Compute from usage x caller-owned price table (in/out/cached/special/units)
    D. ``agentguard.estimate_cost`` only when the model is known and returns > 0
    E. Conservative overestimate, or fail-loud when ``strict=True``

Never silently treat an unknown/uncomputable successful LLM call as $0 under a
dollar budget. Tool-only steps and intentional free/local models may use
``source=zero`` with ``cost_usd=0``.
"""

from __future__ import annotations

import logging
import os
import warnings
from typing import Any, Dict, Mapping, Optional, Tuple

from agentguard.cost import LAST_UPDATED as _ESTIMATE_LAST_UPDATED
from agentguard.cost import UnknownModelWarning, estimate_cost
from agentguard.price_table import (
    _DEFAULT_HIGH_WATER_PER_TOKEN,
    _DEFAULT_MIN_CHARGE_USD,
    DEFAULT_PRICE_TABLE,
    PriceRate,
    PriceTable,
    get_default_prices,
)
from agentguard.usage import normalize_usage

logger = logging.getLogger("agentguard.precision_cost")

# Re-export price table symbols for public import path via precision_cost.
__all__ = [
    "ALLOWED_SOURCES",
    "DEFAULT_PRICE_TABLE",
    "SOURCE_COMPUTED",
    "SOURCE_ESTIMATE",
    "SOURCE_OVERESTIMATE",
    "SOURCE_PROVIDER",
    "SOURCE_ZERO",
    "CostResolutionError",
    "PriceRate",
    "PriceTable",
    "consume_billable",
    "extract_tokens",
    "get_default_prices",
    "log_consume_event",
    "resolve_billable_cost",
]

# Source labels for consume logs and resolve results.
SOURCE_PROVIDER = "provider"
SOURCE_COMPUTED = "computed"
SOURCE_ESTIMATE = "estimate"
SOURCE_ZERO = "zero"
SOURCE_OVERESTIMATE = "overestimate"

ALLOWED_SOURCES = frozenset(
    {
        SOURCE_PROVIDER,
        SOURCE_COMPUTED,
        SOURCE_ESTIMATE,
        SOURCE_ZERO,
        SOURCE_OVERESTIMATE,
    }
)

# Provider-specific billed cost field names (step B). Checked on response then usage.
# Documented here so gateway markups (LiteLLM, OpenRouter, Azure) are preferred
# over raw OpenAI list rates when the gateway reports what it actually billed.
_PROVIDER_BILLED_FIELDS: Tuple[str, ...] = (
    "billed_cost",
    "billed_cost_usd",
    "total_cost",
    "total_cost_usd",
    "response_cost",
    "response_cost_usd",
    # LiteLLM / OpenRouter-style
    "x_litellm_response_cost",
    "x_litellm_cost",
    "usage_cost",
    "cost",
    "cost_usd",
)

# Generic numeric cost fields for step A (response-level and usage-level).
_GENERIC_COST_FIELDS: Tuple[str, ...] = (
    "cost_usd",
    "cost",
    "total_cost_usd",
    "total_cost",
)


class CostResolutionError(ValueError):
    """Raised when cost cannot be resolved under strict precision mode."""


# ---------------------------------------------------------------------------
# Response / usage introspection helpers
# ---------------------------------------------------------------------------


def _as_mapping(obj: Any) -> Optional[Mapping[str, Any]]:
    if obj is None:
        return None
    if isinstance(obj, Mapping):
        return obj
    # SDK objects often expose attributes
    data: Dict[str, Any] = {}
    for key in (
        "usage",
        "cost",
        "cost_usd",
        "total_cost",
        "total_cost_usd",
        "billed_cost",
        "billed_cost_usd",
        "response_cost",
        "response_cost_usd",
        "model",
        "id",
        "request_id",
        "_request_id",
        "headers",
        "usage_metadata",
        "candidates",
    ):
        if hasattr(obj, key):
            data[key] = getattr(obj, key)
    # Also pull common dunder/model_dump
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        try:
            dumped = obj.model_dump()
            if isinstance(dumped, dict):
                data.update(dumped)
        except Exception:  # pragma: no cover — defensive
            pass
    return data or None


def _get_attr_or_key(obj: Any, key: str) -> Any:
    if obj is None:
        return None
    if isinstance(obj, Mapping):
        return obj.get(key)
    return getattr(obj, key, None)


def _numeric_cost(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        # Negative costs are nonsense for billing; ignore
        if value < 0:
            return None
        return float(value)
    if isinstance(value, str):
        try:
            parsed = float(value.strip().replace("$", ""))
        except ValueError:
            return None
        if parsed < 0:
            return None
        return parsed
    return None


def _extract_request_id(response: Any) -> Optional[str]:
    for key in ("request_id", "id", "_request_id"):
        val = _get_attr_or_key(response, key)
        if isinstance(val, str) and val:
            return val
    headers = _get_attr_or_key(response, "headers")
    if isinstance(headers, Mapping):
        for hk in (
            "x-request-id",
            "request-id",
            "x-openai-request-id",
            "anthropic-organization-id",
        ):
            hv = headers.get(hk) or headers.get(hk.title())
            if isinstance(hv, str) and hv:
                return hv
    return None


def _extract_usage_object(response: Any) -> Any:
    """Pull usage from a full response, a bare usage dict, or Google usage_metadata."""
    if response is None:
        return None
    usage = _get_attr_or_key(response, "usage")
    if usage is not None:
        return usage
    usage_meta = _get_attr_or_key(response, "usage_metadata")
    if usage_meta is not None:
        # Google generative AI style → normalize later via generic fields
        return {
            "input_tokens": _get_attr_or_key(usage_meta, "prompt_token_count")
            or _get_attr_or_key(usage_meta, "input_tokens")
            or 0,
            "output_tokens": _get_attr_or_key(usage_meta, "candidates_token_count")
            or _get_attr_or_key(usage_meta, "output_tokens")
            or 0,
            "total_tokens": _get_attr_or_key(usage_meta, "total_token_count")
            or _get_attr_or_key(usage_meta, "total_tokens")
            or 0,
            "cached_input_tokens": _get_attr_or_key(usage_meta, "cached_content_token_count") or 0,
        }
    # Bare usage payload passed as response
    if isinstance(response, Mapping):
        keys = set(response.keys())
        usage_keys = {
            "prompt_tokens",
            "completion_tokens",
            "total_tokens",
            "input_tokens",
            "output_tokens",
            "cache_read_input_tokens",
            "prompt_tokens_details",
        }
        if keys & usage_keys:
            return response
    return None


def extract_tokens(
    response: Any,
    *,
    provider: Optional[str] = None,
) -> Dict[str, int]:
    """Normalize token counts from a response or usage payload.

    OpenAI: prompt_tokens / completion_tokens / total_tokens (+ cached details)
    Anthropic: input_tokens / output_tokens (+ cache read/write)
    Google/others: similar via normalize_usage / usage_metadata
    total = input + output when total missing.
    """
    usage = _extract_usage_object(response)
    normalized = normalize_usage(usage, provider=provider) if usage is not None else None
    if not normalized:
        return {
            "input": 0,
            "output": 0,
            "cached": 0,
            "cache_write": 0,
            "reasoning": 0,
            "total": 0,
        }
    input_t = int(normalized.get("input_tokens", 0) or 0)
    output_t = int(normalized.get("output_tokens", 0) or 0)
    cached = int(normalized.get("cached_input_tokens", 0) or 0)
    cache_write = int(normalized.get("cache_write_input_tokens", 0) or 0)
    reasoning = int(normalized.get("reasoning_tokens", 0) or 0)
    total = int(normalized.get("total_tokens", 0) or 0)
    if total <= 0:
        total = input_t + output_t + cached + cache_write
    return {
        "input": input_t,
        "output": output_t,
        "cached": cached,
        "cache_write": cache_write,
        "reasoning": reasoning,
        "total": total,
    }


def _find_provider_cost(response: Any, usage: Any) -> Optional[float]:
    """Steps A+B: numeric provider / gateway billed cost fields."""
    for container in (response, usage):
        if container is None:
            continue
        for field in _GENERIC_COST_FIELDS:
            cost = _numeric_cost(_get_attr_or_key(container, field))
            if cost is not None:
                return cost
        for field in _PROVIDER_BILLED_FIELDS:
            cost = _numeric_cost(_get_attr_or_key(container, field))
            if cost is not None:
                return cost
        # Nested usage.cost inside response already covered; also check .usage
        nested_usage = _get_attr_or_key(container, "usage")
        if nested_usage is not None and nested_usage is not usage:
            for field in list(_GENERIC_COST_FIELDS) + list(_PROVIDER_BILLED_FIELDS):
                cost = _numeric_cost(_get_attr_or_key(nested_usage, field))
                if cost is not None:
                    return cost
    return None


def _lookup_rate(
    prices: PriceTable,
    provider: str,
    model: str,
) -> Optional[PriceRate]:
    rates: Mapping[Any, Any] = prices.get("rates") or {}
    aliases: Mapping[Any, Any] = prices.get("aliases") or {}
    provider_l = (provider or "").strip().lower()
    model_id = (model or "").strip()

    # Exact match
    key = (provider_l, model_id)
    if key in rates:
        return dict(rates[key])

    # Alias exact
    if key in aliases:
        target = aliases[key]
        if isinstance(target, tuple) and target in rates:
            return dict(rates[target])

    # Normalized model (lower, strip date-ish suffix partially handled by aliases)
    model_l = model_id.lower()
    key_l = (provider_l, model_l)
    if key_l in rates:
        return dict(rates[key_l])
    if key_l in aliases:
        target = aliases[key_l]
        if isinstance(target, tuple) and target in rates:
            return dict(rates[target])

    # Scan rates for case-insensitive model match under provider
    for (p, m), rate in rates.items():
        if str(p).lower() == provider_l and str(m).lower() == model_l:
            return dict(rate)

    # Alias scan
    for (p, m), target in aliases.items():
        if str(p).lower() == provider_l and str(m).lower() == model_l:
            if isinstance(target, tuple) and target in rates:
                return dict(rates[target])
            # target may need re-lookup
            if isinstance(target, tuple):
                return _lookup_rate(
                    {"rates": rates, "aliases": {}},
                    str(target[0]),
                    str(target[1]),
                )
    return None


# Providers whose input_tokens already exclude cache-read tokens (bill input +
# cache_read separately). OpenAI-family includes cached tokens inside
# prompt_tokens and must subtract to avoid double-billing the cached slice.
_CACHE_EXCLUSIVE_INPUT_PROVIDERS = frozenset(
    {
        "anthropic",
        "google",
    }
)


def _input_includes_cached(provider: str) -> bool:
    """True when prompt/input token count already includes cached tokens."""
    return (provider or "").strip().lower() not in _CACHE_EXCLUSIVE_INPUT_PROVIDERS


def _compute_from_table(
    tokens: Mapping[str, int],
    rate: PriceRate,
    *,
    provider: str = "",
    batch: bool = False,
    image_units: int = 0,
) -> Tuple[float, Dict[str, Any]]:
    """Compute USD from usage and a rate dict (prices per 1M tokens).

    Provider-aware cache handling:
    - OpenAI / Azure / most gateways: ``prompt_tokens`` *includes* cached
      tokens → bill ``(input - cached) * in + cached * cached_in``.
    - Anthropic / Google: ``input_tokens`` *excludes* cache reads → bill
      ``input * in + cache_read * cached_in + cache_write * write`` with no
      subtraction (subtracting would silently under-count).
    """
    if rate.get("free"):
        return 0.0, {"free": 0.0}

    input_t = int(tokens.get("input", 0) or 0)
    output_t = int(tokens.get("output", 0) or 0)
    cached_t = int(tokens.get("cached", 0) or 0)
    cache_write_t = int(tokens.get("cache_write", 0) or 0)
    reasoning_t = int(tokens.get("reasoning", 0) or 0)

    if cached_t > 0 and _input_includes_cached(provider) and cached_t <= input_t:
        uncached_input = input_t - cached_t
        input_cache_mode = "inclusive"
    else:
        # Exclusive (Anthropic/Google) or no cache / cache > input edge case
        uncached_input = input_t
        input_cache_mode = (
            "exclusive" if not _input_includes_cached(provider) else "inclusive_no_subtract"
        )

    in_price = float(rate.get("input_per_1m", 0.0))
    out_price = float(rate.get("output_per_1m", 0.0))
    cached_price = float(rate.get("cached_input_per_1m", in_price))
    cache_write_price = float(rate.get("cache_write_per_1m", in_price * 1.25))
    reasoning_price = float(rate.get("reasoning_per_1m", out_price))
    image_price = float(rate.get("image_per_unit", 0.0))

    breakdown: Dict[str, Any] = {
        "input_usd": uncached_input * in_price / 1_000_000,
        "output_usd": output_t * out_price / 1_000_000,
        "cached_input_usd": cached_t * cached_price / 1_000_000,
        "cache_write_usd": cache_write_t * cache_write_price / 1_000_000,
        "reasoning_usd": reasoning_t * reasoning_price / 1_000_000,
        "image_usd": image_units * image_price,
        "input_cache_mode": input_cache_mode,
        "uncached_input_tokens": uncached_input,
    }
    total = (
        float(breakdown["input_usd"])
        + float(breakdown["output_usd"])
        + float(breakdown["cached_input_usd"])
        + float(breakdown["cache_write_usd"])
        + float(breakdown["reasoning_usd"])
        + float(breakdown["image_usd"])
    )
    if batch:
        discount = float(rate.get("batch_discount", 0.5))
        total *= discount
        breakdown["batch_discount"] = discount
    return total, breakdown


def _overestimate_cost(
    tokens: Mapping[str, int],
    prices: PriceTable,
) -> float:
    over = prices.get("overestimate") or {}
    min_charge = float(over.get("min_charge_usd", _DEFAULT_MIN_CHARGE_USD))
    high_water = float(over.get("high_water_per_token", _DEFAULT_HIGH_WATER_PER_TOKEN))
    total_tokens = int(tokens.get("total", 0) or 0)
    if total_tokens <= 0:
        # Successful LLM call with no usage: still charge min under non-strict
        return min_charge
    return max(min_charge, total_tokens * high_water)


def _env_strict(strict: bool) -> bool:
    if strict:
        return True
    flag = os.environ.get("STRICT_PRECISION", "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def resolve_billable_cost(
    response: Any,
    *,
    model: str,
    provider: str,
    prices: Optional[PriceTable] = None,
    strict: bool = False,
    billable_llm: bool = True,
    free_local: bool = False,
    batch: bool = False,
    image_units: int = 0,
) -> Dict[str, Any]:
    """Resolve a single billable unit's cost from a provider response.

    Pure function: no BudgetGuard side effects, no network I/O.

    Args:
        response: Full provider response, or a usage-shaped mapping. Streaming
            callers must pass the *final* usage object once (not partial chunks).
        model: Model id as used on the request.
        provider: Provider key (openai, anthropic, google, azure, gateway name…).
        prices: Caller-owned versioned price table. Defaults to
            ``DEFAULT_PRICE_TABLE``.
        strict: If True (or env STRICT_PRECISION=1), refuse unresolvable LLM
            costs instead of overestimating.
        billable_llm: False for tool-only steps with no LLM (cost 0, source zero).
        free_local: True when the model is intentionally free/local.
        batch: Apply batch_discount from the rate row when computing.
        image_units: Optional vision/image unit count for unit pricing.

    Returns:
        Mapping with keys:
            cost_usd, tokens, source, breakdown
            (plus request_id when available)

    Raises:
        CostResolutionError: Under strict mode when cost cannot be determined
            for a billable LLM call without silent $0.
    """
    price_table = prices if prices is not None else DEFAULT_PRICE_TABLE
    tokens = extract_tokens(response, provider=provider)
    usage = _extract_usage_object(response)
    request_id = _extract_request_id(response)
    is_strict = _env_strict(strict)

    base_breakdown: Dict[str, Any] = {
        "model": model,
        "provider": provider,
        "price_table_version": price_table.get("version"),
        "price_table_last_updated": price_table.get("last_updated"),
        "estimate_table_last_updated": _ESTIMATE_LAST_UPDATED,
    }

    # Tool-only / intentional free local: $0 is legitimate
    if not billable_llm or free_local:
        result = {
            "cost_usd": 0.0,
            "tokens": tokens,
            "source": SOURCE_ZERO,
            "breakdown": {**base_breakdown, "reason": "tool_only_or_free_local"},
        }
        if request_id:
            result["request_id"] = request_id
        return result

    # Local/free rate row
    rate = _lookup_rate(price_table, provider, model)
    if rate is not None and rate.get("free"):
        result = {
            "cost_usd": 0.0,
            "tokens": tokens,
            "source": SOURCE_ZERO,
            "breakdown": {**base_breakdown, "reason": "free_model_rate"},
        }
        if request_id:
            result["request_id"] = request_id
        return result

    # A+B: provider / gateway billed cost
    provider_cost = _find_provider_cost(response, usage)
    if provider_cost is not None:
        result = {
            "cost_usd": float(provider_cost),
            "tokens": tokens,
            "source": SOURCE_PROVIDER,
            "breakdown": {
                **base_breakdown,
                "provider_cost": float(provider_cost),
            },
        }
        if request_id:
            result["request_id"] = request_id
        return result

    has_usage = tokens["total"] > 0 or tokens["input"] > 0 or tokens["output"] > 0

    # C: compute from owned price table
    if rate is not None and has_usage:
        computed, parts = _compute_from_table(
            tokens,
            rate,
            provider=provider,
            batch=batch,
            image_units=image_units,
        )
        result = {
            "cost_usd": float(computed),
            "tokens": tokens,
            "source": SOURCE_COMPUTED,
            "breakdown": {**base_breakdown, **parts, "rate": rate},
        }
        if request_id:
            result["request_id"] = request_id
        return result

    # D: estimate_cost fallback only if known model and returns > 0
    if has_usage:
        # Suppress UnknownModelWarning here: $0 from estimate is a miss and we
        # continue to overestimate/fail-loud (never silent under-count).
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UnknownModelWarning)
            estimated = estimate_cost(
                model,
                input_tokens=tokens["input"] or tokens["total"],
                output_tokens=tokens["output"],
                provider=provider or None,
            )
        # estimate_cost returns 0 for unknown — treat 0 as miss
        if estimated > 0:
            result = {
                "cost_usd": float(estimated),
                "tokens": tokens,
                "source": SOURCE_ESTIMATE,
                "breakdown": {
                    **base_breakdown,
                    "estimate_usd": float(estimated),
                },
            }
            if request_id:
                result["request_id"] = request_id
            return result

    # E: fail-loud or conservative overestimate — NEVER silent $0 for billable LLM
    if is_strict:
        raise CostResolutionError(
            f"Cannot resolve billable cost for model={model!r} provider={provider!r} "
            f"(usage_total={tokens['total']}, rate_found={rate is not None}). "
            "STRICT_PRECISION refuses silent $0. Pass provider cost, a price row, "
            "or disable strict and accept a conservative overestimate."
        )

    over = _overestimate_cost(tokens, price_table)
    result = {
        "cost_usd": float(over),
        "tokens": tokens,
        "source": SOURCE_OVERESTIMATE,
        "breakdown": {
            **base_breakdown,
            "overestimate_usd": float(over),
            "reason": "unknown_model_or_missing_usage",
            "has_usage": has_usage,
            "rate_found": rate is not None,
        },
    }
    if request_id:
        result["request_id"] = request_id
    return result


def log_consume_event(
    *,
    model: str,
    provider: str,
    tokens: Mapping[str, int],
    cost_usd: float,
    source_of_cost: str,
    request_id: Optional[str] = None,
    extra: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build and log a structured consume record (rule 15)."""
    record: Dict[str, Any] = {
        "model": model,
        "provider": provider,
        "input_tokens": int(tokens.get("input", 0) or 0),
        "output_tokens": int(tokens.get("output", 0) or 0),
        "cached_tokens": int(tokens.get("cached", 0) or 0),
        "total_tokens": int(tokens.get("total", 0) or 0),
        "cost_usd": float(cost_usd),
        "source_of_cost": source_of_cost,
    }
    if request_id:
        record["request_id"] = request_id
    if extra:
        record.update(dict(extra))
    logger.info(
        "budget.consume model=%s provider=%s input=%s output=%s cached=%s "
        "cost_usd=%s source_of_cost=%s request_id=%s",
        record["model"],
        record["provider"],
        record["input_tokens"],
        record["output_tokens"],
        record["cached_tokens"],
        record["cost_usd"],
        record["source_of_cost"],
        record.get("request_id"),
    )
    return record


def consume_billable(
    budget: Any,
    response: Any,
    *,
    model: str,
    provider: str,
    prices: Optional[PriceTable] = None,
    strict: bool = False,
    calls: int = 1,
    billable_llm: bool = True,
    free_local: bool = False,
    batch: bool = False,
    image_units: int = 0,
) -> Dict[str, Any]:
    """Resolve cost then feed ``BudgetGuard.consume`` once (no double-count).

    Attributes the crossing call before ``BudgetExceeded`` (BudgetGuard already
    records goal ledgers before raising). Logs every consume with model,
    provider, token axes, cost_usd, source_of_cost, and request_id.

    Use this helper for sync, async, streaming-final, and retry attempts —
    call once per provider hit so retries count each attempt.

    Returns:
        The resolve_billable_cost result, with an added ``consume_log`` field.
    """
    resolved = resolve_billable_cost(
        response,
        model=model,
        provider=provider,
        prices=prices,
        strict=strict,
        billable_llm=billable_llm,
        free_local=free_local,
        batch=batch,
        image_units=image_units,
    )
    tokens = resolved["tokens"]
    total_tokens = int(tokens.get("total", 0) or 0)
    cost_usd = float(resolved["cost_usd"])
    source = str(resolved["source"])
    request_id = resolved.get("request_id")

    consume_log = log_consume_event(
        model=model,
        provider=provider,
        tokens=tokens,
        cost_usd=cost_usd,
        source_of_cost=source,
        request_id=request_id if isinstance(request_id, str) else None,
    )
    resolved = dict(resolved)
    resolved["consume_log"] = consume_log

    if budget is not None:
        budget.consume(tokens=total_tokens, calls=calls, cost_usd=cost_usd)
    return resolved
