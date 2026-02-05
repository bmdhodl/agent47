import json
import os
import tempfile
import unittest
import uuid

from agentguard.guards import BudgetGuard, LoopDetected, LoopGuard
from agentguard.tracing import JsonlFileSink, Tracer
from agentguard.integrations.langchain import AgentGuardCallbackHandler


class TestLangChainIntegration(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._trace_path = os.path.join(self._tmpdir, "traces.jsonl")
        self.sink = JsonlFileSink(self._trace_path)
        self.tracer = Tracer(sink=self.sink, service="test")

    def _read_events(self):
        with open(self._trace_path, "r") as f:
            return [json.loads(line) for line in f if line.strip()]

    def test_chain_lifecycle(self):
        handler = AgentGuardCallbackHandler(tracer=self.tracer)
        rid = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {"input": "hello"}, run_id=rid)
        handler.on_chain_end({"output": "world"}, run_id=rid)

        events = self._read_events()
        names = [e["name"] for e in events]
        self.assertIn("chain.agent", names)
        kinds = [e["kind"] for e in events]
        self.assertIn("span", kinds)
        self.assertIn("event", kinds)

    def test_nested_llm_creates_span(self):
        handler = AgentGuardCallbackHandler(tracer=self.tracer)
        chain_id = uuid.uuid4()
        llm_id = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        handler.on_llm_end(_MockResponse(), run_id=llm_id)
        handler.on_chain_end({}, run_id=chain_id)

        events = self._read_events()
        llm_events = [e for e in events if "llm" in e["name"]]
        self.assertTrue(len(llm_events) >= 2)  # span start + event + span end

    def test_tool_with_loop_guard(self):
        guard = LoopGuard(max_repeats=2, window=3)
        handler = AgentGuardCallbackHandler(
            tracer=self.tracer, loop_guard=guard
        )
        chain_id = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)

        handler.on_tool_start({"name": "search"}, "query1", run_id=uuid.uuid4())
        handler.on_tool_end("result1", run_id=uuid.uuid4())

        with self.assertRaises(LoopDetected):
            handler.on_tool_start({"name": "search"}, "query1", run_id=uuid.uuid4())

    def test_budget_guard_on_llm_end(self):
        guard = BudgetGuard(max_tokens=100)
        handler = AgentGuardCallbackHandler(
            tracer=self.tracer, budget_guard=guard
        )
        chain_id = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)

        llm_id = uuid.uuid4()
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        handler.on_llm_end(_MockResponse(tokens=80), run_id=llm_id)

        self.assertEqual(guard.state.tokens_used, 80)

    def test_tool_with_budget_guard(self):
        guard = BudgetGuard(max_calls=2)
        handler = AgentGuardCallbackHandler(
            tracer=self.tracer, budget_guard=guard
        )
        chain_id = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)

        handler.on_tool_start({"name": "search"}, "q1", run_id=uuid.uuid4())
        handler.on_tool_end("r1", run_id=uuid.uuid4())

        handler.on_tool_start({"name": "calc"}, "1+1", run_id=uuid.uuid4())
        handler.on_tool_end("2", run_id=uuid.uuid4())

        self.assertEqual(guard.state.calls_used, 2)


class _MockResponse:
    """Minimal mock for LangChain LLMResult."""

    def __init__(self, tokens: int = 0):
        self.llm_output = {
            "token_usage": {"total_tokens": tokens, "prompt_tokens": 0, "completion_tokens": tokens}
        } if tokens else {}

    def dict(self):
        return {"generations": [], "llm_output": self.llm_output}


if __name__ == "__main__":
    unittest.main()
