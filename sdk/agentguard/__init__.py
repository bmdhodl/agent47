import logging
import os
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

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

# --- First-run star prompt ---
_CI_ENV_VARS = (
    "CI", "GITHUB_ACTIONS", "JENKINS_URL", "GITLAB_CI",
    "CIRCLECI", "TRAVIS", "TF_BUILD", "BUILDKITE",
)


def _show_first_run_prompt() -> None:
    """Show a one-time welcome message on first import. Never in CI."""
    if os.environ.get("AGENTGUARD_QUIET", "") == "1":
        return
    if any(os.environ.get(v) for v in _CI_ENV_VARS):
        return
    try:
        marker_dir = Path.home() / ".agentguard"
        marker = marker_dir / ".first_run_shown"
        if marker.exists():
            return
        marker_dir.mkdir(parents=True, exist_ok=True)
        print(  # noqa: T201
            f"agentguard47 v{__version__} \u2014 runtime guards for AI agents\n"
            f"Docs: https://github.com/bmdhodl/agent47\n"
            f"\u2b50 Star us if this helps: https://github.com/bmdhodl/agent47",
            file=sys.stderr,
        )
        marker.write_text("shown\n")
    except Exception:
        pass  # Never crash on first-run prompt failure


_show_first_run_prompt()

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
