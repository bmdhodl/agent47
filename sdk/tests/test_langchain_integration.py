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

    def test_budget_guard_cost_usd_on_llm_end(self):
        """on_llm_end with a known model should pass cost_usd to BudgetGuard.consume."""
        guard = BudgetGuard(max_cost_usd=1.00)
        handler = AgentGuardCallbackHandler(
            tracer=self.tracer, budget_guard=guard
        )
        chain_id = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)

        llm_id = uuid.uuid4()
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        handler.on_llm_end(
            _MockResponseWithModel(model="gpt-4o", input_t=1000, output_t=500),
            run_id=llm_id,
        )

        self.assertGreater(guard.state.cost_used, 0)

    def test_llm_end_includes_cost_for_known_model(self):
        """on_llm_end with a known model and token usage should include cost_usd."""
        handler = AgentGuardCallbackHandler(tracer=self.tracer)
        chain_id = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)

        llm_id = uuid.uuid4()
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        handler.on_llm_end(
            _MockResponseWithModel(model="gpt-4o", input_t=1000, output_t=500),
            run_id=llm_id,
        )
        handler.on_chain_end({}, run_id=chain_id)

        events = self._read_events()
        llm_end_events = [e for e in events if e["name"] == "llm.end"]
        self.assertTrue(len(llm_end_events) >= 1)
        data = llm_end_events[0].get("data", {})
        self.assertIn("cost_usd", data)
        self.assertGreater(data["cost_usd"], 0)

    def test_llm_end_no_cost_for_unknown_model(self):
        """on_llm_end with an unknown model should not have cost_usd."""
        handler = AgentGuardCallbackHandler(tracer=self.tracer)
        chain_id = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)

        llm_id = uuid.uuid4()
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        handler.on_llm_end(
            _MockResponseWithModel(model="totally-fake-model-xyz", input_t=100, output_t=50),
            run_id=llm_id,
        )
        handler.on_chain_end({}, run_id=chain_id)

        events = self._read_events()
        llm_end_events = [e for e in events if e["name"] == "llm.end"]
        self.assertTrue(len(llm_end_events) >= 1)
        data = llm_end_events[0].get("data", {})
        self.assertNotIn("cost_usd", data)


class TestExtractModelName(unittest.TestCase):
    def test_from_llm_output(self):
        from agentguard.integrations.langchain import _extract_model_name

        class R:
            llm_output = {"model_name": "gpt-4o"}
        self.assertEqual(_extract_model_name(R()), "gpt-4o")

    def test_from_response_metadata(self):
        from agentguard.integrations.langchain import _extract_model_name

        class R:
            response_metadata = {"model": "claude-3-5-sonnet-20241022"}
        self.assertEqual(_extract_model_name(R()), "claude-3-5-sonnet-20241022")

    def test_from_metadata_model_id(self):
        from agentguard.integrations.langchain import _extract_model_name

        class R:
            metadata = {"model_id": "gemini-1.5-pro"}
        self.assertEqual(_extract_model_name(R()), "gemini-1.5-pro")

    def test_returns_unknown_when_no_model(self):
        from agentguard.integrations.langchain import _extract_model_name

        class R:
            pass
        self.assertEqual(_extract_model_name(R()), "unknown")

    def test_returns_unknown_for_empty_dicts(self):
        from agentguard.integrations.langchain import _extract_model_name

        class R:
            llm_output = {}
            response_metadata = {}
            metadata = {}
        self.assertEqual(_extract_model_name(R()), "unknown")


class _MockResponse:
    """Minimal mock for LangChain LLMResult."""

    def __init__(self, tokens: int = 0):
        self.llm_output = {
            "token_usage": {"total_tokens": tokens, "prompt_tokens": 0, "completion_tokens": tokens}
        } if tokens else {}

    def dict(self):
        return {"generations": [], "llm_output": self.llm_output}


class _MockResponseWithModel:
    """Mock LangChain LLMResult with model info and token usage."""

    def __init__(self, model: str = "unknown", input_t: int = 0, output_t: int = 0):
        total = input_t + output_t
        self.llm_output = {
            "model_name": model,
            "token_usage": {
                "total_tokens": total,
                "prompt_tokens": input_t,
                "completion_tokens": output_t,
            },
        }

    def dict(self):
        return {"generations": [], "llm_output": self.llm_output}


if __name__ == "__main__":
    unittest.main()
