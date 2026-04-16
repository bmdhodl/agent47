"""Local proof that a single token-heavy turn can trip BudgetGuard.

Run:

    PYTHONPATH=sdk python examples/per_token_budget_spike.py
"""
from __future__ import annotations

from agentguard import (
    BudgetExceeded,
    BudgetGuard,
    JsonlFileSink,
    Tracer,
    estimate_cost,
)


def _turn_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    return estimate_cost(model, input_tokens=input_tokens, output_tokens=output_tokens)


def main() -> int:
    model = "gpt-4o"
    trace_file = "per_token_budget_spike_traces.jsonl"
    warnings = []

    budget = BudgetGuard(
        max_cost_usd=0.09,
        warn_at_pct=0.8,
        on_warning=warnings.append,
    )
    tracer = Tracer(
        sink=JsonlFileSink(trace_file),
        service="per-token-budget-spike",
    )

    turns = (
        {"name": "outline", "input_tokens": 1800, "output_tokens": 500},
        {"name": "revision", "input_tokens": 2200, "output_tokens": 700},
        {"name": "mega-context", "input_tokens": 18000, "output_tokens": 3500},
    )

    for index, turn in enumerate(turns, start=1):
        cost = _turn_cost(model, turn["input_tokens"], turn["output_tokens"])
        total_tokens = turn["input_tokens"] + turn["output_tokens"]
        try:
            with tracer.trace(f"agent.turn.{index}") as span:
                span.event(
                    "llm.turn",
                    data={
                        "model": model,
                        "turn_name": turn["name"],
                        "input_tokens": turn["input_tokens"],
                        "output_tokens": turn["output_tokens"],
                        "cost_usd": round(cost, 6),
                    },
                )
                budget.consume(tokens=total_tokens, calls=1, cost_usd=cost)
                state = budget.state
                print(
                    f"Turn {index} ({turn['name']}): "
                    f"{total_tokens} tokens -> ${cost:.4f} "
                    f"(running total ${state.cost_used:.4f})"
                )
        except BudgetExceeded as exc:
            state = budget.state
            print(
                f"Budget spike caught on turn {index} ({turn['name']}): "
                f"{total_tokens} tokens -> ${cost:.4f}"
            )
            print(str(exc))
            print(f"Final tracked total: ${state.cost_used:.4f} across {state.tokens_used} tokens")
            break

    for warning in warnings:
        print(f"Warning: {warning}")

    print(f"Wrote {trace_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
