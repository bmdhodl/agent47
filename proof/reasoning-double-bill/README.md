# Reasoning tokens billed once

`_compute_from_table` billed every output token at the output rate, then
billed reasoning/thinking tokens again. OpenAI `completion_tokens` /
`output_tokens` and Anthropic `output_tokens` already include them.

Now the reasoning slice bills at `reasoning_per_1m` (default: the output rate)
and the rest of output at the output rate. Totals equal
`output * out + reasoning * (reasoning_rate - out)`.

| Payload | Before | After |
|---|---|---|
| gpt-4o-mini, Chat Completions: 10 in (4 cached), 5 out, 2 reasoning | $5.4e-6 | $4.2e-6 |
| gpt-4o-mini, Responses API: same counts | $5.4e-6 | $4.2e-6 |
| claude-sonnet-4-5: 100 in, 50 out, 30 thinking | $1.5e-3 | $1.05e-3 |
| gpt-4o-mini Chat row with `reasoning_per_1m=2.40` | $9.0e-6 | $7.8e-6 |

## Files

- `before-fix.txt`: the new tests against the old `precision_cost.py`. 4 failed.
- `after-fix.txt`: the same files with the fix. 47 passed.
- `make-check.txt`: `make check`, trimmed to summaries. 1263 passed, 19 skipped,
  coverage 91.89%, MCP 11/11.
- `compat-latest.txt`: full suite with real openai 3.19.2, anthropic 1.8.0,
  and openai-agents 0.22.3. 1282 passed.
- `make-structural.txt`, `make-security.txt`, `make-release-guard.txt`: pass.
- `make-preflight.txt`: fails on 3 ruff findings in
  `sdk/tests/test_precision_cost.py` (I001, SIM117 x2). HEAD's copy has the
  same 3. CI lints `sdk/agentguard/` only. Left out of scope.
- `preflight-remaining-steps.txt`: the other preflight steps, with that file
  kept out of the ruff input only. All pass.

The compat run shows 6 `RuntimeWarning: coroutine ... never awaited` from
async tests in `test_real_dispatch.py`. HEAD shows the same 6 (1279 passed).

Local runs used Python 3.11. CI uses 3.9 and 3.12.
