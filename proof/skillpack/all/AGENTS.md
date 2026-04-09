Use AgentGuard in local-only mode first.

- Respect the repo's `.agentguard.json`
- Keep traces in `.agentguard/traces.jsonl`
- Prefer `agentguard.init(local_only=True)` for the first integration
- Do not add API keys or hosted dashboard settings in the first PR
- Verify with:
  1. `agentguard doctor`
  2. `agentguard quickstart --framework raw --write`
  3. `python agentguard_raw_quickstart.py`
  4. `agentguard report .agentguard/traces.jsonl`
