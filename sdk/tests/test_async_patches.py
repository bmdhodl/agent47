"""Tests for async patch/unpatch: patch_openai_async, patch_anthropic_async."""
import sys
import types
import unittest
from unittest.mock import MagicMock

from agentguard.instrument import (
    _originals,
    patch_anthropic_async,
    patch_openai_async,
    unpatch_anthropic_async,
    unpatch_openai_async,
)


def _make_mock_openai_module():
    """Create a fake openai module with AsyncOpenAI class."""
    mod = types.ModuleType("openai")

    class AsyncOpenAI:
        def __init__(self, **kwargs):
            self.chat = MagicMock()
            self.chat.completions = MagicMock()
            self.chat.completions.create = MagicMock()

    mod.AsyncOpenAI = AsyncOpenAI
    return mod


def _make_mock_anthropic_module():
    """Create a fake anthropic module with AsyncAnthropic class."""
    mod = types.ModuleType("anthropic")

    class AsyncAnthropic:
        def __init__(self, **kwargs):
            self.messages = MagicMock()
            self.messages.create = MagicMock()

    mod.AsyncAnthropic = AsyncAnthropic
    return mod


class TestPatchOpenaiAsync(unittest.TestCase):
    def setUp(self):
        # Clean up any previous patches
        for key in list(_originals.keys()):
            if "openai_async" in key:
                del _originals[key]

    def tearDown(self):
        # Restore module
        if "_mock_openai" in dir(self):
            sys.modules.pop("openai", None)
        # Clean up originals
        for key in list(_originals.keys()):
            if "openai_async" in key:
                del _originals[key]

    def test_patch_wraps_init(self):
        mock_mod = _make_mock_openai_module()
        original_init = mock_mod.AsyncOpenAI.__init__
        sys.modules["openai"] = mock_mod

        tracer = MagicMock()
        tracer.trace = MagicMock()
        patch_openai_async(tracer)

        # __init__ should be wrapped
        self.assertNotEqual(mock_mod.AsyncOpenAI.__init__, original_init)
        self.assertIn("openai_async_init", _originals)

        sys.modules.pop("openai", None)

    def test_unpatch_restores_init(self):
        mock_mod = _make_mock_openai_module()
        original_init = mock_mod.AsyncOpenAI.__init__
        sys.modules["openai"] = mock_mod

        tracer = MagicMock()
        patch_openai_async(tracer)
        self.assertNotEqual(mock_mod.AsyncOpenAI.__init__, original_init)

        unpatch_openai_async()
        self.assertEqual(mock_mod.AsyncOpenAI.__init__, original_init)
        self.assertNotIn("openai_async_init", _originals)

        sys.modules.pop("openai", None)

    def test_double_patch_is_idempotent(self):
        mock_mod = _make_mock_openai_module()
        sys.modules["openai"] = mock_mod

        tracer = MagicMock()
        patch_openai_async(tracer)
        first_patched = mock_mod.AsyncOpenAI.__init__

        patch_openai_async(tracer)
        second_patched = mock_mod.AsyncOpenAI.__init__

        # Should be the same wrapped function
        self.assertEqual(first_patched, second_patched)

        sys.modules.pop("openai", None)

    def test_patch_no_openai_installed(self):
        # Remove openai from sys.modules
        saved = sys.modules.pop("openai", None)
        try:
            tracer = MagicMock()
            # Should not raise
            patch_openai_async(tracer)
        finally:
            if saved:
                sys.modules["openai"] = saved

    def test_unpatch_without_patch(self):
        # Should not raise
        unpatch_openai_async()


class TestPatchAnthropicAsync(unittest.TestCase):
    def setUp(self):
        for key in list(_originals.keys()):
            if "anthropic_async" in key:
                del _originals[key]

    def tearDown(self):
        sys.modules.pop("anthropic", None)
        for key in list(_originals.keys()):
            if "anthropic_async" in key:
                del _originals[key]

    def test_patch_wraps_init(self):
        mock_mod = _make_mock_anthropic_module()
        original_init = mock_mod.AsyncAnthropic.__init__
        sys.modules["anthropic"] = mock_mod

        tracer = MagicMock()
        patch_anthropic_async(tracer)

        self.assertNotEqual(mock_mod.AsyncAnthropic.__init__, original_init)
        self.assertIn("anthropic_async_init", _originals)

        sys.modules.pop("anthropic", None)

    def test_unpatch_restores_init(self):
        mock_mod = _make_mock_anthropic_module()
        original_init = mock_mod.AsyncAnthropic.__init__
        sys.modules["anthropic"] = mock_mod

        tracer = MagicMock()
        patch_anthropic_async(tracer)
        unpatch_anthropic_async()

        self.assertEqual(mock_mod.AsyncAnthropic.__init__, original_init)

        sys.modules.pop("anthropic", None)

    def test_double_patch_is_idempotent(self):
        mock_mod = _make_mock_anthropic_module()
        sys.modules["anthropic"] = mock_mod

        tracer = MagicMock()
        patch_anthropic_async(tracer)
        first_patched = mock_mod.AsyncAnthropic.__init__

        patch_anthropic_async(tracer)
        second_patched = mock_mod.AsyncAnthropic.__init__

        self.assertEqual(first_patched, second_patched)

        sys.modules.pop("anthropic", None)

    def test_patch_no_anthropic_installed(self):
        saved = sys.modules.pop("anthropic", None)
        try:
            tracer = MagicMock()
            patch_anthropic_async(tracer)
        finally:
            if saved:
                sys.modules["anthropic"] = saved

    def test_unpatch_without_patch(self):
        unpatch_anthropic_async()


if __name__ == "__main__":
    unittest.main()
