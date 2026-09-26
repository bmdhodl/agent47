import json
import os
import tempfile
import threading
import unittest
import uuid

from agentguard.guards import BudgetExceeded, BudgetGuard, LoopDetected, LoopGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler
from agentguard.tracing import JsonlFileSink, Tracer


class TestLangChainIntegration(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._trace_path = os.path.join(self._tmpdir, "traces.jsonl")
        self.sink = JsonlFileSink(self._trace_path)
        self.tracer = Tracer(sink=self.sink, service="test")

    def _read_events(self):
        with open(self._trace_path) as f:
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
        self.assertEqual(handler._span_stack, [])
        self.assertEqual(handler._run_to_span, {})
        self.assertIsNone(handler._root_ctx)

    def test_parent_end_closes_never_ended_child_run(self):
        handler = AgentGuardCallbackHandler(tracer=self.tracer)
        chain_id = uuid.uuid4()
        llm_id = uuid.uuid4()

        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        handler.on_chain_end({"output": "done"}, run_id=chain_id)

        self.assertEqual(handler._span_stack, [])
        self.assertEqual(handler._run_to_span, {})
        self.assertIsNone(handler._root_ctx)

    def test_stale_child_end_does_not_close_new_active_run(self):
        handler = AgentGuardCallbackHandler(tracer=self.tracer)
        chain_id = uuid.uuid4()
        llm_id = uuid.uuid4()

        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        handler.on_chain_end({"output": "done"}, run_id=chain_id)

        next_chain_id = uuid.uuid4()
        handler.on_chain_start({"name": "next"}, {}, run_id=next_chain_id)
        handler.on_llm_end(_MockResponse(), run_id=llm_id)

        self.assertEqual(len(handler._span_stack), 1)
        self.assertIn(str(next_chain_id), handler._run_to_span)
        handler.on_chain_end({"output": "done"}, run_id=next_chain_id)
        self.assertEqual(handler._span_stack, [])
        self.assertEqual(handler._run_to_span, {})
        self.assertIsNone(handler._root_ctx)

    def test_concurrent_callback_lifecycles_do_not_corrupt_state(self):
        handler = AgentGuardCallbackHandler(tracer=self.tracer)

        def run_lifecycle(index: int) -> None:
            run_id = uuid.uuid4()
            handler.on_chain_start({"name": f"agent-{index}"}, {"input": index}, run_id=run_id)
            handler.on_chain_end({"output": index}, run_id=run_id)

        threads = [threading.Thread(target=run_lifecycle, args=(index,)) for index in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(handler._span_stack, [])
        self.assertEqual(handler._run_to_span, {})
        self.assertIsNone(handler._root_ctx)

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
        handler.on_llm_end(
            _MockResponseWithModel(model="gpt-4o", input_t=40, output_t=40),
            run_id=llm_id,
        )

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

    def test_llm_start_does_not_preflight_exhausted_budget(self):
        """LLM dispatch is recorded after the call, not refused before it."""
        guard = BudgetGuard(max_tokens=1)
        guard.consume(tokens=1)
        handler = AgentGuardCallbackHandler(
            tracer=self.tracer, budget_guard=guard
        )
        chain_id = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)
        llm_id = uuid.uuid4()
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        with self.assertRaises(BudgetExceeded):
            handler.on_llm_end(
                _MockResponseWithModel(model="gpt-4o", input_t=1, output_t=1),
                run_id=llm_id,
            )

    def test_tool_start_blocks_exhausted_call_budget(self):
        guard = BudgetGuard(max_calls=1)
        guard.consume(calls=1)
        handler = AgentGuardCallbackHandler(
            tracer=self.tracer, budget_guard=guard
        )
        chain_id = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)
        with self.assertRaises(BudgetExceeded):
            handler.on_tool_start({"name": "search"}, "q1", run_id=uuid.uuid4())

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
        self.assertEqual(data["provider"], "openai")
        self.assertEqual(data["model"], "gpt-4o")
        self.assertEqual(data["token_usage"]["input_tokens"], 1000)
        self.assertEqual(data["token_usage"]["output_tokens"], 500)
        self.assertEqual(data["token_usage"]["total_tokens"], 1500)

    def test_llm_end_prices_unknown_model_as_overestimate(self):
        """An unknown model is charged, not recorded as free."""
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
        data = next(e for e in events if e["name"] == "llm.end").get("data", {})
        self.assertGreater(data["cost_usd"], 0)
        self.assertEqual(data["source_of_cost"], "overestimate")

    def test_unknown_model_trips_a_dollar_budget(self):
        guard = BudgetGuard(max_cost_usd=0.01)
        handler = AgentGuardCallbackHandler(tracer=self.tracer, budget_guard=guard)
        handler.on_chain_start({"name": "agent"}, {}, run_id=uuid.uuid4())
        llm_id = uuid.uuid4()
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        with self.assertRaises(BudgetExceeded):
            handler.on_llm_end(
                _MockResponseWithModel(model="gpt-next", input_t=100_000, output_t=1_000),
                run_id=llm_id,
            )

    def test_strict_precision_raises_and_closes_the_llm_span(self):
        from unittest import mock

        from agentguard.precision_cost import CostResolutionError

        handler = AgentGuardCallbackHandler(tracer=self.tracer)
        handler.on_chain_start({"name": "agent"}, {}, run_id=uuid.uuid4())
        llm_id = uuid.uuid4()
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        with mock.patch.dict("os.environ", {"STRICT_PRECISION": "1"}), \
                self.assertRaises(CostResolutionError):
            handler.on_llm_end(
                _MockResponseWithModel(model="gpt-next", input_t=100, output_t=10),
                run_id=llm_id,
            )
        ended = [e for e in self._read_events()
                 if e.get("kind") == "span" and e.get("phase") == "end" and e.get("error")]
        self.assertEqual(ended[0]["error"]["type"], "CostResolutionError")

    def test_llm_end_bills_reasoning_tokens_once(self):
        """completion_tokens already include reasoning_tokens."""
        handler = AgentGuardCallbackHandler(tracer=self.tracer)
        handler.on_chain_start({"name": "agent"}, {}, run_id=uuid.uuid4())
        llm_id = uuid.uuid4()
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        response = _MockResponseWithModel(model="o3-mini", input_t=0, output_t=0)
        response.llm_output = {
            "model_name": "o3-mini",
            "token_usage": {"prompt_tokens": 1_000, "completion_tokens": 100_000,
                            "total_tokens": 101_000,
                            "completion_tokens_details": {"reasoning_tokens": 80_000}},
        }
        handler.on_llm_end(response, run_id=llm_id)

        data = next(e for e in self._read_events() if e["name"] == "llm.end")["data"]
        # o3-mini: $1.10 input, $4.40 output per 1M; reasoning is inside the 100k.
        self.assertAlmostEqual(data["cost_usd"], (1_000 * 1.10 + 100_000 * 4.40) / 1e6)

    def test_llm_end_bills_anthropic_cache_reads(self):
        """Cache-read tokens sit outside Anthropic input_tokens and are billed at the cache rate."""
        handler = AgentGuardCallbackHandler(tracer=self.tracer)
        handler.on_chain_start({"name": "agent"}, {}, run_id=uuid.uuid4())
        llm_id = uuid.uuid4()
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        response = _MockResponseWithModel(model="claude-sonnet-4-6", input_t=0, output_t=0)
        response.llm_output = {
            "model_name": "claude-sonnet-4-6",
            "usage": {"input_tokens": 1_000, "output_tokens": 100,
                      "cache_read_input_tokens": 50_000},
        }
        handler.on_llm_end(response, run_id=llm_id)

        data = next(e for e in self._read_events() if e["name"] == "llm.end")["data"]
        # $3 input, $0.30 cache read, $15 output per 1M.
        self.assertAlmostEqual(data["cost_usd"], (1_000 * 3 + 50_000 * 0.30 + 100 * 15) / 1e6)

    def test_llm_end_normalizes_anthropic_usage(self):
        handler = AgentGuardCallbackHandler(tracer=self.tracer)
        chain_id = uuid.uuid4()
        handler.on_chain_start({"name": "agent"}, {}, run_id=chain_id)

        llm_id = uuid.uuid4()
        handler.on_llm_start({}, ["prompt"], run_id=llm_id)
        handler.on_llm_end(
            _MockAnthropicResponse(
                model="claude-sonnet-4-20250514",
                input_t=300,
                output_t=40,
                cache_read_t=200,
            ),
            run_id=llm_id,
        )
        handler.on_chain_end({}, run_id=chain_id)

        events = self._read_events()
        llm_end_events = [e for e in events if e["name"] == "llm.end"]
        self.assertTrue(len(llm_end_events) >= 1)
        data = llm_end_events[0].get("data", {})
        self.assertEqual(data["provider"], "anthropic")
        self.assertEqual(data["model"], "claude-sonnet-4-20250514")
        self.assertEqual(data["token_usage"]["input_tokens"], 300)
        self.assertEqual(data["token_usage"]["output_tokens"], 40)
        self.assertEqual(data["token_usage"]["cached_input_tokens"], 200)
        self.assertEqual(data["token_usage"]["total_tokens"], 540)


