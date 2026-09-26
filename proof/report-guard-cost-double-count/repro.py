"""Drive $1.50 OpenAI calls through the real client until BudgetExceeded, then report."""
import json, os, subprocess, sys, tempfile
import importlib, openai
from agentguard import BudgetExceeded, BudgetGuard, JsonlFileSink, Tracer
from agentguard.instrument import patch_openai, unpatch_openai

body = {
    "id": "c", "object": "chat.completion", "created": 0, "model": "gpt-4o-mini",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
    "cost": 1.50,  # provider-reported cost field -> resolve_billable_cost uses it
}
path = os.path.join(tempfile.mkdtemp(), "trace.jsonl")
guard = BudgetGuard(max_cost_usd=5.0)
patch_openai(Tracer(sink=JsonlFileSink(path)), budget_guard=guard)
base = next(c for c in openai.DefaultHttpxClient.__mro__ if c.__name__ == "Client")
httpx = importlib.import_module(base.__module__.split(".")[0])
client = openai.OpenAI(api_key="x", http_client=openai.DefaultHttpxClient(
    transport=httpx.MockTransport(lambda r: httpx.Response(200, json=body))))
try:
    for _ in range(10):
        client.chat.completions.create(model="gpt-4o-mini", messages=[{"role": "user", "content": "hi"}])
except BudgetExceeded as exc:
    print("BudgetExceeded:", exc)
unpatch_openai()
print(f"guard cost_used: ${guard.state.cost_used:.2f}")
for line in open(path):
    e = json.loads(line)
    if e["name"] in ("llm.result", "guard.budget_exceeded"):
        print(e["name"], "top cost_usd=", e.get("cost_usd"), "data.cost_usd=", e.get("data", {}).get("cost_usd"))
sys.stdout.flush()
subprocess.run([sys.executable, "-m", "agentguard", "report", path])
