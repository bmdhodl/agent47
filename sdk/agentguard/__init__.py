import logging
import re
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Optional

from .atracing import AsyncTraceContext, AsyncTracer
from .cost import estimate_cost
from .precision_cost import (
    ALLOWED_SOURCES,
    DEFAULT_PRICE_TABLE,
    CostResolutionError,
    consume_billable,
    get_default_prices,
    resolve_billable_cost,
)
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
from .goal import Call, Goal
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
from .state import JsonFileStateStore, StateStore, StateStoreError
from .tracing import JsonlFileSink, StdoutSink, Tracer, TraceSink


def _read_source_version() -> Optional[str]:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    if not pyproject_path.exists():
        return None

    content = pyproject_path.read_text(encoding="utf-8")
    in_project_table = False
    project_name = None
    project_version = None

    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_project_table = line == "[project]"
            continue
        if not in_project_table:
            continue

        name_match = re.match(r'^name\s*=\s*"([^"]+)"', line)
        if name_match is not None:
            project_name = name_match.group(1)
            continue

        version_match = re.match(r'^version\s*=\s*"([^"]+)"', line)
        if version_match is not None:
            project_version = version_match.group(1)

    if project_name != "agentguard47" or project_version is None:
        return None
    return project_version


def _package_version(package_name: str = "agentguard47") -> str:
    source_version = _read_source_version()
    if source_version:
        return source_version

    try:
        return version(package_name)
    except (PackageNotFoundError, TypeError):  # pragma: no cover
        return "0.0.0-dev"


__version__ = _package_version()

# Libraries should not configure logging; only add a NullHandler so
# consumers do not see "No handler found" warnings.
_logger = logging.getLogger("agentguard")
if not any(isinstance(handler, logging.NullHandler) for handler in _logger.handlers):
    _logger.addHandler(logging.NullHandler())

__all__ = [
    "SUPPORTED_PROFILES",
    "AgentGuardError",
    "AssertionResult",
    "AsyncTraceContext",
    "AsyncTracer",
    "BaseGuard",
    "BudgetAwareEscalation",
    "BudgetExceeded",
    "BudgetGuard",
    "BudgetWarning",
    "ALLOWED_SOURCES",
    "Call",
    "CostResolutionError",
    "DEFAULT_PRICE_TABLE",
    "DecisionTrace",
    "EscalationRequired",
    "EscalationSignal",
    "EvalResult",
    "EvalSuite",
    "FuzzyLoopGuard",
    "Goal",
    "HttpSink",
    "InitConfig",
    "JsonFileStateStore",
    "JsonlFileSink",
    "LoopDetected",
    "LoopGuard",
    "ProfileDefaults",
    "RateLimitGuard",
    "RepoConfig",
    "RetryGuard",
    "RetryLimitExceeded",
    "StateStore",
    "StateStoreError",
    "StdoutSink",
    "TimeoutExceeded",
    "TimeoutGuard",
    "TraceSink",
    "Tracer",
    "__version__",
    "async_trace_agent",
    "async_trace_tool",
    "consume_billable",
    "decision_flow",
    "estimate_cost",
    "extract_decision_events",
    "extract_decision_payload",
    "get_budget_guard",
    "get_default_prices",
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
    "resolve_billable_cost",
    "shutdown",
    "summarize_trace",
    "trace_agent",
    "trace_tool",
    "unpatch_anthropic",
    "unpatch_anthropic_async",
    "unpatch_openai",
    "unpatch_openai_async",
]
