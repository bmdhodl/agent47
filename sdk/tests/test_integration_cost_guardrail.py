"""Integration test: cost guardrail pipeline → mock ingest → verify via /api/v1/traces.

Exercises the full cost guardrail pipeline:
  BudgetGuard → patch_openai → BudgetExceeded → HttpSink → mock server → query traces

CI-friendly: uses local mock server (no external deps).
"""
from __future__ import annotations

import json
import sys
import time
import types
import urllib.request

import pytest

from agentguard import (
    BudgetExceeded,
    BudgetGuard,
    Tracer,
)
from agentguard.instrument import (
    _originals,
    patch_openai,
    unpatch_openai,
)
from agentguard.sinks.http import HttpSink

from conftest import IngestHandler


def _make_mock_openai(prompt_tokens=1000, completion_tokens=500, total_tokens=1500):
    """Create a mock openai module with predictable token usage."""
    usage = types.SimpleNamespace(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
    result = types.SimpleNamespace(usage=usage)

    class MockCompletions:
        def create(self, *args, **kwargs):
            return result

    class MockChat:
        def __init__(self):
            self.completions = MockCompletions()

    class MockOpenAI:
        def __init__(self, *args, **kwargs):
            self.chat = MockChat()

    mod = types.ModuleType("openai")
    mod.OpenAI = MockOpenAI
    return mod, MockOpenAI


class TestIntegrationCostGuardrail:
    """Full integration: agent → budget guard → HttpSink → mock server → query."""

    def test_cost_guardrail_pipeline(self, ingest_url):
        """Run agent loop until BudgetExceeded, then verify events on server."""
        # --- Setup ---
        warnings = []
        guard = BudgetGuard(
            max_cost_usd=0.05,
            warn_at_pct=0.3,
            on_warning=warnings.append,
        )

        # Parse server URL from ingest_url to build query URL
        base_url = ingest_url.replace("/api/ingest", "")

        http_sink = HttpSink(
            url=ingest_url,
            api_key="ag_test_key_e2e",
            batch_size=5,
            flush_interval=0.2,
            compress=True,
            _allow_private=True,
        )
        tracer = Tracer(
            sink=http_sink,
            service="integration-cost-test",
            guards=[guard],
        )

        # --- Mock OpenAI ---
        mod, cls = _make_mock_openai(1000, 500, 1500)
        sys.modules["openai"] = mod
        _originals.clear()
        patch_openai(tracer, budget_guard=guard)

        # --- Run agent loop until BudgetExceeded ---
        exceeded = False
        calls_made = 0
        try:
            client = cls()
            for _ in range(50):  # safety cap
                client.chat.completions.create(model="gpt-4o")
                calls_made += 1
        except BudgetExceeded:
            exceeded = True
        finally:
            unpatch_openai()
            del sys.modules["openai"]
            _originals.clear()

        # --- Flush sink ---
        http_sink.shutdown()
        time.sleep(0.5)

        # --- Assertions on guard state ---
        assert exceeded, "BudgetExceeded should have been raised"
        assert calls_made > 0, "At least one call should have succeeded"
        assert len(warnings) > 0, "Budget warning callback should have fired"

        # --- Assertions on IngestHandler events ---
        events = IngestHandler.events
        names = [e.get("name", "") for e in events]

        assert "guard.budget_warning" in names, (
            f"Expected guard.budget_warning in events, got: {names}"
        )
        assert "guard.budget_exceeded" in names, (
            f"Expected guard.budget_exceeded in events, got: {names}"
        )

        # LLM events have cost
        llm_events = [e for e in events if e.get("name") == "llm.result"]
        assert len(llm_events) > 0, "Expected at least one llm.result event"
        for le in llm_events:
            cost = le.get("cost_usd")
            if cost is None and isinstance(le.get("data"), dict):
                cost = le["data"].get("cost_usd")
            assert cost is not None and cost > 0, (
                f"llm.result should have cost_usd > 0, got: {le}"
            )

        # No cost double-counting: cost_usd should be at top level OR in data, not both
        for le in llm_events:
            top = le.get("cost_usd")
            nested = le.get("data", {}).get("cost_usd") if isinstance(le.get("data"), dict) else None
            if top is not None and nested is not None:
                pytest.fail(f"cost_usd found at both top-level and data: {le}")

        # --- Verify via /api/v1/traces endpoint ---
        req = urllib.request.Request(f"{base_url}/api/v1/traces")
        with urllib.request.urlopen(req) as resp:
            body = json.loads(resp.read().decode())

        traces = body.get("traces", [])
        assert len(traces) > 0, "Expected at least one trace"

        total_cost_all = sum(t["total_cost"] for t in traces)
        total_events_all = sum(t["event_count"] for t in traces)

        assert total_cost_all > 0, (
            f"Total cost across traces should be > 0, got: {total_cost_all}"
        )
        assert total_events_all > 0, (
            f"Total event count across traces should be > 0, got: {total_events_all}"
        )
        assert total_events_all == len(events), (
            f"Sum of trace event_counts ({total_events_all}) should match "
            f"server events ({len(events)})"
        )
