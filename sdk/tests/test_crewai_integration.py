"""Tests for CrewAI integration (AgentGuardCrewHandler)."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from types import SimpleNamespace

from agentguard import Tracer, JsonlFileSink, LoopGuard, BudgetGuard
from agentguard.guards import LoopDetected, BudgetExceeded
from agentguard.integrations.crewai import AgentGuardCrewHandler


class TestCrewHandler(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.mkdtemp()
        self._trace_path = os.path.join(self._tmpdir, "traces.jsonl")
        self.sink = JsonlFileSink(self._trace_path)
        self.tracer = Tracer(sink=self.sink, service="test-crewai")

    def _read_events(self):
        with open(self._trace_path, "r") as f:
            return [json.loads(line) for line in f if line.strip()]

    def test_step_callback_with_tool(self):
        """step_callback records a tool step."""
        handler = AgentGuardCrewHandler(tracer=self.tracer)

        step = SimpleNamespace(
            tool="search_web",
            tool_input="python agents",
            result="Found 10 results",
        )
        handler.step_callback(step)

        events = self._read_events()
        names = [e["name"] for e in events]
        self.assertIn("step.search_web", names)

    def test_step_callback_without_tool(self):
        """step_callback without tool records a thought step."""
        handler = AgentGuardCrewHandler(tracer=self.tracer)

        step = SimpleNamespace(output="I should search for info")
        handler.step_callback(step)

        events = self._read_events()
        names = [e["name"] for e in events]
        self.assertIn("step.thought", names)

    def test_step_callback_dict_input(self):
        """step_callback handles dict-style step output."""
        handler = AgentGuardCrewHandler(tracer=self.tracer)

        step = {"tool": "calculator", "tool_input": "2+2", "result": "4"}
        handler.step_callback(step)

        events = self._read_events()
        names = [e["name"] for e in events]
        self.assertIn("step.calculator", names)

    def test_task_callback(self):
        """task_callback records a task completion."""
        handler = AgentGuardCrewHandler(tracer=self.tracer)

        task_output = SimpleNamespace(
            description="Research AI agents",
            raw="Found comprehensive info on AI agents",
        )
        handler.task_callback(task_output)

        events = self._read_events()
        names = [e["name"] for e in events]
        self.assertIn("task.complete", names)

    def test_task_callback_dict(self):
        """task_callback handles dict-style output."""
        handler = AgentGuardCrewHandler(tracer=self.tracer)

        handler.task_callback({
            "description": "Analyze data",
            "raw": "Analysis complete",
        })

        events = self._read_events()
        names = [e["name"] for e in events]
        self.assertIn("task.complete", names)

    def test_crew_callback(self):
        """crew_callback records crew completion."""
        handler = AgentGuardCrewHandler(tracer=self.tracer)

        crew_output = SimpleNamespace(
            raw="Final crew output",
            tasks_output=[
                SimpleNamespace(raw="task1"),
                SimpleNamespace(raw="task2"),
            ],
        )
        handler.crew_callback(crew_output)

        events = self._read_events()
        names = [e["name"] for e in events]
        self.assertIn("crew.complete", names)
        # Check task_count in data
        start_events = [e for e in events if e.get("phase") == "start"]
        self.assertTrue(any(e.get("data", {}).get("task_count") == 2 for e in start_events))

    def test_loop_guard_fires(self):
        """LoopGuard raises on repeated identical tool calls."""
        handler = AgentGuardCrewHandler(
            tracer=self.tracer,
            loop_guard=LoopGuard(max_repeats=3),
        )

        step = SimpleNamespace(tool="search", tool_input="same query")
        handler.step_callback(step)
        handler.step_callback(step)

        # Third identical call triggers max_repeats=3
        with self.assertRaises(LoopDetected):
            handler.step_callback(step)

    def test_budget_guard_fires(self):
        """BudgetGuard raises after call limit."""
        handler = AgentGuardCrewHandler(
            tracer=self.tracer,
            budget_guard=BudgetGuard(max_calls=2),
        )

        step = SimpleNamespace(tool="api_call", tool_input="data")
        handler.step_callback(step)
        handler.step_callback(SimpleNamespace(tool="other_call", tool_input="x"))

        with self.assertRaises(BudgetExceeded):
            handler.step_callback(SimpleNamespace(tool="third_call", tool_input="y"))

    def test_default_tracer(self):
        """Works without explicit tracer."""
        handler = AgentGuardCrewHandler()

        step = SimpleNamespace(tool="test", tool_input="x", result="y")
        handler.step_callback(step)  # Should not raise

    def test_step_truncates_long_input(self):
        """Long tool inputs are truncated in trace data."""
        handler = AgentGuardCrewHandler(tracer=self.tracer)

        long_input = "x" * 1000
        step = SimpleNamespace(tool="search", tool_input=long_input, result="ok")
        handler.step_callback(step)

        events = self._read_events()
        start_events = [e for e in events if e.get("phase") == "start"]
        for e in start_events:
            data = e.get("data", {})
            if "input" in data:
                self.assertLessEqual(len(data["input"]), 500)


if __name__ == "__main__":
    unittest.main()
