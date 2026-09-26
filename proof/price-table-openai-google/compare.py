"""Price the same OpenAI and Gemini calls with resolve_billable_cost; run on main and on the branch.

Expected values: developers.openai.com/api/docs/pricing and
ai.google.dev/gemini-api/docs/pricing, Standard tier, read 2026-09-26.
"""
from agentguard.precision_cost import resolve_billable_cost

OAI = {"prompt_tokens": 10_000, "completion_tokens": 500}
OAI_CACHED = {"prompt_tokens": 50_000, "completion_tokens": 500,
              "prompt_tokens_details": {"cached_tokens": 40_000}}
GEM = {"usage_metadata": {"prompt_token_count": 10_000, "candidates_token_count": 500}}
GEM_THINKING = {"usage_metadata": {"prompt_token_count": 10_000, "candidates_token_count": 500,
                                   "thoughts_token_count": 2_000}}
GEM_CACHED = {"usage_metadata": {"prompt_token_count": 50_000, "candidates_token_count": 500,
                                 "cached_content_token_count": 40_000}}

CASES = [
    # (label, provider, model, response, expected USD)
    ("gpt-6-sol", "openai", "gpt-6-sol", {"usage": OAI}, (10_000 * 2 + 500 * 10) / 1e6),
    ("gpt-5.6-terra", "openai", "gpt-5.6-terra", {"usage": OAI}, (10_000 * 2 + 500 * 12) / 1e6),
    ("gpt-5", "openai", "gpt-5", {"usage": OAI}, (10_000 * 1.25 + 500 * 10) / 1e6),
    ("o3", "openai", "o3", {"usage": OAI}, (10_000 * 2 + 500 * 8) / 1e6),
    ("gpt-5.5, 40k cached of 50k", "openai", "gpt-5.5", {"usage": OAI_CACHED},
     (10_000 * 5 + 40_000 * 0.5 + 500 * 30) / 1e6),
    ("gpt-5.4, 40k cached of 50k", "openai", "gpt-5.4", {"usage": OAI_CACHED},
     (10_000 * 2.5 + 40_000 * 0.25 + 500 * 15) / 1e6),
    ("gemini-3.5-flash", "google", "gemini-3.5-flash", GEM, (10_000 * 1.5 + 500 * 9) / 1e6),
    ("gemini-3.1-pro-preview", "google", "gemini-3.1-pro-preview", GEM,
     (10_000 * 2 + 500 * 12) / 1e6),
    ("gemini-2.5-pro, 2k thinking tokens", "google", "gemini-2.5-pro", GEM_THINKING,
     (10_000 * 1.25 + 2_500 * 10) / 1e6),
    ("gemini-2.5-pro, 40k cached of 50k", "google", "gemini-2.5-pro", GEM_CACHED,
     (10_000 * 1.25 + 40_000 * 0.125 + 500 * 10) / 1e6),
]

print(f"{'case':36} {'recorded':>10} {'expected':>10} {'ratio':>7}  source")
for label, provider, model, response, expected in CASES:
    r = resolve_billable_cost(response, model=model, provider=provider)
    ratio = f"{r['cost_usd'] / expected:.2f}x"
    print(f"{label:36} ${r['cost_usd']:>9.4f} ${expected:>9.4f} {ratio:>7}  {r['source']}")
