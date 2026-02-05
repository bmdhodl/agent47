import json
import os
import tempfile
import unittest

from agentguard.evaluation import AssertionResult, EvalResult, EvalSuite


def _write_trace(events):
    """Write events to a temp JSONL file and return the path."""
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w") as f:
        for e in events:
            f.write(json.dumps(e) + "\n")
    return path


class TestEvalSuiteNoLoops(unittest.TestCase):
    def test_passes_when_no_loops(self):
        path = _write_trace([
            {"name": "agent.run", "kind": "span", "phase": "start"},
            {"name": "reasoning.step", "kind": "event", "phase": "emit"},
            {"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 50},
        ])
        result = EvalSuite(path).assert_no_loops().run()
        os.unlink(path)
        self.assertTrue(result.passed)

    def test_fails_when_loops_present(self):
        path = _write_trace([
            {"name": "guard.loop_detected", "kind": "event", "phase": "emit"},
        ])
        result = EvalSuite(path).assert_no_loops().run()
        os.unlink(path)
        self.assertFalse(result.passed)


class TestEvalSuiteToolCalled(unittest.TestCase):
    def test_passes_when_tool_called_enough(self):
        path = _write_trace([
            {"name": "tool.search", "kind": "span", "phase": "start"},
            {"name": "tool.search", "kind": "span", "phase": "end"},
            {"name": "tool.search", "kind": "span", "phase": "start"},
            {"name": "tool.search", "kind": "span", "phase": "end"},
        ])
        result = EvalSuite(path).assert_tool_called("search", min_times=2).run()
        os.unlink(path)
        self.assertTrue(result.passed)

    def test_fails_when_tool_not_called_enough(self):
        path = _write_trace([
            {"name": "tool.search", "kind": "span", "phase": "start"},
        ])
        result = EvalSuite(path).assert_tool_called("search", min_times=5).run()
        os.unlink(path)
        self.assertFalse(result.passed)


class TestEvalSuiteBudget(unittest.TestCase):
    def test_passes_under_budget(self):
        path = _write_trace([
            {"name": "llm.call", "kind": "event", "data": {"usage": {"total_tokens": 100}}},
        ])
        result = EvalSuite(path).assert_budget_under(tokens=200).run()
        os.unlink(path)
        self.assertTrue(result.passed)

    def test_fails_over_budget(self):
        path = _write_trace([
            {"name": "llm.call", "kind": "event", "data": {"usage": {"total_tokens": 500}}},
        ])
        result = EvalSuite(path).assert_budget_under(tokens=200).run()
        os.unlink(path)
        self.assertFalse(result.passed)


class TestEvalSuiteCompletesWithin(unittest.TestCase):
    def test_passes_fast_trace(self):
        path = _write_trace([
            {"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 100},
        ])
        result = EvalSuite(path).assert_completes_within(1.0).run()
        os.unlink(path)
        self.assertTrue(result.passed)

    def test_fails_slow_trace(self):
        path = _write_trace([
            {"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 60000},
        ])
        result = EvalSuite(path).assert_completes_within(5.0).run()
        os.unlink(path)
        self.assertFalse(result.passed)


class TestEvalSuiteEventExists(unittest.TestCase):
    def test_passes_when_event_found(self):
        path = _write_trace([
            {"name": "reasoning.step", "kind": "event"},
        ])
        result = EvalSuite(path).assert_event_exists("reasoning.step").run()
        os.unlink(path)
        self.assertTrue(result.passed)

    def test_fails_when_event_missing(self):
        path = _write_trace([
            {"name": "tool.result", "kind": "event"},
        ])
        result = EvalSuite(path).assert_event_exists("reasoning.step").run()
        os.unlink(path)
        self.assertFalse(result.passed)


class TestEvalSuiteNoErrors(unittest.TestCase):
    def test_passes_no_errors(self):
        path = _write_trace([
            {"name": "agent.run", "kind": "span", "error": None},
        ])
        result = EvalSuite(path).assert_no_errors().run()
        os.unlink(path)
        self.assertTrue(result.passed)

    def test_fails_with_errors(self):
        path = _write_trace([
            {"name": "agent.run", "kind": "span", "error": {"type": "RuntimeError", "message": "boom"}},
        ])
        result = EvalSuite(path).assert_no_errors().run()
        os.unlink(path)
        self.assertFalse(result.passed)


class TestEvalSuiteChaining(unittest.TestCase):
    def test_multiple_assertions_chained(self):
        path = _write_trace([
            {"name": "agent.run", "kind": "span", "phase": "start"},
            {"name": "reasoning.step", "kind": "event", "phase": "emit"},
            {"name": "agent.run", "kind": "span", "phase": "end", "duration_ms": 50, "error": None},
        ])
        result = (
            EvalSuite(path)
            .assert_no_loops()
            .assert_no_errors()
            .assert_completes_within(10.0)
            .assert_event_exists("reasoning.step")
            .run()
        )
        os.unlink(path)
        self.assertTrue(result.passed)
        self.assertEqual(len(result.assertions), 4)


class TestEvalSuiteEdgeCases(unittest.TestCase):
    def test_empty_trace(self):
        path = _write_trace([])
        result = EvalSuite(path).assert_no_loops().assert_no_errors().run()
        os.unlink(path)
        self.assertTrue(result.passed)

    def test_malformed_jsonl(self):
        fd, path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(fd, "w") as f:
            f.write("not json\n")
            f.write(json.dumps({"name": "agent.run", "kind": "span"}) + "\n")
            f.write("also {bad\n")
        result = EvalSuite(path).assert_event_exists("agent.run").run()
        os.unlink(path)
        self.assertTrue(result.passed)


class TestEvalResult(unittest.TestCase):
    def test_summary_format(self):
        result = EvalResult(assertions=[
            AssertionResult(name="test1", passed=True, message="ok"),
            AssertionResult(name="test2", passed=False, message="fail"),
        ])
        self.assertFalse(result.passed)
        self.assertIn("1/2 passed", result.summary)
        self.assertIn("[PASS]", result.summary)
        self.assertIn("[FAIL]", result.summary)


if __name__ == "__main__":
    unittest.main()
