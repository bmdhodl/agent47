import logging
from importlib.metadata import version, PackageNotFoundError

from .setup import init, shutdown, get_tracer, get_budget_guard
from .tracing import Tracer, JsonlFileSink, StdoutSink, TraceSink
from .guards import (
    AgentGuardError,
    BaseGuard,
    LoopGuard,
    BudgetGuard,
    TimeoutGuard,
    FuzzyLoopGuard,
    RateLimitGuard,
    LoopDetected,
    BudgetExceeded,
    BudgetWarning,
    TimeoutExceeded,
)
from .cost import CostTracker, estimate_cost, update_prices, UnknownModelWarning
from .recording import Recorder, Replayer
from .sinks import HttpSink
from .evaluation import EvalSuite, EvalResult, AssertionResult, summarize_trace
from .atracing import AsyncTracer, AsyncTraceContext
from .instrument import (
    trace_agent,
    trace_tool,
    patch_openai,
    patch_anthropic,
    unpatch_openai,
    unpatch_anthropic,
    async_trace_agent,
    async_trace_tool,
    patch_openai_async,
    patch_anthropic_async,
    unpatch_openai_async,
    unpatch_anthropic_async,
)

try:
    __version__ = version("agentguard47")
except PackageNotFoundError:
    __version__ = "0.0.0-dev"

# Libraries should not configure logging — only add NullHandler
# so consumers don't see "No handler found" warnings.
logging.getLogger("agentguard").addHandler(logging.NullHandler())

__all__ = [
    "__version__",
    "init",
    "shutdown",
    "get_tracer",
    "get_budget_guard",
    "Tracer",
    "JsonlFileSink",
    "StdoutSink",
    "TraceSink",
    "AgentGuardError",
    "LoopGuard",
    "BudgetGuard",
    "TimeoutGuard",
    "FuzzyLoopGuard",
    "RateLimitGuard",
    "LoopDetected",
    "BudgetExceeded",
    "BudgetWarning",
    "TimeoutExceeded",
    "CostTracker",
    "estimate_cost",
    "update_prices",
    "UnknownModelWarning",
    "Recorder",
    "Replayer",
    "HttpSink",
    "BaseGuard",
    "EvalSuite",
    "EvalResult",
    "AssertionResult",
    "summarize_trace",
    "trace_agent",
    "trace_tool",
    "patch_openai",
    "patch_anthropic",
    "unpatch_openai",
    "unpatch_anthropic",
    "AsyncTracer",
    "AsyncTraceContext",
    "async_trace_agent",
    "async_trace_tool",
    "patch_openai_async",
    "patch_anthropic_async",
    "unpatch_openai_async",
    "unpatch_anthropic_async",
]
