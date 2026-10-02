"""Price the same calls with resolve_billable_cost; run on main and on the branch.

Expected values come from the provider price pages cited in price_table.py.
"""
from agentguard.precision_cost import resolve_billable_cost

CASES = [
    # (label, provider, model, usage, expected USD)
    ("gpt-5.5, 300k prompt (long-context tier)", "openai", "gpt-5.5",
     {"prompt_tokens": 300_000, "completion_tokens": 1_000}, (300_000 * 10 + 1_000 * 45) / 1e6),
    ("gpt-5.5 dated snapshot", "openai", "gpt-5.5-2026-04-23",
     {"prompt_tokens": 10_000, "completion_tokens": 500}, (10_000 * 5 + 500 * 30) / 1e6),
    ("claude-opus-5", "anthropic", "claude-opus-5",
     {"input_tokens": 10_000, "output_tokens": 500}, (10_000 * 5 + 500 * 25) / 1e6),
    ("claude-sonnet-5", "anthropic", "claude-sonnet-5",
     {"input_tokens": 10_000, "output_tokens": 500}, (10_000 * 2 + 500 * 10) / 1e6),
    ("claude-fable-5-1, 50k cache read", "anthropic", "claude-fable-5-1",
     {"input_tokens": 2_000, "cache_read_input_tokens": 50_000, "output_tokens": 500},
     (2_000 * 10 + 50_000 * 0.25 + 500 * 50) / 1e6),
    ("claude-opus-4-20250514 (real Opus 4 id)", "anthropic", "claude-opus-4-20250514",
     {"input_tokens": 10_000, "output_tokens": 500}, (10_000 * 15 + 500 * 75) / 1e6),
    ("claude-haiku-4-5 alias", "anthropic", "claude-haiku-4-5",
     {"input_tokens": 10_000, "output_tokens": 500}, (10_000 * 1 + 500 * 5) / 1e6),
    ("unknown OpenAI model (no true price)", "openai", "gpt-next",
     {"prompt_tokens": 10_000, "completion_tokens": 500}, None),
]

print(f"{'case':44} {'recorded':>10} {'expected':>10} {'ratio':>7}  source")
for label, provider, model, usage, expected in CASES:
    r = resolve_billable_cost({"usage": usage}, model=model, provider=provider)
    ratio = f"{r['cost_usd'] / expected:.2f}x" if expected else "-"
    exp = f"${expected:.4f}" if expected else "-"
    print(f"{label:44} ${r['cost_usd']:>9.4f} {exp:>10} {ratio:>7}  {r['source']}")
