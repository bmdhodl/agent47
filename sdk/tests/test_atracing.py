"""Tests for AsyncTracer, AsyncTraceContext, and async decorators."""
import asyncio
import json
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock

from agentguard import (
    AsyncTracer,
    AsyncTraceContext,
    BudgetExceeded,
    BudgetGuard,
    JsonlFileSink,
    LoopGuard,
    LoopDetected,
)
from agentguard.instrument import (
    _originals,
    async_trace_agent,
    async_trace_tool,
    patch_openai_async,
    patch_anthropic_async,
    unpatch_openai_async,
    unpatch_anthropic_async,
)


class TestAsyncTracer(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        os.close(self.fd)

    def tearDown(self):
        os.unlink(self.path)

    def test_trace_emits_start_and_end(self):
        async def run():
            tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")
            async with tracer.trace("agent.run") as span:
                span.event("reasoning.step", data={"step": 1})

        asyncio.run(run())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("agent.run", names)
        self.assertIn("reasoning.step", names)
        phases = [e.get("phase") for e in events if e["name"] == "agent.run"]
        self.assertIn("start", phases)
        self.assertIn("end", phases)

    def test_nested_spans(self):
        async def run():
            tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")
            async with tracer.trace("agent.run") as span:
                async with span.span("tool.search") as child:
                    child.event("tool.result", data={"result": "found"})

        asyncio.run(run())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("tool.search", names)
        self.assertIn("tool.result", names)

    def test_error_recorded_on_exception(self):
        async def run():
            tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")
            try:
                async with tracer.trace("agent.run") as span:
                    raise ValueError("boom")
            except ValueError:
                pass

        asyncio.run(run())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        end_events = [e for e in events if e.get("phase") == "end"]
        self.assertTrue(len(end_events) > 0)
        self.assertIsNotNone(end_events[0].get("error"))
        self.assertEqual(end_events[0]["error"]["type"], "ValueError")

    def test_duration_recorded(self):
        async def run():
            tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")
            async with tracer.trace("agent.run"):
                await asyncio.sleep(0.01)

        asyncio.run(run())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        end_events = [e for e in events if e.get("phase") == "end"]
        self.assertTrue(len(end_events) > 0)
        self.assertIsNotNone(end_events[0].get("duration_ms"))
        self.assertGreater(end_events[0]["duration_ms"], 0)

    def test_guards_auto_check(self):
        async def run():
            guard = LoopGuard(max_repeats=3)
            tracer = AsyncTracer(
                sink=JsonlFileSink(self.path),
                service="test",
                guards=[guard],
            )
            async with tracer.trace("agent.run") as span:
                span.event("tool.search", data={"q": "a"})
                span.event("tool.search", data={"q": "a"})
                with self.assertRaises(LoopDetected):
                    span.event("tool.search", data={"q": "a"})

        asyncio.run(run())

    def test_cost_tracker(self):
        async def run():
            tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")
            async with tracer.trace("agent.run") as span:
                span.cost.add("gpt-4o", input_tokens=100, output_tokens=50, provider="openai")
                self.assertGreater(span.cost.total, 0)

        asyncio.run(run())


    def test_guards_auto_check_uses_auto_check_method(self):
        """Verify AsyncTracer calls auto_check() (not just check()) for guards that have it."""
        auto_check_calls = []

        class MockGuard:
            def auto_check(self, name, data=None):
                auto_check_calls.append((name, data))

            def check(self, name, data=None):
                raise AssertionError("check() should not be called when auto_check() exists")

        async def run():
            guard = MockGuard()
            tracer = AsyncTracer(
                sink=JsonlFileSink(self.path),
                service="test",
                guards=[guard],
            )
            async with tracer.trace("agent.run") as span:
                span.event("tool.search", data={"q": "test"})

        asyncio.run(run())
        self.assertEqual(len(auto_check_calls), 1)
        self.assertEqual(auto_check_calls[0][0], "tool.search")

    def test_budget_guard_fires_via_consume(self):
        """Verify BudgetGuard raises BudgetExceeded when used with AsyncTracer context."""
        async def run():
            guard = BudgetGuard(max_calls=2)
            tracer = AsyncTracer(
                sink=JsonlFileSink(self.path),
                service="test",
            )
            async with tracer.trace("agent.run") as span:
                guard.consume(calls=1)
                span.event("tool.call1")
                guard.consume(calls=1)
                span.event("tool.call2")
                with self.assertRaises(BudgetExceeded):
                    guard.consume(calls=1)

        asyncio.run(run())

    def test_sampling_rate_zero_emits_nothing(self):
        """With sampling_rate=0.0, no events should be emitted to the sink."""
        async def run():
            tracer = AsyncTracer(
                sink=JsonlFileSink(self.path),
                service="test",
                sampling_rate=0.0,
            )
            async with tracer.trace("agent.run") as span:
                span.event("reasoning.step", data={"step": 1})

        asyncio.run(run())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        self.assertEqual(len(events), 0)

    def test_sampling_rate_one_emits_all(self):
        """With sampling_rate=1.0, all events should be emitted."""
        async def run():
            tracer = AsyncTracer(
                sink=JsonlFileSink(self.path),
                service="test",
                sampling_rate=1.0,
            )
            async with tracer.trace("agent.run") as span:
                span.event("reasoning.step")

        asyncio.run(run())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        # watermark + span start + event + span end = 4
        self.assertGreaterEqual(len(events), 3)

    def test_sampling_rate_invalid_raises(self):
        """sampling_rate outside 0.0-1.0 should raise ValueError."""
        with self.assertRaises(ValueError):
            AsyncTracer(sampling_rate=1.5)
        with self.assertRaises(ValueError):
            AsyncTracer(sampling_rate=-0.1)

    def test_guards_fire_when_sampled_out(self):
        """Guards must still fire even when trace is sampled out."""
        async def run():
            guard = LoopGuard(max_repeats=3)
            tracer = AsyncTracer(
                sink=JsonlFileSink(self.path),
                service="test",
                guards=[guard],
                sampling_rate=0.0,
            )
            async with tracer.trace("agent.run") as span:
                span.event("tool.search", data={"q": "a"})
                span.event("tool.search", data={"q": "a"})
                with self.assertRaises(LoopDetected):
                    span.event("tool.search", data={"q": "a"})

        asyncio.run(run())

        # No events emitted to sink (sampled out)
        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        self.assertEqual(len(events), 0)

    def test_metadata_attached_to_events(self):
        """metadata dict should appear on every emitted event."""
        async def run():
            tracer = AsyncTracer(
                sink=JsonlFileSink(self.path),
                service="test",
                metadata={"env": "test", "git_sha": "abc123"},
            )
            async with tracer.trace("agent.run") as span:
                span.event("step")

        asyncio.run(run())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        # All non-watermark events should have metadata
        for event in events:
            self.assertIn("metadata", event)
            self.assertEqual(event["metadata"]["env"], "test")
            self.assertEqual(event["metadata"]["git_sha"], "abc123")

    def test_watermark_emitted_once(self):
        """Watermark event should be emitted exactly once."""
        async def run():
            tracer = AsyncTracer(
                sink=JsonlFileSink(self.path),
                service="test",
                watermark=True,
            )
            async with tracer.trace("agent.run") as span:
                span.event("step1")
                span.event("step2")

        asyncio.run(run())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        watermarks = [e for e in events if e.get("name") == "watermark"]
        self.assertEqual(len(watermarks), 1)
        self.assertIn("AgentGuard", watermarks[0]["message"])

    def test_watermark_disabled(self):
        """watermark=False should suppress the watermark event."""
        async def run():
            tracer = AsyncTracer(
                sink=JsonlFileSink(self.path),
                service="test",
                watermark=False,
            )
            async with tracer.trace("agent.run") as span:
                span.event("step")

        asyncio.run(run())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        watermarks = [e for e in events if e.get("name") == "watermark"]
        self.assertEqual(len(watermarks), 0)


class TestAsyncTracerRepr(unittest.TestCase):
    def test_repr(self):
        tracer = AsyncTracer(service="my-agent")
        self.assertIn("AsyncTracer", repr(tracer))
        self.assertIn("my-agent", repr(tracer))


class TestAsyncTraceAgent(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        os.close(self.fd)

    def tearDown(self):
        os.unlink(self.path)

    def test_wraps_async_function(self):
        tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")

        @async_trace_agent(tracer)
        async def my_agent(x):
            return x + 1

        result = asyncio.run(my_agent(5))
        self.assertEqual(result, 6)

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("agent.my_agent", names)

    def test_custom_name(self):
        tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")

        @async_trace_agent(tracer, name="custom.agent")
        async def do_stuff():
            return "done"

        asyncio.run(do_stuff())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("custom.agent", names)

    def test_preserves_exceptions(self):
        tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")

        @async_trace_agent(tracer)
        async def failing():
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            asyncio.run(failing())


class TestAsyncTraceTool(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        os.close(self.fd)

    def tearDown(self):
        os.unlink(self.path)

    def test_wraps_async_tool(self):
        tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")

        @async_trace_tool(tracer)
        async def search(query):
            return f"results for {query}"

        result = asyncio.run(search("hello"))
        self.assertEqual(result, "results for hello")

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("tool.search", names)

    def test_emits_tool_result(self):
        tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")

        @async_trace_tool(tracer)
        async def lookup(key):
            return "value"

        asyncio.run(lookup("k"))

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        result_events = [e for e in events if e.get("name") == "tool.result"]
        self.assertTrue(len(result_events) > 0)


class TestPatchOpenAIAsync(unittest.TestCase):
    def setUp(self):
        _originals.clear()
        mod = types.ModuleType("openai")

        class _Completions:
            async def create(self, **kwargs):
                resp = MagicMock()
                resp.usage.prompt_tokens = 10
                resp.usage.completion_tokens = 20
                resp.usage.total_tokens = 30
                return resp

        class _Chat:
            def __init__(self):
                self.completions = _Completions()

        class AsyncOpenAI:
            def __init__(self, **kwargs):
                self.chat = _Chat()

        mod.AsyncOpenAI = AsyncOpenAI
        self.fake_mod = mod
        sys.modules["openai"] = mod

    def tearDown(self):
        unpatch_openai_async()
        _originals.clear()
        sys.modules.pop("openai", None)

    def test_patch_traces_async_create(self):
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        tracer = AsyncTracer(sink=CaptureSink(), service="test")
        patch_openai_async(tracer)

        async def run():
            client = self.fake_mod.AsyncOpenAI()
            return await client.chat.completions.create(model="gpt-4o")

        result = asyncio.run(run())
        self.assertIsNotNone(result)
        names = [e["name"] for e in captured]
        self.assertTrue(any("llm.openai.gpt-4o" in n for n in names))

    def test_unpatch_restores(self):
        original_init = self.fake_mod.AsyncOpenAI.__init__
        tracer = MagicMock()
        tracer.trace = MagicMock()
        patch_openai_async(tracer)
        self.assertNotEqual(self.fake_mod.AsyncOpenAI.__init__, original_init)
        unpatch_openai_async()
        self.assertEqual(self.fake_mod.AsyncOpenAI.__init__, original_init)


class TestPatchAnthropicAsync(unittest.TestCase):
    def setUp(self):
        _originals.clear()
        mod = types.ModuleType("anthropic")

        class _Messages:
            async def create(self, **kwargs):
                resp = MagicMock()
                resp.usage.input_tokens = 100
                resp.usage.output_tokens = 50
                return resp

        class AsyncAnthropic:
            def __init__(self, **kwargs):
                self.messages = _Messages()

        mod.AsyncAnthropic = AsyncAnthropic
        self.fake_mod = mod
        sys.modules["anthropic"] = mod

    def tearDown(self):
        unpatch_anthropic_async()
        _originals.clear()
        sys.modules.pop("anthropic", None)

    def test_patch_traces_async_create(self):
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        tracer = AsyncTracer(sink=CaptureSink(), service="test")
        patch_anthropic_async(tracer)

        async def run():
            client = self.fake_mod.AsyncAnthropic()
            return await client.messages.create(model="claude-3-5-sonnet-20241022")

        result = asyncio.run(run())
        self.assertIsNotNone(result)
        names = [e["name"] for e in captured]
        self.assertTrue(any("llm.anthropic" in n for n in names))


class TestAsyncExports(unittest.TestCase):
    def test_all_async_exports(self):
        import agentguard

        for name in [
            "AsyncTracer", "AsyncTraceContext",
            "async_trace_agent", "async_trace_tool",
            "patch_openai_async", "patch_anthropic_async",
            "unpatch_openai_async", "unpatch_anthropic_async",
        ]:
            self.assertTrue(
                hasattr(agentguard, name),
                f"{name} not exported from agentguard",
            )


if __name__ == "__main__":
    unittest.main()
