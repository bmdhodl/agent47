# Launch Post Drafts

## LinkedIn / X (short)
Built a tiny observability SDK for AI agents.

It traces reasoning steps, catches tool loops, and replays runs deterministically.
Self-hosted, OSS-first, built for solo builders.

Demo output:
AgentGuard report
  Total events: 21
  Spans: 6  Events: 15
  Approx run time: 1.3 ms
  Reasoning steps: 6
  Tool results: 3
  LLM results: 3
  Loop guard triggered: 3 time(s)

Early access (dashboard pilot): https://github.com/bmdhodl/agent47

## Hacker News (technical)
Title idea: "AgentGuard: OSS observability SDK for multi-agent systems"

Body:
I built a minimal SDK that traces reasoning, detects loop failures, and replays runs deterministically. It emits JSONL traces, has guardrails for tool loops, and includes a LangChain integration stub. There’s a one-command demo and an E2E test script. Looking for early users to stress test the reliability layer.

Demo output (from local run):
AgentGuard report
  Total events: 21
  Spans: 6  Events: 15
  Approx run time: 1.3 ms
  Reasoning steps: 6
  Tool results: 3
  LLM results: 3
  Loop guard triggered: 3 time(s)

Repo/landing: https://github.com/bmdhodl/agent47
