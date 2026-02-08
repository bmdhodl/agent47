"""Tests for patch_openai / patch_anthropic with mocked modern SDK clients."""
import sys
import types
import unittest
from unittest.mock import MagicMock

from agentguard.instrument import (
    _originals,
    patch_openai,
    patch_anthropic,
    unpatch_openai,
    unpatch_anthropic,
)


def _make_fake_openai_module():
    """Create a fake openai module that mimics openai >= 1.0."""
    mod = types.ModuleType("openai")

    class _Completions:
        def create(self, **kwargs):
            resp = MagicMock()
            resp.usage.prompt_tokens = 10
            resp.usage.completion_tokens = 20
            resp.usage.total_tokens = 30
            return resp

    class _Chat:
        def __init__(self):
            self.completions = _Completions()

    class OpenAI:
        def __init__(self, **kwargs):
            self.chat = _Chat()

    mod.OpenAI = OpenAI
    return mod


def _make_fake_anthropic_module():
    """Create a fake anthropic module that mimics the Anthropic SDK."""
    mod = types.ModuleType("anthropic")

    class _Messages:
        def create(self, **kwargs):
            resp = MagicMock()
            resp.usage.input_tokens = 100
            resp.usage.output_tokens = 50
            return resp

    class Anthropic:
        def __init__(self, **kwargs):
            self.messages = _Messages()

    mod.Anthropic = Anthropic
    return mod


class TestPatchOpenAIModern(unittest.TestCase):
    def setUp(self):
        _originals.clear()
        self.fake_mod = _make_fake_openai_module()
        sys.modules["openai"] = self.fake_mod

    def tearDown(self):
        unpatch_openai()
        _originals.clear()
        sys.modules.pop("openai", None)

    def test_patch_traces_create_call(self):
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        from agentguard.tracing import Tracer

        tracer = Tracer(sink=CaptureSink(), service="test")
        patch_openai(tracer)

        client = self.fake_mod.OpenAI()
        client.chat.completions.create(model="gpt-4o")

        # Should have trace events: span start, llm.result event, span end
        names = [e["name"] for e in captured]
        self.assertTrue(any("llm.openai.gpt-4o" in n for n in names))

    def test_patch_is_idempotent(self):
        tracer = MagicMock()
        tracer.trace = MagicMock()
        patch_openai(tracer)
        patch_openai(tracer)  # second call should be no-op
        self.assertIn("openai_init", _originals)

    def test_unpatch_restores_original(self):
        original_init = self.fake_mod.OpenAI.__init__
        tracer = MagicMock()
        tracer.trace = MagicMock()
        patch_openai(tracer)
        self.assertNotEqual(self.fake_mod.OpenAI.__init__, original_init)
        unpatch_openai()
        # After unpatch, __init__ should be restored
        self.assertEqual(self.fake_mod.OpenAI.__init__, original_init)

    def test_create_returns_result(self):
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        from agentguard.tracing import Tracer

        tracer = Tracer(sink=CaptureSink(), service="test")
        patch_openai(tracer)

        client = self.fake_mod.OpenAI()
        result = client.chat.completions.create(model="gpt-4o")
        # Should return the mock result (not None)
        self.assertIsNotNone(result)
        self.assertEqual(result.usage.prompt_tokens, 10)


class TestPatchAnthropicModern(unittest.TestCase):
    def setUp(self):
        _originals.clear()
        self.fake_mod = _make_fake_anthropic_module()
        sys.modules["anthropic"] = self.fake_mod

    def tearDown(self):
        unpatch_anthropic()
        _originals.clear()
        sys.modules.pop("anthropic", None)

    def test_patch_traces_create_call(self):
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        from agentguard.tracing import Tracer

        tracer = Tracer(sink=CaptureSink(), service="test")
        patch_anthropic(tracer)

        client = self.fake_mod.Anthropic()
        client.messages.create(model="claude-3-5-sonnet-20241022")

        names = [e["name"] for e in captured]
        self.assertTrue(
            any("llm.anthropic.claude-3-5-sonnet-20241022" in n for n in names)
        )

    def test_patch_is_idempotent(self):
        tracer = MagicMock()
        tracer.trace = MagicMock()
        patch_anthropic(tracer)
        patch_anthropic(tracer)
        self.assertIn("anthropic_init", _originals)

    def test_unpatch_restores_original(self):
        original_init = self.fake_mod.Anthropic.__init__
        tracer = MagicMock()
        tracer.trace = MagicMock()
        patch_anthropic(tracer)
        self.assertNotEqual(self.fake_mod.Anthropic.__init__, original_init)
        unpatch_anthropic()
        self.assertEqual(self.fake_mod.Anthropic.__init__, original_init)

    def test_create_returns_result(self):
        captured = []

        class CaptureSink:
            def emit(self, event):
                captured.append(event)

        from agentguard.tracing import Tracer

        tracer = Tracer(sink=CaptureSink(), service="test")
        patch_anthropic(tracer)

        client = self.fake_mod.Anthropic()
        result = client.messages.create(model="claude-3-5-sonnet-20241022")
        self.assertIsNotNone(result)
        self.assertEqual(result.usage.input_tokens, 100)


class TestUnpatchSafeWhenNotPatched(unittest.TestCase):
    def setUp(self):
        _originals.clear()

    def test_unpatch_openai_safe(self):
        unpatch_openai()  # should not raise

    def test_unpatch_anthropic_safe(self):
        unpatch_anthropic()  # should not raise


if __name__ == "__main__":
    unittest.main()
