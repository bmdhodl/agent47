import json
import os
import tempfile
import unittest
from unittest.mock import MagicMock

from agentguard.instrument import trace_agent, trace_tool, patch_openai, patch_anthropic
from agentguard.tracing import JsonlFileSink, Tracer


class TestTraceAgentDecorator(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        os.close(self.fd)
        self.tracer = Tracer(sink=JsonlFileSink(self.path), service="test")

    def tearDown(self):
        os.unlink(self.path)

    def test_wraps_function_in_trace(self):
        @trace_agent(self.tracer)
        def my_agent(x):
            return x + 1

        result = my_agent(5)
        self.assertEqual(result, 6)

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("agent.my_agent", names)

    def test_custom_name(self):
        @trace_agent(self.tracer, name="custom.agent")
        def do_stuff():
            return "done"

        do_stuff()

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("custom.agent", names)

    def test_preserves_exceptions(self):
        @trace_agent(self.tracer)
        def failing():
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            failing()

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        # Should have start and end spans, end should have error
        end_events = [e for e in events if e.get("phase") == "end"]
        self.assertTrue(len(end_events) > 0)
        self.assertIsNotNone(end_events[0].get("error"))


class TestTraceToolDecorator(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        os.close(self.fd)
        self.tracer = Tracer(sink=JsonlFileSink(self.path), service="test")

    def tearDown(self):
        os.unlink(self.path)

    def test_wraps_tool_in_span(self):
        @trace_tool(self.tracer)
        def search(query):
            return f"results for {query}"

        result = search("hello")
        self.assertEqual(result, "results for hello")

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("tool.search", names)

    def test_emits_tool_result_event(self):
        @trace_tool(self.tracer)
        def lookup(key):
            return "value"

        lookup("k")

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        result_events = [e for e in events if e.get("name") == "tool.result"]
        self.assertTrue(len(result_events) > 0)

    def test_custom_tool_name(self):
        @trace_tool(self.tracer, name="tool.custom_search")
        def my_fn():
            return 42

        my_fn()

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("tool.custom_search", names)


class TestPatchOpenAI(unittest.TestCase):
    def test_no_crash_without_openai(self):
        """patch_openai should silently return if openai not installed."""
        tracer = MagicMock()
        # This should not raise
        patch_openai(tracer)


class TestPatchAnthropic(unittest.TestCase):
    def test_no_crash_without_anthropic(self):
        """patch_anthropic should silently return if anthropic not installed."""
        tracer = MagicMock()
        # This should not raise
        patch_anthropic(tracer)


if __name__ == "__main__":
    unittest.main()
