# Demo Agent (End-to-End)

This creates a real `traces.jsonl` file, triggers the loop guard, and shows replay.

## Run
```bash
python3 /Users/patrickhughes/Documents/New\\ project/sdk/examples/demo_agent.py
```

## Summarize traces
```bash
python3 -m agentguard.cli summarize /Users/patrickhughes/Documents/New\\ project/sdk/examples/traces.jsonl
```

## Human-readable report
```bash
python3 -m agentguard.cli report /Users/patrickhughes/Documents/New\\ project/sdk/examples/traces.jsonl
```

## Output
- `traces.jsonl` with reasoning, tool, and guard events
- `replay.jsonl` with request/response pairs
