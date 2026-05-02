# AgentGuard Proof Gallery

These are local, runnable proof paths for the public SDK. Use them in demos,
issues, discussions, launch posts, and first-run validation.

No hosted dashboard or API key is required unless a command explicitly says so.

## 1. Offline Guard Demo

```bash
pip install agentguard47
agentguard demo
```

Proves:

- `BudgetGuard` stops simulated spend
- `LoopGuard` stops repeated tool calls
- `RetryGuard` stops retry storms
- no network calls are required

Expected stop condition:

```text
Local proof complete.
```

## 2. Coding-Agent Review Loop

```bash
python examples/coding_agent_review_loop.py
agentguard incident coding_agent_review_loop_traces.jsonl
```

Proves:

- repeated review/edit attempts can burn budget
- stuck patch retries are stopped locally
- the same trace can become an incident report

Sample incident:
[`docs/examples/coding-agent-review-loop-incident.md`](coding-agent-review-loop-incident.md)

## 3. Token-Budget Spike

```bash
python examples/per_token_budget_spike.py
agentguard report per_token_budget_spike_traces.jsonl
```

Proves:

- one oversized context or completion can exceed a run budget
- the SDK can price a local synthetic turn without provider credentials
- spend control is not only about loop count

Expected stop condition:

```text
Cost budget exceeded:
```

## 4. Decision Trace Workflow

```bash
python examples/decision_trace_workflow.py
agentguard decisions decision_trace_workflow.jsonl
```

Proves:

- agent proposals can be captured as `decision.proposed`
- human edits and overrides can carry reason/comment fields
- approval and binding outcomes use the normal trace pipeline

Expected event types:

```text
decision.proposed
decision.edited
decision.approved
decision.bound
```

## 5. Budget-Aware Escalation

```bash
python examples/budget_aware_escalation.py
```

Proves:

- apps can keep a cheaper default model
- hard turns can be marked for escalation by deterministic rules
- the SDK advises without hiding provider routing inside AgentGuard

Expected stop condition:

```text
Escalation reason: token_count 2430 exceeded 2000
```

## 6. Starter File Smoke Test

```bash
agentguard quickstart --framework raw --write
python agentguard_raw_quickstart.py
agentguard report .agentguard/traces.jsonl
```

Proves:

- a new repo can get a runnable local integration in one command
- generated starters write traces to `.agentguard/traces.jsonl`
- first value does not require a dashboard account

## What To Share

The most shareable public demo is the coding-agent review loop:

```bash
python examples/coding_agent_review_loop.py
agentguard incident coding_agent_review_loop_traces.jsonl
```

It maps directly to the product wedge: a coding agent gets stuck reviewing and
retrying, then AgentGuard stops the run before it keeps burning tokens.
