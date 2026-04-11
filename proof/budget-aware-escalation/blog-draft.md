# Draft Blog Hook

Local Llama should not have to lose every hard turn.

`BudgetAwareEscalation` gives AgentGuard users a portable version of the advisor pattern: keep a cheap local model on by default, watch for token blowups, low confidence, or deep tool chains, and then hand the next turn to a stronger model only when it matters. The SDK does not hide provider routing inside a patcher or force a hosted workflow. It gives you a runtime-safe decision point you can wire into Ollama, Claude, OpenAI-compatible endpoints, or your own client stack. The worked example in this PR shows the exact shape: local Llama first, Claude only when the trace says the turn is getting expensive or shaky.
