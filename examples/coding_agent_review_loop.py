"""Local proof that repeated coding-agent review loops burn budget.

Run:

    PYTHONPATH=sdk python examples/coding_agent_review_loop.py
    agentguard report coding_agent_review_loop_traces.jsonl
    agentguard incident coding_agent_review_loop_traces.jsonl

No API keys, dashboard, or network calls are required.
"""
from __future__ import annotations

from agentguard import (
    BudgetExceeded,
    BudgetGuard,
    JsonlFileSink,
    RetryGuard,
    RetryLimitExceeded,
    Tracer,
    estimate_cost,
)


TRACE_FILE = "coding_agent_review_loop_traces.jsonl"
MODEL = "gpt-4o"


def _turn_cost(input_tokens: int, output_tokens: int) -> float:
    return estimate_cost(MODEL, input_tokens=input_tokens, output_tokens=output_tokens)


def _run_review_budget_loop(tracer: Tracer) -> None:
    budget = BudgetGuard(max_cost_usd=0.045, warn_at_pct=0.8)
    review_turns = (
        {
            "attempt": 1,
            "input_tokens": 2600,
            "output_tokens": 700,
            "comment": "tighten tests and rerun",
        },
        {
            "attempt": 2,
            "input_tokens": 3200,
            "output_tokens": 900,
            "comment": "address new reviewer concern",
        },
        {
            "attempt": 3,
            "input_tokens": 3800,
            "output_tokens": 1100,
            "comment": "same concern resurfaced after edits",
        },
    )

    with tracer.trace("coding_agent.review_loop.budget") as span:
        for turn in review_turns:
            cost = _turn_cost(turn["input_tokens"], turn["output_tokens"])
            total_tokens = turn["input_tokens"] + turn["output_tokens"]
            span.event(
                "review.iteration",
                data={
                    "attempt": turn["attempt"],
                    "model": MODEL,
                    "input_tokens": turn["input_tokens"],
                    "output_tokens": turn["output_tokens"],
                    "reviewer_comment": turn["comment"],
                    "cost_usd": round(cost, 6),
                },
                cost_usd=cost,
            )
            try:
                budget.consume(tokens=total_tokens, calls=1, cost_usd=cost)
                print(
                    f"Review attempt {turn['attempt']}: "
                    f"{total_tokens} tokens -> ${cost:.4f} "
                    f"(running total ${budget.state.cost_used:.4f})"
                )
            except BudgetExceeded as exc:
                span.event(
                    "guard.budget_exceeded",
                    data={
                        "attempt": turn["attempt"],
                        "reason": str(exc),
                        "cost_usd": round(budget.state.cost_used, 6),
                        "tokens_used": budget.state.tokens_used,
                    },
                )
                print(
                    f"BudgetGuard stopped review loop on attempt {turn['attempt']}: "
                    f"{total_tokens} tokens -> ${cost:.4f}"
                )
                print(str(exc))
                break


def _run_retry_storm(tracer: Tracer) -> None:
    retry_guard = RetryGuard(max_retries=3)
    with tracer.trace("coding_agent.review_loop.retry_storm") as span:
        for attempt in range(1, 6):
            span.event(
                "tool.retry",
                data={
                    "tool_name": "apply_patch",
                    "attempt": attempt,
                    "reason": "review feedback still unresolved",
                },
            )
            try:
                retry_guard.check("apply_patch")
                print(f"Retry attempt {attempt}: apply_patch still retrying")
            except RetryLimitExceeded as exc:
                span.event(
                    "guard.retry_limit_exceeded",
                    data={
                        "tool_name": "apply_patch",
                        "attempt": attempt,
                        "reason": str(exc),
                    },
                )
                print(f"RetryGuard stopped retry storm on attempt {attempt}: {exc}")
                break


def main() -> int:
    tracer = Tracer(
        sink=JsonlFileSink(TRACE_FILE),
        service="coding-agent-review-loop",
    )

    print("AgentGuard coding-agent review loop proof")
    print("No API keys. No dashboard. No network calls.")
    _run_review_budget_loop(tracer)
    _run_retry_storm(tracer)
    print(f"Trace written to {TRACE_FILE}")
    print(f"Next: agentguard incident {TRACE_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
