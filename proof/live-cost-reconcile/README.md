# Live OpenAI cost reconciliation — proof

Platform: Linux x86_64, Python 3.11.15, openai 3.19.2. Date: 2026-09-27 UTC.

## Run 2 — gate passes (`run2-live.txt`, exit 0)

```
python scripts/live_cost_reconcile.py --out .pytest_cache/live-cost-run2
```

Six real calls (Chat Completions, Responses, a Responses stream, gpt-5-nano at
minimal effort, and a 2,053-token prompt sent twice) through `patch_openai` with
`BudgetGuard(max_cost_usd=0.02)`. Spend: $0.0002856.

OpenAI's Usage API matched AgentGuard's trace exactly on every model:
requests, input, cached input (1,920 on the second long prompt) and output tokens.
Cost from OpenAI's counts × the price table equals AgentGuard's recorded cost
within 1e-9. Usage took ~15 minutes to cover the run.

## Run 1 — timed out before usage landed (`run1-timeout-15m.txt`, exit 1)

The first run used a 15-minute wait. gpt-4o-mini and gpt-5-nano landed within
minutes and matched; the three gpt-4.1-nano calls were absent from both the
Usage and Costs APIs until ~55 minutes after the run, then matched exactly
(3 requests, 4,119 input, 1,920 cached, 5 output). A control gpt-4.1-nano call
sent 35 minutes later landed in ~4 minutes, so the lag is per call, not per
model. The script now waits up to 60 minutes; the job timeout is 75.

## D-2 Costs report (report only)

The 2026-09-25 bucket had no usage, so the ratio is `n/a`. Every cost row this
organization returned on the days probed shows `amount.value = 0.0`, so the
Costs API cannot currently validate dollars for this org; token counts are the
gate.

## Checks

`make-check.txt` (exit 0, 1355 passed, coverage 92.36%) and `checks.txt`
(structural, security, release-guard, the new tests — all exit 0). The three
pytest warnings are pre-existing async-mock warnings in `test_real_dispatch.py`,
which only runs when `openai` is installed.

Regenerated after review: not yet.