class TestExtractModelName(unittest.TestCase):
    def test_from_llm_output(self):
        from agentguard.integrations.langchain import _extract_model_name

        class R:
            def __init__(self):
                self.llm_output = {"model_name": "gpt-4o"}

        self.assertEqual(_extract_model_name(R()), "gpt-4o")

    def test_from_response_metadata(self):
        from agentguard.integrations.langchain import _extract_model_name

        class R:
            def __init__(self):
                self.response_metadata = {"model": "claude-3-5-sonnet-20241022"}

        self.assertEqual(_extract_model_name(R()), "claude-3-5-sonnet-20241022")

    def test_from_metadata_model_id(self):
        from agentguard.integrations.langchain import _extract_model_name

        class R:
            def __init__(self):
                self.metadata = {"model_id": "gemini-1.5-pro"}

        self.assertEqual(_extract_model_name(R()), "gemini-1.5-pro")

    def test_returns_unknown_when_no_model(self):
        from agentguard.integrations.langchain import _extract_model_name

        class R:
            pass
        self.assertEqual(_extract_model_name(R()), "unknown")

    def test_returns_unknown_for_empty_dicts(self):
        from agentguard.integrations.langchain import _extract_model_name

        class R:
            def __init__(self):
                self.llm_output = {}
                self.response_metadata = {}
                self.metadata = {}

        self.assertEqual(_extract_model_name(R()), "unknown")


class TestExtractTokenUsage(unittest.TestCase):
    def test_ignores_model_extraction_errors(self):
        from agentguard.integrations.langchain import _extract_token_usage

        class R:
            def __init__(self):
                self.llm_output = {
                    "token_usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    }
                }

            @property
            def response_metadata(self):
                raise RuntimeError("boom")

        usage = _extract_token_usage(R())
        self.assertEqual(
            usage,
            {
                "input_tokens": 10,
                "output_tokens": 5,
                "total_tokens": 15,
                "prompt_tokens": 10,
                "completion_tokens": 5,
            },
        )


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


class _MockAnthropicResponse:
    """Mock LangChain LLMResult with Anthropic-style usage fields."""

    def __init__(self, model: str, input_t: int, output_t: int, cache_read_t: int = 0):
        self.llm_output = {
            "model_name": model,
            "token_usage": {
                "input_tokens": input_t,
                "output_tokens": output_t,
                "cache_read_input_tokens": cache_read_t,
            },
        }

    def dict(self):
        return {"generations": [], "llm_output": self.llm_output}


if __name__ == "__main__":
    unittest.main()
