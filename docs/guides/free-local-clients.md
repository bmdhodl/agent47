# Explicit free local clients

This option is in the unpublished AgentGuard **1.4.1 candidate**. Published
1.4.0 needs the [manual-accounting example](../../examples/local_cost_manual.py).

Create the OpenAI-compatible client first, then declare that exact instance
free when you activate the patch:

```python
from openai import OpenAI
from agentguard import BudgetGuard, JsonlFileSink, Tracer, patch_openai

local = OpenAI(base_url="http://127.0.0.1:11434/v1", api_key="ollama")
budget = BudgetGuard(max_tokens=3000, max_calls=10)
tracer = Tracer(sink=JsonlFileSink("traces.jsonl"))
patch_openai(tracer, budget_guard=budget, free_local_clients=[local])
local.chat.completions.create(model="qwen3.5:4b", messages=[{"role": "user", "content": "Hi"}])
```

The named client's model calls record `provider="local"`, cost source `zero`,
and zero model cost. Actual usage still feeds token and call limits. JSONL,
`agentguard report` and `agentguard incident` retain that zero cost. Unnamed
clients keep OpenAI accounting, including unknown-model estimates and clients
with the same base URL or model. This is your explicit billing declaration;
it does not detect localhost, verify provider billing, or account for electricity
and hardware. A dollar-only cap cannot bound a free loop. A shared guard still
refuses any next call when its recorded budget is already exhausted.

Use `patch_openai_async(..., free_local_clients=[async_client])` for
`AsyncOpenAI` clients. Each patch accepts only its matching client kind.
`agentguard.init(free_local_clients=[local, async_client], local_only=True)`
accepts both kinds and activates both patches; `auto_patch=False` with a
nonempty list raises `ValueError`. `local_only=True` selects local trace output;
the free-client list selects billing. Both are independent options.

Provide the complete iterable at activation. Repeated patch calls keep the
original tracer, guard and client declarations. Call `unpatch_openai()` /
`unpatch_openai_async()` before a new activation, or `shutdown()` before a new
`init()`. A copied client or a client created later is a new instance and is
paid by default. The declarations use weak references and do not keep clients
alive. Wrong client kinds, invalid entries and clients without weak-reference
support raise `TypeError` before activation. A nonempty list requires the
optional OpenAI SDK and its standard resource classes.

The option covers the existing sync/async Chat Completions and Responses
patches, including `responses.parse`, completed streams and raw response
helpers. Existing resources are covered, but bound methods and raw/streaming
helpers saved before activation must be recreated. Custom resource classes
and instance-level overrides remain outside the
[enforcement boundary](../enforcement-boundary.md).

Store-backed sync non-stream calls and store-backed streams reserve zero
dollars for a named client. Token caps still require an explicit request token
bound; paid clients still require dollar bounds. Interrupted or missing-usage
streams retain their existing unresolved token/call holds. Async non-stream
calls and in-memory guards keep recorded-budget preflight. These limits do not
guarantee provider invoices or prevent all in-flight token overshoot.
