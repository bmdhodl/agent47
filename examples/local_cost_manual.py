from agentguard import BudgetGuard, JsonlFileSink, Tracer, consume_billable

budget = BudgetGuard(max_tokens=3000, max_calls=1)
tracer = Tracer(sink=JsonlFileSink(".agentguard/traces.jsonl"))

budget.check()  # before the request you own
response = {
    "model": "qwen3.5:4b",
    "usage": {"prompt_tokens": 2000, "completion_tokens": 500, "total_tokens": 2500},
}
with tracer.trace("local.call") as span:
    resolved = consume_billable(
        budget, response, model=response["model"], provider="ollama", free_local=True,
    )
    span.event("llm.result", data=resolved["consume_log"], cost_usd=resolved["cost_usd"])
assert budget.state.tokens_used == 2500
assert budget.state.cost_used == 0
