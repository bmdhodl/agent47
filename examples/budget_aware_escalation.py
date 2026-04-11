"""Local-only example of advisor-style model escalation with AgentGuard.

Run:

    PYTHONPATH=sdk python examples/budget_aware_escalation.py
"""
from __future__ import annotations

from agentguard import (
    BudgetAwareEscalation,
    EscalationRequired,
    EscalationSignal,
    JsonlFileSink,
    Tracer,
)


def _simulated_model_call(model: str, prompt: str) -> dict:
    if model == "ollama/llama3.1:8b":
        return {
            "model": model,
            "prompt": prompt,
            "answer": "borderline",
            "token_count": 2430,
            "confidence": 0.39,
            "tool_call_depth": 4,
        }
    return {
        "model": model,
        "prompt": prompt,
        "answer": "escalated-final-answer",
        "token_count": 840,
        "confidence": 0.92,
        "tool_call_depth": 1,
    }


def main() -> int:
    guard = BudgetAwareEscalation(
        primary_model="ollama/llama3.1:8b",
        escalate_model="claude-opus-4-6",
        escalate_on=(
            EscalationSignal.TOKEN_COUNT(threshold=2000),
            EscalationSignal.CONFIDENCE_BELOW(threshold=0.45),
            EscalationSignal.TOOL_CALL_DEPTH(threshold=3),
        ),
    )
    tracer = Tracer(
        sink=JsonlFileSink("budget_aware_escalation_traces.jsonl"),
        service="budget-aware-escalation-example",
    )

    prompt = "Classify this contract clause and explain the escalation path."

    with tracer.trace("agent.turn.1") as ctx:
        first_model = guard.select_model()
        print(f"Turn 1 model: {first_model}")
        ctx.event("model.route", data={"selected_model": first_model, "route": "primary"})
        first_result = _simulated_model_call(first_model, prompt)
        ctx.event("llm.result", data=first_result)
        guard.auto_check("llm.result", first_result)

    with tracer.trace("agent.turn.2") as ctx:
        try:
            guard.check()
            second_model = guard.primary_model
            reason = "primary path"
        except EscalationRequired as exc:
            second_model = exc.target_model
            reason = exc.reason
            ctx.event(
                "guard.escalation",
                data={
                    "signal_name": exc.signal_name,
                    "reason": exc.reason,
                    "target_model": exc.target_model,
                },
            )
        print(f"Turn 2 model: {second_model}")
        print(f"Escalation reason: {reason}")
        ctx.event("model.route", data={"selected_model": second_model, "route": "escalated"})
        second_result = _simulated_model_call(second_model, prompt)
        ctx.event("llm.result", data=second_result)

    print("Wrote budget_aware_escalation_traces.jsonl")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
