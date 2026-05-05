import logging
from importlib.metadata import PackageNotFoundError, version

from .atracing import AsyncTraceContext, AsyncTracer
from .cost import estimate_cost
from .decision import (
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
from .evaluation import AssertionResult, EvalResult, EvalSuite, summarize_trace
from .guards import (
    AgentGuardError,
    BaseGuard,
    BudgetAwareEscalation,
    BudgetExceeded,
    BudgetGuard,
    BudgetWarning,
    EscalationRequired,
    EscalationSignal,
    FuzzyLoopGuard,
    LoopDetected,
    LoopGuard,
    RateLimitGuard,
    RetryGuard,
    RetryLimitExceeded,
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
from .schemas import (
    SUPPORTED_PROFILES,
    InitConfig,
    ProfileDefaults,
    RepoConfig,
)
from .setup import get_budget_guard, get_tracer, init, shutdown
from .sinks import HttpSink
from .tracing import JsonlFileSink, StdoutSink, Tracer, TraceSink

try:
    __version__ = version("agentguard47")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0-dev"

# Libraries should not configure logging; only add a NullHandler so
# consumers do not see "No handler found" warnings.
_logger = logging.getLogger("agentguard")
if not any(isinstance(handler, logging.NullHandler) for handler in _logger.handlers):
    _logger.addHandler(logging.NullHandler())

__all__ = [
    "AgentGuardError",
    "AssertionResult",
    "AsyncTraceContext",
    "AsyncTracer",
    "BaseGuard",
    "BudgetAwareEscalation",
    "BudgetExceeded",
    "BudgetGuard",
    "BudgetWarning",
    "DecisionTrace",
    "EscalationRequired",
    "EscalationSignal",
    "EvalResult",
    "EvalSuite",
    "FuzzyLoopGuard",
    "HttpSink",
    "InitConfig",
    "JsonlFileSink",
    "LoopDetected",
    "LoopGuard",
    "ProfileDefaults",
    "RateLimitGuard",
    "RepoConfig",
    "RetryGuard",
    "RetryLimitExceeded",
    "SUPPORTED_PROFILES",
    "StdoutSink",
    "TimeoutExceeded",
    "TimeoutGuard",
    "TraceSink",
    "Tracer",
    "__version__",
    "async_trace_agent",
    "async_trace_tool",
    "decision_flow",
    "estimate_cost",
    "extract_decision_events",
    "extract_decision_payload",
    "get_budget_guard",
    "get_tracer",
    "init",
    "is_decision_event",
    "log_decision_approved",
    "log_decision_bound",
    "log_decision_edited",
    "log_decision_overridden",
    "log_decision_proposed",
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
