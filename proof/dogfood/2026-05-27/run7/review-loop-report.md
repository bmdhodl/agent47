AgentGuard report
  Total events: 14
  Spans: 4  Events: 9
  Approx run time: 1.6 ms
  Reasoning steps: 0
  Tool results: 0
  LLM results: 0
  Estimated cost: $0.1020
  Known issue: this report double-counts review-loop cost on current main. The raw trace has three review.iteration costs totaling $0.0510, and guard.budget_exceeded stopped at $0.0510 > $0.0450.
  Savings ledger: exact 0 tokens / $0.0000, estimated 0 tokens / $0.0205
  Loop guard triggered: 0
  Guard events:
    guard.budget_exceeded: 1
    guard.retry_limit_exceeded: 1
  Incident hint: rerun with `agentguard incident` for a shareable incident report

Traced by AgentGuard | agentguard47.com
