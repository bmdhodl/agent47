import agentguard
from openai import OpenAI

agentguard.init(
    profile="coding-agent",
    service="my-agent",
    budget_usd=5.00,
    trace_file=".agentguard/traces.jsonl",
    local_only=True,
)

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Give me a one-line summary of AgentGuard."}],
)

print(response.choices[0].message.content)
print("Traces saved to " + ".agentguard/traces.jsonl")
