"""Ralph Loop Agent — dogfood demo for AgentGuard SDK.

The Ralph Loop (named after Ralph Wiggum) is an outer-loop pattern where
a fresh agent instance runs each iteration, state persists on disk, and
an external signal — not the LLM — decides when the task is done.

This demo simulates a Ralph Loop that:
  1. Reads a task + progress file
  2. Spawns a fresh "agent" iteration (simulated LLM + tools)
  3. Writes code, runs verification (tests)
  4. Persists progress to disk
  5. Repeats until COMPLETE or guards intervene

AgentGuard provides the safety rails:
  - LoopGuard / FuzzyLoopGuard: catch stuck iterations
  - BudgetGuard: enforce dollar cap across all iterations
  - Cost tracking: per-call estimates

Run:
    cd sdk
    PYTHONPATH=. python examples/ralph_agent.py

    # Then inspect:
    agentguard report examples/ralph_traces.jsonl
"""
from __future__ import annotations

import json
import os
import random
import time
from typing import Any, Dict, List, Optional

from agentguard import (
    Tracer,
    JsonlFileSink,
    LoopGuard,
    FuzzyLoopGuard,
    BudgetGuard,
    BudgetExceeded,
    BudgetWarning,
    LoopDetected,
    EvalSuite,
    estimate_cost,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
TRACE_FILE = os.path.join(HERE, "ralph_traces.jsonl")
PROGRESS_FILE = os.path.join(HERE, "ralph_progress.txt")
MAX_ITERATIONS = 8
BUDGET_USD = 0.50  # dollar cap for the entire run


# ---------------------------------------------------------------------------
# Simulated LLM + Tools (swap for real OpenAI calls when ready)
# ---------------------------------------------------------------------------
class SimulatedLLM:
    """Fake LLM that progressively gets closer to solving the task.

    Iteration 1-2: tries wrong approach (gets stuck, triggers fuzzy guard)
    Iteration 3: partially correct
    Iteration 4+: correct solution
    """

    def __init__(self) -> None:
        self._call_count = 0

    def chat(self, prompt: str, iteration: int) -> Dict[str, Any]:
        self._call_count += 1
        # Simulate token usage + cost
        input_tokens = len(prompt.split()) * 2
        output_tokens = random.randint(50, 200)
        cost = estimate_cost(
            model="gpt-4o",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

        if iteration <= 2:
            # Stuck — keeps trying the same bad approach
            code = "def fibonacci(n):\n    return n  # wrong"
            reasoning = "I'll just return n directly"
        elif iteration == 3:
            # Partial fix
            code = "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)"
            reasoning = "Recursive approach, but no memoization — will be slow"
        else:
            # Correct
            code = (
                "def fibonacci(n):\n"
                "    if n <= 1:\n"
                "        return n\n"
                "    a, b = 0, 1\n"
                "    for _ in range(2, n + 1):\n"
                "        a, b = b, a + b\n"
                "    return b"
            )
            reasoning = "Iterative approach — O(n) time, O(1) space"

        return {
            "reasoning": reasoning,
            "code": code,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
        }


def run_tests(code: str) -> Dict[str, Any]:
    """External verification — the Ralph Loop's exit signal."""
    # Build a local namespace and exec the code
    ns: Dict[str, Any] = {}
    try:
        exec(code, ns)  # noqa: S102
    except Exception as e:
        return {"passed": False, "error": str(e), "results": []}

    fib = ns.get("fibonacci")
    if not callable(fib):
        return {"passed": False, "error": "fibonacci not defined", "results": []}

    cases = [(0, 0), (1, 1), (5, 5), (10, 55), (20, 6765)]
    results = []
    all_pass = True
    for n, expected in cases:
        try:
            actual = fib(n)
            ok = actual == expected
            if not ok:
                all_pass = False
            results.append({"n": n, "expected": expected, "actual": actual, "pass": ok})
        except Exception as e:
            all_pass = False
            results.append({"n": n, "expected": expected, "error": str(e), "pass": False})

    # Performance check (the naive recursive version blows up at n=35)
    if all_pass:
        start = time.perf_counter()
        try:
            fib(35)
            elapsed = time.perf_counter() - start
            if elapsed > 0.05:
                all_pass = False
                results.append({"perf_test": "fib(35)", "elapsed_s": round(elapsed, 3), "pass": False})
            else:
                results.append({"perf_test": "fib(35)", "elapsed_s": round(elapsed, 6), "pass": True})
        except RecursionError:
            all_pass = False
            results.append({"perf_test": "fib(35)", "error": "RecursionError", "pass": False})

    return {"passed": all_pass, "results": results}


def read_progress() -> List[str]:
    """Read append-only progress log from disk."""
    if not os.path.exists(PROGRESS_FILE):
        return []
    with open(PROGRESS_FILE, "r") as f:
        return [line.strip() for line in f if line.strip()]


def write_progress(iteration: int, summary: str) -> None:
    """Append a progress entry — persists across context rotations."""
    with open(PROGRESS_FILE, "a") as f:
        f.write(f"[iter {iteration}] {summary}\n")


# ---------------------------------------------------------------------------
# Ralph Loop
# ---------------------------------------------------------------------------
def ralph_loop() -> None:
    # Clean slate
    for f in [TRACE_FILE, PROGRESS_FILE]:
        if os.path.exists(f):
            os.remove(f)

    # --- AgentGuard setup ---
    budget_warnings: List[str] = []

    def on_budget_warning(msg: str) -> None:
        budget_warnings.append(msg)
        print(f"  WARNING: {msg}")

    tracer = Tracer(
        sink=JsonlFileSink(TRACE_FILE),
        service="ralph-agent",
        guards=[
            LoopGuard(max_repeats=4),
            FuzzyLoopGuard(max_tool_repeats=5, max_alternations=3),
        ],
        metadata={"demo": "ralph-loop", "max_iterations": MAX_ITERATIONS},
    )
    budget = BudgetGuard(
        max_cost_usd=BUDGET_USD,
        warn_at_pct=0.7,
        on_warning=on_budget_warning,
    )
    loop_guard = LoopGuard(max_repeats=3, window=6)
    llm = SimulatedLLM()

    print(f"Ralph Loop Agent")
    print(f"Task: Implement fibonacci(n) — iterative, O(n), passes all tests")
    print(f"Budget: ${BUDGET_USD:.2f} | Max iterations: {MAX_ITERATIONS}")
    print(f"Guards: LoopGuard, FuzzyLoopGuard, BudgetGuard(warn@70%)")
    print("=" * 60)

    completed = False

    with tracer.trace("ralph.run", data={"task": "fibonacci", "budget": BUDGET_USD}) as run:

        for iteration in range(1, MAX_ITERATIONS + 1):
            progress = read_progress()

            with run.span(f"ralph.iteration.{iteration}", data={
                "iteration": iteration,
                "prior_attempts": len(progress),
            }) as span:

                print(f"\n--- Iteration {iteration}/{MAX_ITERATIONS} ---")

                # 1. Build prompt (fresh context each iteration)
                prompt_parts = [
                    "Task: Write a Python function fibonacci(n) that returns the nth Fibonacci number.",
                    "Requirements: O(n) time, O(1) space, handles n=0 and n=1.",
                ]
                if progress:
                    prompt_parts.append(f"Previous attempts ({len(progress)}):")
                    for p in progress[-3:]:  # only last 3 to keep context small
                        prompt_parts.append(f"  {p}")
                prompt = "\n".join(prompt_parts)

                span.event("ralph.prompt_built", data={
                    "prompt_length": len(prompt),
                    "history_entries": len(progress),
                })

                # 2. Check guards before LLM call
                try:
                    loop_guard.check("llm.chat", {"iteration": iteration})
                except LoopDetected as e:
                    span.event("guard.loop_detected", data={"error": str(e)})
                    print(f"  LOOP DETECTED: {e}")
                    write_progress(iteration, f"STUCK — loop guard fired: {e}")
                    loop_guard.reset()
                    continue

                if budget.state.cost_used >= budget._max_cost_usd:
                    msg = f"${budget.state.cost_used:.4f} >= ${BUDGET_USD}"
                    span.event("guard.budget_exceeded", data={"error": msg})
                    print(f"  BUDGET EXCEEDED: {msg}")
                    write_progress(iteration, f"HALTED — budget exceeded: {msg}")
                    break

                # 3. LLM call (simulated)
                with span.span("llm.chat") as llm_span:
                    response = llm.chat(prompt, iteration)
                    cost = response["cost_usd"]
                    budget.consume(
                        tokens=response["input_tokens"] + response["output_tokens"],
                        calls=1,
                        cost_usd=cost,
                    )
                    llm_span.event("llm.response", data={
                        "reasoning": response["reasoning"],
                        "cost_usd": cost,
                        "tokens": response["input_tokens"] + response["output_tokens"],
                    })

                print(f"  LLM: {response['reasoning']}")
                print(f"  Cost: ${cost:.4f} (budget used: ${budget.state.cost_used:.4f}/${BUDGET_USD})")

                # 4. Run verification (external signal — not LLM self-assessment)
                with span.span("ralph.verify") as verify_span:
                    test_result = run_tests(response["code"])
                    verify_span.event("test.result", data=test_result)

                passed = test_result["passed"]
                n_pass = sum(1 for r in test_result["results"] if r.get("pass"))
                n_total = len(test_result["results"])
                print(f"  Tests: {n_pass}/{n_total} {'PASS' if passed else 'FAIL'}")

                if not passed:
                    failures = [r for r in test_result["results"] if not r.get("pass")]
                    fail_summary = "; ".join(
                        r.get("error", f"n={r.get('n')}: got {r.get('actual')}")
                        for r in failures[:2]
                    )
                    print(f"  Failures: {fail_summary}")

                # 5. Persist progress
                status = "PASS" if passed else "FAIL"
                write_progress(
                    iteration,
                    f"{status} — {response['reasoning']} — {n_pass}/{n_total} tests",
                )
                span.event("ralph.iteration_complete", data={
                    "passed": passed,
                    "tests_passed": n_pass,
                    "tests_total": n_total,
                })

                # 6. Check completion signal
                if passed:
                    span.event("ralph.complete", data={"iteration": iteration})
                    print(f"\n  COMPLETE at iteration {iteration}")
                    completed = True
                    break

        # End of loop
        run.event("ralph.summary", data={
            "completed": completed,
            "iterations": iteration,
            "total_cost": budget.state.cost_used,
            "budget_warnings": len(budget_warnings),
        })

    # --- Post-run report ---
    print("\n" + "=" * 60)
    print("Ralph Loop Summary")
    print("=" * 60)
    print(f"  Completed: {completed}")
    print(f"  Iterations: {iteration}/{MAX_ITERATIONS}")
    print(f"  Total cost: ${budget.state.cost_used:.4f} / ${BUDGET_USD:.2f}")
    print(f"  Budget warnings: {len(budget_warnings)}")
    print(f"  Traces: {TRACE_FILE}")

    # --- Run eval assertions ---
    print(f"\n  Running EvalSuite...")
    result = (
        EvalSuite(TRACE_FILE)
        .assert_no_loops()
        .assert_no_errors()
        .assert_cost_under(max_cost_usd=BUDGET_USD)
        .assert_completes_within(30.0)
        .run()
    )
    print(f"  Eval: {result.summary}")

    # --- Progress log ---
    print(f"\n  Progress log ({PROGRESS_FILE}):")
    for line in read_progress():
        print(f"    {line}")

    print(f"\n  View traces:")
    print(f"    agentguard report examples/ralph_traces.jsonl")


if __name__ == "__main__":
    ralph_loop()
