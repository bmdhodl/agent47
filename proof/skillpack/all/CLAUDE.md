When integrating AgentGuard:

- start local-only
- respect the repo's `.agentguard.json`
- keep traces in `.agentguard/traces.jsonl`
- prefer `agentguard.init(local_only=True)` on the first pass
- do not add API keys or dashboard settings in the first PR
- prove the wiring with:
  1. `agentguard doctor`
  2. `agentguard quickstart --framework raw --write`
  3. `python agentguard_raw_quickstart.py`
  4. `agentguard report .agentguard/traces.jsonl`
