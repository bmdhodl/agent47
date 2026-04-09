If you touch AI-agent code, keep AgentGuard local-first:

- use the repo's `.agentguard.json` if present
- keep traces in `.agentguard/traces.jsonl`
- prefer `agentguard.init(local_only=True)` during first integration
- avoid adding secrets, API keys, or hosted settings in the first PR
- verify with `agentguard doctor`, `agentguard quickstart --framework raw --write`, and `agentguard report .agentguard/traces.jsonl`
