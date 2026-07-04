# Local-first agent template

A minimal, framework-free agent loop that runs against a **local** model
server while AgentGuard enforces a budget cap, a rate limit, and a tool
allowlist -- and writes a JSONL audit log of every decision.

Use this as a copy-paste starting point when your model runs on hardware you
own (llama.cpp, Ollama, LM Studio) and there is no hosted provider to stop a
runaway loop for you.

## What it shows

- A hand-rolled agent loop -- no LangChain, no CrewAI, nothing to learn.
- `BudgetGuard` capping tokens and calls, warning at 80%.
- `RateLimitGuard` checked before every model call.
- A tool allowlist: the agent may only call `read_file`; an attempt to call
  `run_shell` is denied and logged.
- A `JsonlFileSink` audit log -- one line per model call, tool call, and guard
  decision.

## Run it

Offline is the default. It uses a deterministic canned model reply, so it
needs **no model server, no GPU, and no network** -- this is also what CI runs:

```bash
pip install agentguard47
python examples/local-first-template/agent.py
agentguard report local_first_template_traces.jsonl
```

Expected: turn 1 attempts a disallowed tool (denied), turn 2 uses `read_file`,
turn 3 produces the final answer. The audit log captures all of it.

## Run it against a real local model

Start an OpenAI-compatible server first. Both of these expose
`POST /v1/chat/completions`:

```bash
# llama.cpp
llama-server -m ./model.gguf --port 8080

# or Ollama (default port 11434)
ollama serve
```

Then point the example at it:

```bash
AGENTGUARD_LOCAL_DEMO=live \
AGENTGUARD_LOCAL_BASE_URL=http://localhost:8080 \
AGENTGUARD_LOCAL_MODEL=llama3.1:8b \
python examples/local-first-template/agent.py
```

The loop is identical in both modes -- only the model call differs.

## Swap models

Everything tunable lives in `config.py`:

- `base_url` / `model` -- which server and model (or set the env vars above).
- `max_tokens`, `max_calls`, `max_cost_usd`, `warn_at_pct` -- the budget.
- `max_calls_per_minute` -- the rate limit.
- `allowed_tools` -- the tool allowlist. Keep it tight.

Any server that speaks the OpenAI chat-completions shape works without code
changes. On a Mac, an MLX-based server (e.g. `mlx_lm.server`) exposes the same
endpoint and works the same way -- point `AGENTGUARD_LOCAL_BASE_URL` at it.

## Honest limits

- The offline reply is canned. It exists to make the example testable, not to
  simulate a real model's reasoning. Run in `live` mode for real behavior.
- Tool-call parsing here is a simple `TOOL_CALL: name {json}` convention, not a
  production protocol. Real loops should use the model's native tool/function
  calling. The AgentGuard wiring -- budget, rate, allowlist, audit -- is the
  part meant for reuse.
- Local models still cost electricity and time. The token budget is the real
  guardrail; the dollar cap is near-zero and only matters if you later swap in
  a paid model.
- No GPU is required to run the example. Running a real local model at usable
  speed usually does need one.
