from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from agentguard.guards import BudgetGuard, BudgetExceeded, LoopGuard, LoopDetected
from agentguard.tracing import Tracer, TraceContext

try:
    from langchain_core.callbacks.base import BaseCallbackHandler as _Base

    _HAS_LANGCHAIN = True
except ImportError:
    _Base = object  # type: ignore[assignment,misc]
    _HAS_LANGCHAIN = False


class AgentGuardCallbackHandler(_Base):  # type: ignore[misc]
    """LangChain callback handler that emits AgentGuard traces.

    Tracks nested chains/tool calls as a span stack, optionally wiring
    LoopGuard and BudgetGuard checks into tool invocations.

    Works with ``langchain-core >= 0.1``. Install via::

        pip install agentguard47[langchain]
    """

    def __init__(
        self,
        tracer: Optional[Tracer] = None,
        loop_guard: Optional[LoopGuard] = None,
        budget_guard: Optional[BudgetGuard] = None,
    ) -> None:
        if _HAS_LANGCHAIN:
            super().__init__()
        self._tracer = tracer or Tracer()
        self._loop_guard = loop_guard
        self._budget_guard = budget_guard
        self._root_ctx: Optional[Any] = None
        self._span_stack: List[TraceContext] = []
        self._run_to_span: Dict[str, TraceContext] = {}

    # -- chains ---------------------------------------------------------------

    def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        name = serialized.get("name") or serialized.get("id", ["chain"])[-1] if isinstance(serialized.get("id"), list) else serialized.get("name") or "chain"
        if not self._span_stack:
            ctx_mgr = self._tracer.trace(f"chain.{name}", data={"inputs": _safe_dict(inputs)})
            ctx = ctx_mgr.__enter__()
            self._root_ctx = ctx_mgr
            self._span_stack.append(ctx)
        else:
            parent = self._span_stack[-1]
            ctx = parent.span(f"chain.{name}", data={"inputs": _safe_dict(inputs)})
            ctx.__enter__()
            self._span_stack.append(ctx)
        if run_id:
            self._run_to_span[str(run_id)] = ctx

    def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        ctx = self._pop_span(run_id)
        if ctx is None:
            return
        ctx.event("chain.outputs", data={"outputs": _safe_dict(outputs)})
        ctx.__exit__(None, None, None)

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        ctx = self._pop_span(run_id)
        if ctx is None:
            return
        ctx.__exit__(type(error), error, error.__traceback__)

    # -- llm ------------------------------------------------------------------

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        parent = self._span_stack[-1] if self._span_stack else None
        if parent is None:
            self.on_chain_start({"name": "llm"}, {"prompts": prompts}, run_id=run_id)
            return
        ctx = parent.span("llm.call", data={"prompts": prompts})
        ctx.__enter__()
        self._span_stack.append(ctx)
        if run_id:
            self._run_to_span[str(run_id)] = ctx

    def on_llm_end(
        self,
        response: Any,
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        ctx = self._pop_span(run_id)
        if ctx is None:
            return
        usage = _extract_token_usage(response)
        payload: Dict[str, Any] = {"response": _safe_response(response)}
        if usage:
            payload["token_usage"] = usage
            # Estimate cost from token usage
            input_t = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
            output_t = usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)
            model_name = _extract_model_name(response)
            if input_t or output_t:
                from agentguard.cost import estimate_cost

                cost = estimate_cost(model_name, input_t, output_t)
                if cost > 0:
                    payload["cost_usd"] = cost
            if self._budget_guard and "total_tokens" in usage:
                try:
                    self._budget_guard.consume(tokens=usage["total_tokens"])
                except BudgetExceeded as e:
                    ctx.event("guard.budget_exceeded", data={
                        "tokens_used": self._budget_guard.state.tokens_used,
                        "tokens_limit": self._budget_guard._max_tokens,
                        "calls_used": self._budget_guard.state.calls_used,
                        "calls_limit": self._budget_guard._max_calls,
                        "error": str(e),
                    })
                    ctx.event("llm.end", data=payload)
                    ctx.__exit__(None, None, None)
                    raise
        ctx.event("llm.end", data=payload)
        ctx.__exit__(None, None, None)

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        ctx = self._pop_span(run_id)
        if ctx is None:
            return
        ctx.__exit__(type(error), error, error.__traceback__)

    # -- tools ----------------------------------------------------------------

    def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name") or serialized.get("id", "tool")
        if isinstance(tool_name, list):
            tool_name = tool_name[-1]
        if self._loop_guard:
            try:
                self._loop_guard.check(tool_name=tool_name, tool_args={"input": input_str})
            except LoopDetected as e:
                ctx = self._span_stack[-1] if self._span_stack else None
                if ctx:
                    ctx.event("guard.loop_detected", data={
                        "tool_name": tool_name,
                        "repeat_count": self._loop_guard._max_repeats,
                        "error": str(e),
                    })
                raise
        if self._budget_guard:
            try:
                self._budget_guard.consume(calls=1)
            except BudgetExceeded as e:
                ctx = self._span_stack[-1] if self._span_stack else None
                if ctx:
                    ctx.event("guard.budget_exceeded", data={
                        "tokens_used": self._budget_guard.state.tokens_used,
                        "tokens_limit": self._budget_guard._max_tokens,
                        "calls_used": self._budget_guard.state.calls_used,
                        "calls_limit": self._budget_guard._max_calls,
                        "error": str(e),
                    })
                raise
        parent = self._span_stack[-1] if self._span_stack else None
        if parent is None:
            self.on_chain_start({"name": "tool"}, {"input": input_str}, run_id=run_id)
            return
        ctx = parent.span(f"tool.{tool_name}", data={"input": input_str})
        ctx.__enter__()
        self._span_stack.append(ctx)
        if run_id:
            self._run_to_span[str(run_id)] = ctx

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        ctx = self._pop_span(run_id)
        if ctx is None:
            return
        ctx.event("tool.result", data={"output": str(output)})
        ctx.__exit__(None, None, None)

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: Optional[uuid.UUID] = None,
        **kwargs: Any,
    ) -> None:
        ctx = self._pop_span(run_id)
        if ctx is None:
            return
        ctx.__exit__(type(error), error, error.__traceback__)

    # -- helpers --------------------------------------------------------------

    def _pop_span(self, run_id: Optional[uuid.UUID]) -> Optional[TraceContext]:
        if run_id and str(run_id) in self._run_to_span:
            ctx = self._run_to_span.pop(str(run_id))
            if ctx in self._span_stack:
                self._span_stack.remove(ctx)
            return ctx
        if self._span_stack:
            return self._span_stack.pop()
        return None


# -- utility functions --------------------------------------------------------


def _safe_dict(d: Any) -> Dict[str, Any]:
    if isinstance(d, dict):
        return d
    return {"value": repr(d)}


def _safe_response(response: Any) -> Dict[str, Any]:
    try:
        if hasattr(response, "dict"):
            return response.dict()
        if hasattr(response, "model_dump"):
            return response.model_dump()
    except Exception:
        pass
    return {"repr": repr(response)}


def _extract_model_name(response: Any) -> str:
    """Try to extract model name from a LangChain LLM response."""
    for attr in ("llm_output", "response_metadata", "metadata"):
        if hasattr(response, attr):
            try:
                data = getattr(response, attr)
                if isinstance(data, dict):
                    model = data.get("model_name") or data.get("model") or data.get("model_id")
                    if model:
                        return str(model)
            except Exception:
                continue
    return "unknown"


def _extract_token_usage(response: Any) -> Optional[Dict[str, Any]]:
    for attr in ("llm_output", "response_metadata", "metadata"):
        if hasattr(response, attr):
            try:
                data = getattr(response, attr)
                if isinstance(data, dict):
                    usage = data.get("token_usage") or data.get("usage")
                    if isinstance(usage, dict):
                        return usage
            except Exception:
                continue
    return None
