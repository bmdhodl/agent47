import logging
from importlib.metadata import PackageNotFoundError, version

from .atracing import AsyncTraceContext, AsyncTracer
from .cost import estimate_cost
from .evaluation import AssertionResult, EvalResult, EvalSuite, summarize_trace
from .guards import (
    AgentGuardError,
    BaseGuard,
    BudgetExceeded,
    BudgetGuard,
    BudgetWarning,
    FuzzyLoopGuard,
    LoopDetected,
    LoopGuard,
    RateLimitGuard,
    TimeoutExceeded,
    TimeoutGuard,
)
from .instrument import (
    async_trace_agent,
    async_trace_tool,
    patch_anthropic,
    patch_anthropic_async,
    patch_openai,
    patch_openai_async,
    trace_agent,
    trace_tool,
    unpatch_anthropic,
    unpatch_anthropic_async,
    unpatch_openai,
    unpatch_openai_async,
)
from .setup import get_budget_guard, get_tracer, init, shutdown
from .sinks import HttpSink
from .tracing import JsonlFileSink, StdoutSink, Tracer, TraceSink

try:
    __version__ = version("agentguard47")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0-dev"

# Libraries should not configure logging — only add NullHandler
# so consumers don't see "No handler found" warnings.
logging.getLogger("agentguard").addHandler(logging.NullHandler())

__all__ = [
    "AgentGuardError",
    "AssertionResult",
    "AsyncTraceContext",
    "AsyncTracer",
    "BaseGuard",
    "BudgetExceeded",
    "BudgetGuard",
    "BudgetWarning",
    "EvalResult",
    "EvalSuite",
    "FuzzyLoopGuard",
    "HttpSink",
    "JsonlFileSink",
    "LoopDetected",
    "LoopGuard",
    "RateLimitGuard",
    "StdoutSink",
    "TimeoutExceeded",
    "TimeoutGuard",
    "TraceSink",
    "Tracer",
    "__version__",
    "async_trace_agent",
    "async_trace_tool",
    "estimate_cost",
    "get_budget_guard",
    "get_tracer",
    "init",
    "patch_anthropic",
    "patch_anthropic_async",
    "patch_openai",
    "patch_openai_async",
    "shutdown",
    "summarize_trace",
    "trace_agent",
    "trace_tool",
    "unpatch_anthropic",
    "unpatch_anthropic_async",
    "unpatch_openai",
    "unpatch_openai_async",
]
