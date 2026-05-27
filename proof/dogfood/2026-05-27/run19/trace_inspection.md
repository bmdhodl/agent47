# Trace inspection

Generated: 2026-05-27T21:38:02.225241+00:00

## agentguard_doctor_trace.jsonl
- total_events: 4
- guard_events: none

## agentguard_demo_traces.jsonl
- total_events: 36
- guard_events: guard.budget_warning, guard.budget_exceeded, guard.loop_detected, guard.retry_limit_exceeded

## coding_agent_review_loop_traces.jsonl
- total_events: 14
- guard_events: guard.budget_exceeded, guard.retry_limit_exceeded

## Concrete enforcement observed
- agentguard_demo_traces.jsonl: `guard.budget_warning` - {"cost_used": 0.84, "limit_usd": 1.0}
- agentguard_demo_traces.jsonl: `guard.budget_exceeded` - Cost budget exceeded: $1.0800 > $1.0000 (this call added $0.1200)
- agentguard_demo_traces.jsonl: `guard.loop_detected` - Loop detected: tool.search({"query":"python asyncio"}) repeated 3 times in last 6 calls. Consider varying the arguments or breaking the loop.
- agentguard_demo_traces.jsonl: `guard.retry_limit_exceeded` - Retry limit exceeded: fetch_docs attempted 3 times (limit: 2)
- coding_agent_review_loop_traces.jsonl: `guard.budget_exceeded` - Cost budget exceeded: $0.0510 > $0.0450 (this call added $0.0205)
- coding_agent_review_loop_traces.jsonl: `guard.retry_limit_exceeded` - Retry limit exceeded: apply_patch attempted 4 times (limit: 3)
