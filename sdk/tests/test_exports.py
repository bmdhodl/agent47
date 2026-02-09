"""Test that all public API is importable from top-level agentguard package."""
import unittest


class TestTopLevelExports(unittest.TestCase):
    def test_tracer(self):
        from agentguard import Tracer
        self.assertIsNotNone(Tracer)

    def test_jsonl_file_sink(self):
        from agentguard import JsonlFileSink
        self.assertIsNotNone(JsonlFileSink)

    def test_stdout_sink(self):
        from agentguard import StdoutSink
        self.assertIsNotNone(StdoutSink)

    def test_trace_sink(self):
        from agentguard import TraceSink
        self.assertIsNotNone(TraceSink)

    def test_guards(self):
        from agentguard import LoopGuard, BudgetGuard, TimeoutGuard
        self.assertIsNotNone(LoopGuard)
        self.assertIsNotNone(BudgetGuard)
        self.assertIsNotNone(TimeoutGuard)

    def test_exceptions(self):
        from agentguard import LoopDetected, BudgetExceeded, TimeoutExceeded
        self.assertTrue(issubclass(LoopDetected, RuntimeError))
        self.assertTrue(issubclass(BudgetExceeded, RuntimeError))
        self.assertTrue(issubclass(TimeoutExceeded, RuntimeError))

    def test_cost(self):
        from agentguard import CostTracker, estimate_cost, update_prices
        self.assertIsNotNone(CostTracker)
        self.assertIsNotNone(estimate_cost)
        self.assertIsNotNone(update_prices)

    def test_recording(self):
        from agentguard import Recorder, Replayer
        self.assertIsNotNone(Recorder)
        self.assertIsNotNone(Replayer)

    def test_http_sink(self):
        from agentguard import HttpSink
        self.assertIsNotNone(HttpSink)

    def test_evaluation(self):
        from agentguard import EvalSuite, EvalResult, AssertionResult
        self.assertIsNotNone(EvalSuite)
        self.assertIsNotNone(EvalResult)
        self.assertIsNotNone(AssertionResult)

    def test_instrument_decorators(self):
        from agentguard import trace_agent, trace_tool
        self.assertIsNotNone(trace_agent)
        self.assertIsNotNone(trace_tool)

    def test_instrument_patches(self):
        from agentguard import patch_openai, patch_anthropic
        self.assertIsNotNone(patch_openai)
        self.assertIsNotNone(patch_anthropic)

    def test_instrument_unpatches(self):
        from agentguard import unpatch_openai, unpatch_anthropic
        self.assertIsNotNone(unpatch_openai)
        self.assertIsNotNone(unpatch_anthropic)

    def test_all_list_complete(self):
        import agentguard
        expected = {
            "Tracer", "JsonlFileSink", "StdoutSink", "TraceSink",
            "BaseGuard", "LoopGuard", "BudgetGuard", "TimeoutGuard",
            "FuzzyLoopGuard", "RateLimitGuard",
            "LoopDetected", "BudgetExceeded", "BudgetWarning", "TimeoutExceeded",
            "CostTracker", "estimate_cost", "update_prices",
            "Recorder", "Replayer", "HttpSink",
            "EvalSuite", "EvalResult", "AssertionResult", "summarize_trace",
            "trace_agent", "trace_tool",
            "patch_openai", "patch_anthropic",
            "unpatch_openai", "unpatch_anthropic",
            "AsyncTracer", "AsyncTraceContext",
            "async_trace_agent", "async_trace_tool",
            "patch_openai_async", "patch_anthropic_async",
            "unpatch_openai_async", "unpatch_anthropic_async",
        }
        self.assertEqual(set(agentguard.__all__), expected)


if __name__ == "__main__":
    unittest.main()
