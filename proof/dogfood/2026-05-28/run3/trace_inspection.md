# Trace Inspection

## Counts
- installed_agentguard_doctor_trace.jsonl: exists=True events=4 guard_events=0
- installed_agentguard_demo_traces.jsonl: exists=True events=36 guard_events=4
- repo_agentguard_doctor_trace.jsonl: exists=True events=4 guard_events=0
- repo_agentguard_demo_traces.jsonl: exists=True events=36 guard_events=4
- coding_agent_review_loop_traces.jsonl: exists=True events=14 guard_events=2

## Guard Events
- installed_agentguard_demo_traces.jsonl:16 guard.budget_warning ()
- installed_agentguard_demo_traces.jsonl:21 guard.budget_exceeded ()
- installed_agentguard_demo_traces.jsonl:27 guard.loop_detected ()
- installed_agentguard_demo_traces.jsonl:35 guard.retry_limit_exceeded ()
- repo_agentguard_demo_traces.jsonl:16 guard.budget_warning ()
- repo_agentguard_demo_traces.jsonl:21 guard.budget_exceeded ()
- repo_agentguard_demo_traces.jsonl:27 guard.loop_detected ()
- repo_agentguard_demo_traces.jsonl:35 guard.retry_limit_exceeded ()
- coding_agent_review_loop_traces.jsonl:6 guard.budget_exceeded (reason=Cost budget exceeded: $0.0510 > $0.0450 (this call added $0.0205); cost_usd=0.051; attempt=3)
- coding_agent_review_loop_traces.jsonl:13 guard.retry_limit_exceeded (reason=Retry limit exceeded: apply_patch attempted 4 times (limit: 3); attempt=4)
