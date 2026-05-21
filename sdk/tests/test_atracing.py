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
    JsonlFileSink,
    LoopDetected,
    LoopGuard,
    Tracer,
)
from agentguard.instrument import (
    _originals,
    async_trace_agent,
    async_trace_tool,
    patch_anthropic_async,
    patch_openai_async,
    unpatch_anthropic_async,
    unpatch_openai_async,
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
            async with tracer.trace("agent.run") as span, span.span("tool.search") as child:
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
                async with tracer.trace("agent.run"):
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

    def test_session_id_emitted(self):
        async def run():
            tracer = AsyncTracer(
                sink=JsonlFileSink(self.path),
                service="test",
                session_id="session-123",
            )
            async with tracer.trace("agent.run") as span:
                span.event("reasoning.step", data={"step": 1})

        asyncio.run(run())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        trace_events = [event for event in events if event.get("kind") in {"span", "event"}]
        self.assertTrue(trace_events)
        self.assertTrue(all(event["session_id"] == "session-123" for event in trace_events))


class TestAsyncTracerRepr(unittest.TestCase):
    def test_repr(self):
        tracer = AsyncTracer(service="my-agent")
        self.assertIn("AsyncTracer", repr(tracer))
        self.assertIn("my-agent", repr(tracer))

    def test_repr_includes_session_id_when_set(self):
        tracer = AsyncTracer(service="my-agent", session_id="session-123")
        self.assertEqual(
            repr(tracer),
            "AsyncTracer(service='my-agent', session_id='session-123', sink=StdoutSink())",
        )

    def test_service_is_truncated_like_sync_tracer(self):
        tracer = AsyncTracer(service="x" * 1205)
        self.assertEqual(len(tracer._service), 1000)


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
        self.assertEqual(result_events[0]["data"]["tool_name"], "lookup")

    def test_emits_tool_error_and_reraises(self):
        tracer = AsyncTracer(sink=JsonlFileSink(self.path), service="test")

        @async_trace_tool(tracer)
        async def flaky():
            raise RuntimeError("boom")

        with self.assertRaises(RuntimeError):
            asyncio.run(flaky())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        error_events = [e for e in events if e.get("name") == "tool.error"]
        self.assertTrue(len(error_events) > 0)
        self.assertEqual(error_events[0]["data"]["tool_name"], "flaky")


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


class TestAsyncDecoratorsWithSyncTracer(unittest.TestCase):
    """Async decorators must accept a sync Tracer, not only an AsyncTracer.

    A sync Tracer is the documented default tracer. Applying an async
    decorator while a sync Tracer is configured is a normal usage
    combination and must not raise.
    """

    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        os.close(self.fd)

    def tearDown(self):
        os.unlink(self.path)

    def test_async_trace_agent_works_with_sync_tracer(self):
        tracer = Tracer(sink=JsonlFileSink(self.path), service="test")

        @async_trace_agent(tracer)
        async def my_agent(x):
            return x + 1

        result = asyncio.run(my_agent(5))
        self.assertEqual(result, 6)

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("agent.my_agent", names)

    def test_async_trace_tool_works_with_sync_tracer(self):
        tracer = Tracer(sink=JsonlFileSink(self.path), service="test")

        @async_trace_tool(tracer)
        async def search(query):
            return f"results for {query}"

        result = asyncio.run(search("hello"))
        self.assertEqual(result, "results for hello")

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        names = [e["name"] for e in events]
        self.assertIn("tool.search", names)
        self.assertIn("tool.result", names)

    def test_async_trace_agent_sync_tracer_preserves_exceptions(self):
        tracer = Tracer(sink=JsonlFileSink(self.path), service="test")

        @async_trace_agent(tracer)
        async def failing():
            raise ValueError("boom")

        with self.assertRaises(ValueError):
            asyncio.run(failing())

        with open(self.path) as f:
            events = [json.loads(line) for line in f if line.strip()]
        end_events = [e for e in events if e.get("phase") == "end"]
        self.assertTrue(end_events)
        self.assertEqual(end_events[-1]["error"]["type"], "ValueError")


class TestSyncAsyncTracerParity(unittest.TestCase):
    """AsyncTracer must produce the same event shape as the sync Tracer.

    Observable behavior must not depend on which tracer the caller picked.
    """

    def setUp(self):
        self.fd_sync, self.path_sync = tempfile.mkstemp(suffix=".jsonl")
        os.close(self.fd_sync)
        self.fd_async, self.path_async = tempfile.mkstemp(suffix=".jsonl")
        os.close(self.fd_async)

    def tearDown(self):
        os.unlink(self.path_sync)
        os.unlink(self.path_async)

    def _sync_event(self, name, data):
        tracer = Tracer(
            sink=JsonlFileSink(self.path_sync), service="test", watermark=False
        )
        with tracer.trace("agent.run") as span:
            span.event(name, data=data)
        with open(self.path_sync) as f:
            events = [json.loads(line) for line in f if line.strip()]
        return next(e for e in events if e["name"] == name)

    def _async_event(self, name, data):
        async def run():
            tracer = AsyncTracer(sink=JsonlFileSink(self.path_async), service="test")
            async with tracer.trace("agent.run") as span:
                span.event(name, data=data)

        asyncio.run(run())
        with open(self.path_async) as f:
            events = [json.loads(line) for line in f if line.strip()]
        return next(e for e in events if e["name"] == name)

    def test_oversized_event_data_truncated_like_sync(self):
        """A 100 KB payload must be truncated to <=64 KB on both paths."""
        big_payload = {"blob": "x" * 100_000}
        sync_event = self._sync_event("big", big_payload)
        async_event = self._async_event("big", big_payload)

        sync_size = len(json.dumps(sync_event["data"]).encode("utf-8"))
        async_size = len(json.dumps(async_event["data"]).encode("utf-8"))

        # Sync truncates to the 64 KB limit; async must do the same.
        self.assertLessEqual(sync_size, 65_536)
        self.assertLessEqual(
            async_size,
            65_536,
            "AsyncTracer did not truncate oversized event data like the "
            "sync Tracer does",
        )

    def test_long_event_name_truncated_like_sync(self):
        """An over-length event name must be truncated on both paths."""
        long_name = "n" * 5000

        # The name is truncated, so look the event up by kind, not name.
        tracer = Tracer(
            sink=JsonlFileSink(self.path_sync), service="test", watermark=False
        )
        with tracer.trace("agent.run") as span:
            span.event(long_name, data={"k": "v"})
        with open(self.path_sync) as f:
            sync_events = [json.loads(line) for line in f if line.strip()]
        sync_event = next(e for e in sync_events if e["kind"] == "event")

        async def run():
            atracer = AsyncTracer(
                sink=JsonlFileSink(self.path_async), service="test"
            )
            async with atracer.trace("agent.run") as span:
                span.event(long_name, data={"k": "v"})

        asyncio.run(run())
        with open(self.path_async) as f:
            async_events = [json.loads(line) for line in f if line.strip()]
        async_event = next(e for e in async_events if e["kind"] == "event")

        self.assertEqual(
            async_event["name"],
            sync_event["name"],
            "AsyncTracer did not truncate the event name like the sync "
            "Tracer does",
        )

    def test_non_serializable_event_data_coerced_like_sync(self):
        """Non-JSON values must be coerced identically on both paths."""

        class Widget:
            pass

        payload = {"widget": Widget()}
        sync_event = self._sync_event("w", payload)
        async_event = self._async_event("w", payload)

        # Sync coerces unknown objects to a marker dict; async must match.
        self.assertEqual(async_event["data"], sync_event["data"])


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
