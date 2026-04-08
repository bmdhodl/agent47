import agentguard

tracer = agentguard.init(
    profile="coding-agent",
    service="my-agent",
    budget_usd=5.00,
    trace_file=".agentguard/traces.jsonl",
    local_only=True,
)

@agentguard.trace_tool(tracer)
def search_docs(query: str) -> str:
    return f"results for {query}"

with tracer.trace("agent.run") as span:
    result = search_docs("agentguard quickstart")
    span.event("agent.answer", data={"result": result})

print("Traces saved to " + ".agentguard/traces.jsonl")
