"""Policy configuration for the local-first agent template.

One place to set every AgentGuard knob the example uses: budget caps, the
rate limit, the tool allowlist, and where the JSONL audit log is written.

Copy this file into your own project and adjust the numbers. Nothing here
talks to a hosted service -- the local-first template runs against a model
server on your own machine.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class AgentPolicy:
    """Everything the agent loop is allowed to do, in one object."""

    # --- Model server ---
    # llama.cpp (`llama-server`) and Ollama both expose an OpenAI-compatible
    # chat endpoint. Point base_url at yours; the path is appended by the loop.
    base_url: str = "http://localhost:8080"
    model: str = "local-model"

    # --- Budget ---
    # Token cap is the real guardrail for a local model (electricity, not API
    # dollars). max_calls stops a runaway loop. The cost cap is near-zero so
    # the BudgetGuard cost field still has meaning if you swap in a paid model.
    max_tokens: int = 4_000
    max_calls: int = 12
    max_cost_usd: float = 0.50
    warn_at_pct: float = 0.8

    # --- Rate limit ---
    # Sliding-window cap. A local 8B model on consumer hardware does not love
    # being hammered; this also protects a shared dev box.
    max_calls_per_minute: int = 30

    # --- Tool allowlist ---
    # The agent may only call tools named here. Anything else is denied and
    # logged. Keep this tight: it is the difference between a helpful agent
    # and one that runs `rm -rf` because the model hallucinated a tool.
    allowed_tools: List[str] = field(default_factory=lambda: ["read_file"])

    # --- Audit log ---
    audit_log_path: str = "local_first_template_traces.jsonl"

    @classmethod
    def from_env(cls) -> "AgentPolicy":
        """Build a policy, letting env vars override the model-server fields.

        AGENTGUARD_LOCAL_BASE_URL and AGENTGUARD_LOCAL_MODEL let you point the
        same example at a real server without editing code.
        """
        return cls(
            base_url=os.environ.get("AGENTGUARD_LOCAL_BASE_URL", cls.base_url),
            model=os.environ.get("AGENTGUARD_LOCAL_MODEL", cls.model),
        )
