# Hacker News "Show HN" Post

## Title

Show HN: AgentGuard – Lightweight guardrails for AI agents (loop detection, budget limits)

## Body

I've been building AI agents for the past few months and kept running into the same runtime issues: agents would loop infinitely, burn through API budgets overnight, and fail in ways that were nearly impossible to debug or reproduce.

**The problem:** AI agents fail differently than normal software. They enter infinite tool-call loops (calling the same function with identical arguments repeatedly), cascade failures silently across multiple agents, and produce nondeterministic bugs that you can't reproduce. The existing tooling either locks you into a specific model provider (OpenAI/Anthropic), couples tightly to a framework (LangChain/LlamaIndex), or requires a commercial platform subscription.

**What AgentGuard does:** It's a lightweight Python SDK that gives you runtime observability and safety checks for agents:

- **Tracing**: Captures agent reasoning steps, tool calls, and LLM interactions in structured JSONL
- **Loop detection**: Stops execution if the same tool is called repeatedly with identical arguments
- **Budget guards**: Enforces token limits and max API calls to prevent runaway costs
- **Timeout guards**: Enforces wall-clock time limits for long-running agents
- **Replay**: Records runs and replays them deterministically for testing and debugging

Here's what it looks like:

```python
from agentguard import Tracer, LoopGuard, BudgetGuard

tracer = Tracer()
loop_guard = LoopGuard(max_repeats=3)
budget_guard = BudgetGuard(max_tokens=100000, max_calls=500)

with tracer.trace("agent.run") as span:
    span.event("reasoning.step", data={"thought": "search documentation"})
    loop_guard.check(tool_name="search", tool_args={"query": "agent loops"})
    budget_guard.consume(tokens=150, calls=1)
```

**Why it's different:**

- **Zero dependencies**: Pure stdlib Python, no cloud services, no API keys required
- **Model-agnostic**: Works with OpenAI, Anthropic, Ollama, llama.cpp, or any other backend
- **Framework-agnostic**: Works with LangChain, CrewAI, AutoGen, or custom agent architectures
- **MIT licensed**: Use it however you want

**Current state:** Published on PyPI as `agentguard47`. Has LangChain callback handler integration. Early stage and looking for feedback on what other runtime issues people are hitting with agents.

Install: `pip install agentguard47`

Repo: https://github.com/bmdhodl/agent47

I'm building this solo as an open-source foundation with plans for an optional hosted dashboard later. Would love feedback from anyone building autonomous agents and dealing with reliability issues.

---

## Anticipated HN Comments & Responses

### Comment: "Why not just use LangSmith / OpenAI's observability tools?"

**Response:**

Good question. LangSmith is great if you're all-in on LangChain and don't mind the vendor lock-in. OpenAI's tools only work with OpenAI models. AgentGuard is designed to be model-agnostic and framework-agnostic.

The core insight is that loop detection, budget guards, and timeouts are runtime concerns that apply regardless of which LLM or framework you're using. You should be able to run agents locally with Ollama and still get observability without sending telemetry to a third party.

Also, AgentGuard is MIT licensed and has zero dependencies. You can fork it, modify it, and run it entirely locally. The hosted dashboard I'm planning is optional, not required.

### Comment: "This is trivial to build yourself in 50 lines of code."

**Response:**

You're right that the core loop detection logic is simple (literally just tracking tool calls and arguments). But the value is in the interface design and the integrations.

Writing your own ad-hoc loop detection for every project means you end up with slightly different implementations across codebases, no standardization, and no ecosystem. AgentGuard gives you a consistent API, structured trace output, framework integrations, and CLI tools.

It's similar to why people use logging libraries instead of just printing to stdout. Yes, you could build it yourself. But having a standard tool that everyone uses makes debugging and sharing knowledge easier.

### Comment: "How is this different from OpenTelemetry?"

**Response:**

OpenTelemetry is designed for distributed systems and microservices. It's powerful but heavyweight and has a steep learning curve. AgentGuard is focused specifically on AI agent runtime concerns: loop detection, reasoning step capture, budget enforcement, and deterministic replay.

That said, AgentGuard's trace format is simple JSONL. If you want to bridge to OpenTelemetry for broader observability, you absolutely can. The two tools solve different problems and can coexist.

### Comment: "Agents are overhyped. This is just LLM API calls with extra steps."

**Response:**

Fair take. But whether you call them "agents" or "LLM-driven workflows," the runtime failure modes are real. I've personally burned hundreds of dollars on infinite loops and have talked to dozens of developers dealing with the same issues.

The terminology is debatable, but the problem space is concrete: if you're building systems where an LLM decides which functions to call next, you need runtime safety checks. That's what AgentGuard provides.

### Comment: "What about PII / sensitive data in traces?"

**Response:**

Great question. By default, AgentGuard writes traces to local JSONL files, so you control where the data goes. If you're logging sensitive information, you should either sanitize it before passing to the tracer or restrict access to the trace files.

The hosted dashboard I'm planning will be optional and will support self-hosting for exactly this reason. Enterprises won't send PII to a third-party SaaS, so the architecture needs to support on-premise deployment.

### Comment: "How do you handle non-deterministic LLM responses in replay mode?"

**Response:**

Replay mode records the actual responses from LLM calls and tool executions, then plays them back verbatim during replay. This makes tests deterministic even though the LLM itself is non-deterministic.

The tradeoff is that you're testing the agent logic (did it make the right tool calls given these LLM responses?), not the LLM itself. But that's usually what you want for regression testing. You record a "golden run" and then ensure that future code changes don't break the agent's decision-making logic.

### Comment: "What's the performance overhead?"

**Response:**

Minimal. Tracing is just appending JSON to a file. Loop detection is a hash map lookup. Budget guards are incrementing counters. I haven't done formal benchmarks, but in my testing, the overhead is negligible compared to the network latency of LLM API calls.

If you're concerned about performance, you can also disable tracing in production or sample traces (e.g., only trace 10% of runs).

### Comment: "This looks like it only detects exact argument matches. What about semantic loops?"

**Response:**

You're right. The current loop detection is syntactic (exact match on tool name and arguments). Semantic loop detection (e.g., the agent is searching for variations of the same query) is on the roadmap but requires embedding-based similarity checks, which adds dependencies.

For now, exact-match loop detection catches the most common failure mode (agent literally calling the same function with identical args). Semantic loops are rarer but definitely a real problem. Open to ideas on how to implement this without adding heavy dependencies.

### Comment: "Why not just use max_iterations in LangChain?"

**Response:**

`max_iterations` is a global limit on the agent's total steps. It prevents runaway execution, but it doesn't distinguish between productive steps and repeated steps.

LoopGuard is more precise: it detects when the agent is calling the same tool repeatedly with identical arguments, which usually indicates a stuck agent. You can have a long-running agent with many steps (high max_iterations) but still catch loops early.

They solve related but different problems. You might use both.

### Comment: "Are you planning to make money from this? What's the business model?"

**Response:**

The SDK is MIT licensed and will remain free forever. The business model is an optional hosted dashboard with team collaboration features, advanced analytics, and integrations (think Sentry for agents).

The strategy is to build a widely-used open-source tool, then offer a commercial layer for teams that want hosted infrastructure. Solo devs and small teams can use the open-source SDK indefinitely.

### Comment: "I'd use this if it supported JavaScript / TypeScript."

**Response:**

That's good signal. The current implementation is Python because that's where most agent frameworks are (LangChain, CrewAI, AutoGen). But a TypeScript port is feasible and on the roadmap if there's demand.

Would you use a JS/TS version? What frameworks would you want it to integrate with (LangChain.js, others)?
