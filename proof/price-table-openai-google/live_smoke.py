"""Real OpenAI calls through the patched client; recorded cost vs the published price.

Needs OPENAI_API_KEY. Total spend is well under $0.01.
Published Standard rates, developers.openai.com/api/docs/pricing, 2026-09-26
(input, cached input, output per 1M tokens):
"""
import json
import os
import sys

from agentguard import BudgetGuard, JsonlFileSink, Tracer
from agentguard.instrument import patch_openai, patch_openai_async

PUBLISHED = {
    "gpt-5-nano": (0.05, 0.005, 0.40),
    "gpt-4.1-nano": (0.10, 0.025, 0.40),
    "gpt-4o-mini": (0.15, 0.075, 0.60),
}
TRACE = sys.argv[1] if len(sys.argv) > 1 else ".pytest_cache/live/price-smoke.jsonl"
if os.path.exists(TRACE):
    os.remove(TRACE)

guard = BudgetGuard(max_cost_usd=0.05)
tracer = Tracer(sink=JsonlFileSink(TRACE), service="price-smoke", watermark=False)
patch_openai(tracer, budget_guard=guard)
patch_openai_async(tracer, budget_guard=guard)  # the Agents SDK uses AsyncOpenAI

import openai  # noqa: E402

client = openai.OpenAI()
client.responses.create(model="gpt-5-nano", input="Reply with the word ok.",
                        reasoning={"effort": "minimal"}, max_output_tokens=64)
with client.responses.create(model="gpt-4o-mini", input="Reply with the word ok.",
                             max_output_tokens=16, stream=True) as stream:
    for _ in stream:
        pass
client.chat.completions.create(model="gpt-4.1-nano", max_tokens=5,
                               messages=[{"role": "user", "content": "Reply with the word ok."}])

from agents import Agent, Runner, set_tracing_disabled  # noqa: E402

set_tracing_disabled(True)
Runner.run_sync(Agent(name="a", instructions="Reply with one word.", model="gpt-5-nano"),
                "Say ok.", max_turns=2)

events = [json.loads(line) for line in open(TRACE, encoding="utf-8")]
results = [e for e in events if e.get("name") == "llm.result"]
print(f"{'model':14} {'in':>5} {'cached':>6} {'out':>5} {'recorded':>12} {'published':>12}  source")
total = 0.0
for e in results:
    d = e["data"]
    u = d.get("usage") or {}
    model = d["model"]
    base = next(m for m in PUBLISHED if model.startswith(m))
    rate_in, rate_cached, rate_out = PUBLISHED[base]
    prompt = u.get("input_tokens", u.get("prompt_tokens", 0))
    cached = u.get("cached_input_tokens", 0)  # prompts here are far below the 1024-token cache minimum
    out = u.get("output_tokens", u.get("completion_tokens", 0))
    published = ((prompt - cached) * rate_in + cached * rate_cached + out * rate_out) / 1e6
    total += e["cost_usd"]
    print(f"{model:14} {prompt:>5} {cached:>6} {out:>5} ${e['cost_usd']:>11.8f} "
          f"${published:>11.8f}  {d.get('source_of_cost')}")
    assert abs(e["cost_usd"] - published) < 1e-12, model
print(f"calls {len(results)} | guard cost ${guard.state.cost_used:.7f} | trace sum ${total:.7f}")
