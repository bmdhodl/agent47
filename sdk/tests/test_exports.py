"""Test that all public API is importable from top-level agentguard package."""
import importlib
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
        from agentguard import (
            BudgetAwareEscalation,
            BudgetGuard,
            EscalationSignal,
            LoopGuard,
            RetryGuard,
            TimeoutGuard,
        )
        self.assertIsNotNone(LoopGuard)
        self.assertIsNotNone(BudgetGuard)
        self.assertIsNotNone(TimeoutGuard)
        self.assertIsNotNone(RetryGuard)
        self.assertIsNotNone(BudgetAwareEscalation)
        self.assertIsNotNone(EscalationSignal)

    def test_exceptions(self):
        from agentguard import (
            BudgetExceeded,
            EscalationRequired,
            LoopDetected,
            RetryLimitExceeded,
            TimeoutExceeded,
        )
        self.assertTrue(issubclass(LoopDetected, RuntimeError))
        self.assertTrue(issubclass(BudgetExceeded, RuntimeError))
        self.assertTrue(issubclass(TimeoutExceeded, RuntimeError))
        self.assertTrue(issubclass(RetryLimitExceeded, RuntimeError))
        self.assertTrue(issubclass(EscalationRequired, RuntimeError))

    def test_legacy_guard_exports_do_not_create_import_cycle(self):
        escalation_module = importlib.import_module("agentguard.escalation")
        guards_module = importlib.import_module("agentguard.guards")

        self.assertIs(guards_module.BudgetAwareEscalation, escalation_module.BudgetAwareEscalation)
        self.assertIs(guards_module.EscalationSignal, escalation_module.EscalationSignal)
        self.assertIs(guards_module.EscalationRequired, escalation_module.EscalationRequired)

    def test_cost(self):
        from agentguard import estimate_cost
        self.assertIsNotNone(estimate_cost)

    def test_http_sink(self):
        from agentguard import HttpSink
        self.assertIsNotNone(HttpSink)

    def test_evaluation(self):
        from agentguard import AssertionResult, EvalResult, EvalSuite
        self.assertIsNotNone(EvalResult)
        self.assertIsNotNone(EvalSuite)
        self.assertIsNotNone(AssertionResult)

    def test_decision_tracing(self):
        from agentguard import (
            DecisionTrace,
            decision_flow,
            extract_decision_events,
            extract_decision_payload,
            is_decision_event,
            log_decision_approved,
            log_decision_bound,
            log_decision_edited,
            log_decision_overridden,
            log_decision_proposed,
        )
        self.assertIsNotNone(DecisionTrace)
        self.assertIsNotNone(decision_flow)
        self.assertIsNotNone(extract_decision_events)
        self.assertIsNotNone(extract_decision_payload)
        self.assertIsNotNone(is_decision_event)
        self.assertIsNotNone(log_decision_proposed)
        self.assertIsNotNone(log_decision_edited)
        self.assertIsNotNone(log_decision_overridden)
        self.assertIsNotNone(log_decision_approved)
        self.assertIsNotNone(log_decision_bound)

    def test_instrument_decorators(self):
        from agentguard import trace_agent, trace_tool
        self.assertIsNotNone(trace_agent)
        self.assertIsNotNone(trace_tool)

    def test_instrument_patches(self):
        from agentguard import patch_anthropic, patch_openai
        self.assertIsNotNone(patch_openai)
        self.assertIsNotNone(patch_anthropic)

    def test_instrument_unpatches(self):
        from agentguard import unpatch_anthropic, unpatch_openai
        self.assertIsNotNone(unpatch_openai)
        self.assertIsNotNone(unpatch_anthropic)

    def test_all_list_complete(self):
        import agentguard
        expected = {
            "__version__",
            "init", "shutdown", "get_tracer", "get_budget_guard",
            "Tracer", "JsonlFileSink", "StdoutSink", "TraceSink",
            "AgentGuardError",
            "BaseGuard", "LoopGuard", "BudgetGuard", "TimeoutGuard",
            "FuzzyLoopGuard", "RateLimitGuard", "RetryGuard",
            "BudgetAwareEscalation", "EscalationSignal",
            "LoopDetected", "BudgetExceeded", "BudgetWarning", "TimeoutExceeded",
            "RetryLimitExceeded", "EscalationRequired",
            "DecisionTrace", "decision_flow",
            "extract_decision_events", "extract_decision_payload", "is_decision_event",
            "log_decision_proposed", "log_decision_edited",
            "log_decision_overridden", "log_decision_approved",
            "log_decision_bound",
            "estimate_cost",
            "HttpSink",
            "EvalSuite", "EvalResult", "AssertionResult", "summarize_trace",
            "trace_agent", "trace_tool",
            "patch_openai", "patch_anthropic",
            "unpatch_openai", "unpatch_anthropic",
            "AsyncTracer", "AsyncTraceContext",
            "async_trace_agent", "async_trace_tool",
            "patch_openai_async", "patch_anthropic_async",
            "unpatch_openai_async", "unpatch_anthropic_async",
            "InitConfig", "RepoConfig", "ProfileDefaults", "SUPPORTED_PROFILES",
        }
        self.assertEqual(set(agentguard.__all__), expected)


if __name__ == "__main__":
    unittest.main()
