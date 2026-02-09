"""Tests for LangGraph integration (guarded_node / guard_node)."""
from __future__ import annotations

import json
import os
import tempfile
import unittest

from agentguard import Tracer, JsonlFileSink, LoopGuard, BudgetGuard
from agentguard.guards import LoopDetected, BudgetExceeded
from agentguard.integrations.langgraph import guarded_node, guard_node


class TestGuardedNode(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._trace_path = os.path.join(self._tmpdir, "traces.jsonl")
        self.sink = JsonlFileSink(self._trace_path)
        self.tracer = Tracer(sink=self.sink, service="test-langgraph")

    def _read_events(self):
        with open(self._trace_path, "r") as f:
            return [json.loads(line) for line in f if line.strip()]

    def test_basic_node_tracing(self):
        """Decorated node produces span events."""

        @guarded_node(tracer=self.tracer)
        def my_node(state):
            return {"result": "done"}

        result = my_node({"messages": ["hello"]})
        self.assertEqual(result, {"result": "done"})

        events = self._read_events()
        names = [e["name"] for e in events]
        self.assertIn("node.my_node", names)

    def test_node_with_dict_state(self):
        """State dict is summarized in span data."""

        @guarded_node(tracer=self.tracer)
        def process(state):
            return {"output": state.get("input", "")}

        process({"input": "test value", "messages": ["a", "b", "c"]})

        events = self._read_events()
        start_events = [e for e in events if e.get("phase") == "start"]
        self.assertTrue(len(start_events) > 0)
        data = start_events[0].get("data", {})
        self.assertEqual(data.get("message_count"), 3)

    def test_custom_name(self):
        """Custom span name is used."""

        @guarded_node(tracer=self.tracer, name="research.step")
        def my_node(state):
            return state

        my_node({})
        events = self._read_events()
        names = [e["name"] for e in events]
        self.assertIn("research.step", names)

    def test_loop_guard_fires(self):
        """LoopGuard raises after repeated identical calls."""
        loop_guard = LoopGuard(max_repeats=3)

        @guarded_node(tracer=self.tracer, loop_guard=loop_guard)
        def stuck_node(state):
            return state

        # First two calls should succeed
        stuck_node({"key": "same"})
        stuck_node({"key": "same"})

        # Third identical call triggers max_repeats=3
        with self.assertRaises(LoopDetected):
            stuck_node({"key": "same"})

    def test_budget_guard_fires(self):
        """BudgetGuard raises after call limit."""
        budget_guard = BudgetGuard(max_calls=2)

        @guarded_node(tracer=self.tracer, budget_guard=budget_guard)
        def costly_node(state):
            return state

        costly_node({"a": 1})
        costly_node({"a": 2})

        with self.assertRaises(BudgetExceeded):
            costly_node({"a": 3})

    def test_guard_node_functional_form(self):
        """guard_node() wraps a plain function."""

        def plain_fn(state):
            return {"wrapped": True}

        wrapped = guard_node(plain_fn, tracer=self.tracer)
        result = wrapped({"input": "x"})
        self.assertEqual(result, {"wrapped": True})

        events = self._read_events()
        names = [e["name"] for e in events]
        self.assertIn("node.plain_fn", names)

    def test_node_exception_propagates(self):
        """Exceptions from the node propagate through."""

        @guarded_node(tracer=self.tracer)
        def failing_node(state):
            raise ValueError("node failed")

        with self.assertRaises(ValueError):
            failing_node({})

        events = self._read_events()
        # Should still have trace events (span start/end with error)
        self.assertTrue(len(events) > 0)

    def test_node_returns_none(self):
        """Node returning None doesn't crash."""

        @guarded_node(tracer=self.tracer)
        def noop_node(state):
            return None

        result = noop_node({})
        self.assertIsNone(result)

    def test_default_tracer(self):
        """Works without explicit tracer (creates default)."""

        @guarded_node()
        def auto_node(state):
            return {"ok": True}

        result = auto_node({})
        self.assertEqual(result, {"ok": True})


class TestSummarizeState(unittest.TestCase):
    def test_none_state(self):
        from agentguard.integrations.langgraph import _summarize_state

        self.assertEqual(_summarize_state(None), {})

    def test_dict_state_with_messages(self):
        from agentguard.integrations.langgraph import _summarize_state

        result = _summarize_state({"messages": ["a", "b", "c"], "key": "val"})
        self.assertEqual(result["message_count"], 3)
        self.assertEqual(result["last_message"], "c")
        self.assertEqual(result["key"], "val")

    def test_non_dict_state(self):
        from agentguard.integrations.langgraph import _summarize_state

        result = _summarize_state("just a string")
        self.assertIn("state", result)


if __name__ == "__main__":
    unittest.main()
