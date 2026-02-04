from __future__ import annotations

from typing import Any, Dict, Optional

from agentguard.tracing import Tracer


class AgentGuardCallbackHandler:
    """Minimal LangChain callback handler stub.

    This mirrors the naming used by LangChain without importing it to
    keep dependencies optional. It captures high-level LLM and tool events
    into AgentGuard traces. Users can subclass and expand as needed.
    """

    def __init__(self, tracer: Optional[Tracer] = None) -> None:
        self._tracer = tracer or Tracer()
        self._active_trace = None

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        name = serialized.get("name") or serialized.get("id") or "chain"
        self._active_trace = self._tracer.trace(f"chain.{name}", data={"inputs": inputs})
        self._active_trace.__enter__()

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        if self._active_trace is None:
            return
        self._active_trace.event("chain.outputs", data={"outputs": outputs})
        self._active_trace.__exit__(None, None, None)
        self._active_trace = None

    def on_llm_start(self, serialized: Dict[str, Any], prompts: list[str], **kwargs: Any) -> None:
        if self._active_trace is None:
            self.on_chain_start({"name": "llm"}, {"prompts": prompts})
        self._active_trace.event("llm.start", data={"prompts": prompts})

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        if self._active_trace is None:
            return
        usage = _extract_token_usage(response)
        payload = {"response": _safe_response(response)}
        if usage:
            payload["token_usage"] = usage
        if kwargs:
            payload["metadata"] = _safe_metadata(kwargs)
        self._active_trace.event("llm.end", data=payload)

    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs: Any) -> None:
        if self._active_trace is None:
            self.on_chain_start({"name": "tool"}, {"input": input_str})
        name = serialized.get("name") or serialized.get("id") or "tool"
        payload = {"tool": name, "input": input_str}
        if kwargs:
            payload["metadata"] = _safe_metadata(kwargs)
        self._active_trace.event("tool.start", data=payload)

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        if self._active_trace is None:
            return
        payload = {"output": output}
        if kwargs:
            payload["metadata"] = _safe_metadata(kwargs)
        self._active_trace.event("tool.end", data=payload)


def _safe_response(response: Any) -> Dict[str, Any]:
    try:
        if hasattr(response, "dict"):
            return response.dict()
    except Exception:
        pass
    return {"repr": repr(response)}


def _extract_token_usage(response: Any) -> Optional[Dict[str, Any]]:
    # Best-effort extraction without importing LangChain types.
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


def _safe_metadata(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    # Filter kwargs to JSON-serializable primitives where possible.
    safe: Dict[str, Any] = {}
    for key, value in kwargs.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            safe[key] = value
        elif isinstance(value, dict):
            safe[key] = value
        else:
            safe[key] = repr(value)
    return safe
