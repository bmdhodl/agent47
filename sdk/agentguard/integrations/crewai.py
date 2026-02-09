"""CrewAI integration — step/task callbacks with AgentGuard tracing and guards.

Provides callback functions compatible with CrewAI's ``step_callback`` and
``task_callback`` hooks on Agent and Task objects.

Usage::

    from agentguard.integrations.crewai import AgentGuardCrewHandler
    from agentguard import Tracer, LoopGuard, BudgetGuard

    handler = AgentGuardCrewHandler(
        tracer=Tracer(sink=JsonlFileSink("traces.jsonl")),
        loop_guard=LoopGuard(max_repeats=3),
        budget_guard=BudgetGuard(max_cost_usd=5.00),
    )

    agent = Agent(
        role="researcher",
        step_callback=handler.step_callback,
    )

    task = Task(
        description="Research topic",
        agent=agent,
        callback=handler.task_callback,
    )

Requires ``crewai`` (optional dependency). Core SDK remains zero-dep.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from agentguard.guards import BudgetGuard, LoopGuard
from agentguard.tracing import Tracer


class AgentGuardCrewHandler:
    """Callback handler for CrewAI agents and tasks.

    Wire into CrewAI via ``step_callback`` on Agent and ``callback`` on Task.

    Args:
        tracer: AgentGuard Tracer instance. Creates a default if None.
        loop_guard: Optional LoopGuard — detects repeated tool calls.
        budget_guard: Optional BudgetGuard — enforces token/call/cost limits.
    """

    def __init__(
        self,
        tracer: Optional[Tracer] = None,
        loop_guard: Optional[LoopGuard] = None,
        budget_guard: Optional[BudgetGuard] = None,
    ) -> None:
        self._tracer = tracer or Tracer()
        self._loop_guard = loop_guard
        self._budget_guard = budget_guard

    def step_callback(self, step_output: Any) -> None:
        """CrewAI step callback — called after each agent step (tool use or thought).

        Args:
            step_output: CrewAI AgentAction or step result object.
        """
        tool_name = _extract_tool_name(step_output)
        tool_input = _extract_tool_input(step_output)
        tool_output = _extract_tool_output(step_output)

        # Check loop guard
        if self._loop_guard and tool_name:
            self._loop_guard.check(
                tool_name=tool_name,
                tool_args={"input": str(tool_input)[:500]} if tool_input else None,
            )

        # Check budget guard
        if self._budget_guard:
            self._budget_guard.consume(calls=1)

        # Emit a traced span for this step
        span_name = f"step.{tool_name}" if tool_name else "step.thought"
        data: Dict[str, Any] = {}
        if tool_name:
            data["tool"] = tool_name
        if tool_input:
            data["input"] = str(tool_input)[:500]
        if tool_output:
            data["output"] = str(tool_output)[:500]

        with self._tracer.trace(span_name, data=data):
            pass  # Step already executed; we're recording post-hoc

    def task_callback(self, task_output: Any) -> None:
        """CrewAI task callback — called when a task completes.

        Args:
            task_output: CrewAI TaskOutput object.
        """
        description = _extract_task_description(task_output)
        raw_output = _extract_raw_output(task_output)

        data: Dict[str, Any] = {}
        if description:
            data["description"] = str(description)[:500]
        if raw_output:
            data["output"] = str(raw_output)[:1000]

        with self._tracer.trace("task.complete", data=data):
            pass  # Task already executed; we're recording post-hoc

    def crew_callback(self, crew_output: Any) -> None:
        """Optional crew-level callback — called when the full crew finishes.

        Args:
            crew_output: CrewAI CrewOutput object.
        """
        data: Dict[str, Any] = {}
        if hasattr(crew_output, "raw"):
            data["output"] = str(crew_output.raw)[:1000]
        if hasattr(crew_output, "tasks_output") and crew_output.tasks_output:
            data["task_count"] = len(crew_output.tasks_output)

        with self._tracer.trace("crew.complete", data=data):
            pass


# -- helpers ------------------------------------------------------------------


def _extract_tool_name(step: Any) -> Optional[str]:
    """Extract tool name from a CrewAI step output."""
    # CrewAI AgentAction has .tool attribute
    if hasattr(step, "tool"):
        return str(step.tool)
    # Some versions wrap in result dict
    if isinstance(step, dict) and "tool" in step:
        return str(step["tool"])
    return None


def _extract_tool_input(step: Any) -> Optional[str]:
    """Extract tool input from a CrewAI step output."""
    if hasattr(step, "tool_input"):
        return str(step.tool_input)
    if isinstance(step, dict) and "tool_input" in step:
        return str(step["tool_input"])
    return None


def _extract_tool_output(step: Any) -> Optional[str]:
    """Extract tool output/result from a CrewAI step output."""
    if hasattr(step, "result"):
        return str(step.result)
    if hasattr(step, "output"):
        return str(step.output)
    if isinstance(step, dict) and "result" in step:
        return str(step["result"])
    return None


def _extract_task_description(task_output: Any) -> Optional[str]:
    """Extract description from a CrewAI TaskOutput."""
    if hasattr(task_output, "description"):
        return str(task_output.description)
    if isinstance(task_output, dict) and "description" in task_output:
        return str(task_output["description"])
    return None


def _extract_raw_output(task_output: Any) -> Optional[str]:
    """Extract raw output from a CrewAI TaskOutput."""
    if hasattr(task_output, "raw"):
        return str(task_output.raw)
    if hasattr(task_output, "raw_output"):
        return str(task_output.raw_output)
    if isinstance(task_output, dict) and "raw" in task_output:
        return str(task_output["raw"])
    return None
