"""Golden usage / response payloads for precision cost resolution tests.

Shapes mirror real OpenAI, Anthropic, and gateway responses. Not live API data.
"""
from __future__ import annotations

from typing import Any, Dict

# OpenAI Chat Completions style (prompt/completion + cached details)
OPENAI_GPT4O_USAGE: Dict[str, Any] = {
    "id": "chatcmpl-fixture-openai-001",
    "model": "gpt-4o",
    "usage": {
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "total_tokens": 1500,
        "prompt_tokens_details": {"cached_tokens": 200},
        "completion_tokens_details": {"reasoning_tokens": 0},
    },
}

# OpenAI with provider-reported cost preferred over table compute
OPENAI_WITH_PROVIDER_COST: Dict[str, Any] = {
    "id": "chatcmpl-fixture-openai-cost",
    "model": "gpt-4o",
    "cost": 0.042,
    "usage": {
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "total_tokens": 1500,
    },
}

# Anthropic Messages API style
ANTHROPIC_SONNET_USAGE: Dict[str, Any] = {
    "id": "msg_fixture_anthropic_001",
    "model": "claude-3-5-sonnet-20241022",
    "usage": {
        "input_tokens": 800,
        "output_tokens": 400,
        "cache_read_input_tokens": 200,
        "cache_creation_input_tokens": 50,
    },
}

# Gateway (OpenRouter-like) with billed cost including markup
GATEWAY_BILLED_COST: Dict[str, Any] = {
    "id": "gen-fixture-gateway-001",
    "model": "openai/gpt-4o",
    "billed_cost_usd": 0.055,
    "usage": {
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "total_tokens": 1500,
    },
}

# Streaming final usage only (no partial chunks in payload)
STREAMING_FINAL_USAGE: Dict[str, Any] = {
    "id": "chatcmpl-stream-final",
    "model": "gpt-4o-mini",
    "usage": {
        "prompt_tokens": 120,
        "completion_tokens": 80,
        "total_tokens": 200,
    },
}

# Failed call that still carried usage (billed tokens)
FAILED_WITH_USAGE: Dict[str, Any] = {
    "id": "chatcmpl-failed-usage",
    "error": {"message": "content_filter", "type": "invalid_request_error"},
    "usage": {
        "prompt_tokens": 50,
        "completion_tokens": 10,
        "total_tokens": 60,
    },
}

# Missing usage entirely (strict mode must fail / non-strict overestimate)
MISSING_USAGE: Dict[str, Any] = {
    "id": "chatcmpl-no-usage",
    "model": "mystery-model-xyz",
    "choices": [{"message": {"content": "hi"}}],
}
