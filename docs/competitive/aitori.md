# AgentGuard vs aitori

This is a living positioning doc. It compares AgentGuard (in-process Python
SDK) with aitori (on-device AI traffic interceptor). Last updated: 2026-07-28.

## Why this comparison exists

[aitori](https://github.com/truefoundry/aitori) is an agent that runs on a
machine and intercepts the AI traffic leaving it. It routes model and MCP calls
from apps and command-line tools to a gateway that logs them, budgets them, and
checks them against policy. Everything else passes through untouched. It is
Apache-2.0 and written in Go; the repo was created 2026-06-25.

Its pitch overlaps with AgentGuard's on two words: budget and policy. The
architectures do not overlap at all. aitori governs traffic at the machine's
egress. AgentGuard guards behavior inside the agent's process. Naming that
boundary is the point of this doc: each tool covers the gap the other leaves.

## Comparison

| Axis | AgentGuard | aitori |
|------|-----------|--------|
| **Enforcement point** | In-process, at the call site, before or at the moment the limit is crossed. | Device egress, in a separate process, after the agent decided to call. |
| **Deployment model** | `pip install agentguard47`. Zero runtime dependencies. | Elevated install of a binary, a per-device CA, and a system proxy change. |
| **TLS handling** | None. AgentGuard never terminates TLS or reads provider traffic. | Terminates TLS for the listed hosts with a device-local CA. |
| **Behavior when the enforcement layer fails** | No separate layer to fail. A tripped guard raises in the agent's process. | Fails open. Requests reach the provider when no gateway is configured or the gateway is down. |
| **Coverage** | Only code you instrument. | Apps on the machine whose hosts you list, including closed apps and browsers. |
| **Loop and retry detection** | First-class. `LoopGuard`, `RetryGuard`. Sees the agent's call graph. | Not documented. A gateway sees requests, not the agent's call graph. |
| **Audit trail** | Local JSONL traces you own. No network calls unless you opt into a network sink. | Gateway-side log, plus a local live view on `127.0.0.1:9100`. |
| **Scope of trust added** | The Python process already running your agent. | The machine's TLS trust store, plus the gateway. |
| **License** | MIT. | Apache-2.0. |

## aitori's interception boundary

The interception boundary is the device, not the application and not the
provider. To get there aitori does four things, per its own README:

1. Installs a per-device certificate authority into the machine's trust store
   and points the system proxy at itself. On macOS and Linux both steps run
   under `sudo`.
2. Decrypts only the hosts listed in its config. Built-in profiles cover Claude
   Code, Claude Desktop, claude.ai, and chatgpt.com. Unlisted hosts are never
   decrypted.
3. Classifies each decrypted request. Model and MCP calls go to the configured
   gateway; anything else goes straight to the real upstream.
4. Returns the provider's response to the app unchanged. The app talks to the
   same endpoint with the same key and never knows.

That boundary reaches something AgentGuard cannot: traffic from software you
cannot instrument. A browser on claude.ai has no setting that points it at a
gateway, and no SDK you can import into it. If the requirement is "see and
govern every model call leaving this laptop, including the ones from closed
apps," device egress is the only place left to stand.

## What governing at egress costs

**aitori fails open.** With no gateway configured it inspects traffic and
passes it through. With a gateway configured, the README states that if the
gateway is unavailable the request still reaches its original destination.

That is a defensible availability choice for a tool sitting in the path of
every app on a developer's machine. It also means the enforcement is only as
available as the gateway. During an outage the calls keep flowing, the budget
stops being checked, and the log gains a hole. A cap that lives at the gateway
is an advisory cap during the exact window an incident is most likely to be
running. The other direction breaks availability, not spend: `sudo aitori down`
reverts the system proxy, and if the process is killed without it, the proxy
stays pointed at a stopped listener and traffic breaks until someone runs
`down` by hand.

**Reading TLS you did not terminate requires becoming a trust anchor.** aitori
is explicit about most of what that costs, and they are the right tradeoffs to
weigh:

- A new CA lands in the machine's trust store. aitori generates the private key
  per device and it never leaves, so there is no fleet-wide key to steal, but
  that machine now trusts a locally held CA for the listed hosts.
- Interception also implies a plaintext copy. Prompts, tool arguments, and
  request headers exist in a second process on the box. Anything that reads
  that process, or the live UI on `127.0.0.1:9100`, reads the contents of the
  calls. The README does not spell this out; it follows from the design.
- `aitori ca remove` is a separate step from `aitori down`, so an incomplete
  uninstall leaves the CA installed.
- The README states the model plainly: it assumes the machine is cooperating, a
  local administrator can bypass it, and it is a governance tool, not a
  sandbox.

None of that makes aitori unsafe. That is the standard cost of interception,
and aitori keeps it small by decrypting only listed hosts with a device-local
key. AgentGuard has no such cost, because it never terminates TLS.

## How AgentGuard's enforcement differs

AgentGuard enforces in-process, at the call site, in the agent's own runtime.
No proxy, no CA, no trust-store change, no elevation, no second process holding
plaintext. No gateway can be unavailable either, so the guarded path has no
fail-open mode: when a guard raises, the run stops unless your own code
swallows the exception.

The timing matters, so here is what "stops" means:

- `LoopGuard.check(tool_name, tool_args)` and `TimeoutGuard.check()` run before
  dispatch. They raise `LoopDetected` or `TimeoutExceeded` and the call is
  never made.
- `BudgetGuard.consume()` accounts for a call that completed and raises
  `BudgetExceeded` at the moment the limit is crossed. The call that crossed
  the line already happened; the run halts before the next one.

A gateway is not positioned to make either decision. It sees requests, not the
agent's call graph, so it cannot tell the eightieth identical
`search_docs("refund policy")` from the first, and it cannot stop a retry storm
where every individual request looks correct. aitori's README does not document
loop or retry detection.

AgentGuard's own limit is just as real: **it only enforces on code paths that
run through its tracers and guards.** A closed desktop app, a browser tab, a
subprocess you did not instrument, or provider-managed background work is
invisible to it. That is recorded in
[SECURITY.md](../../SECURITY.md#agent-threat-classes), and it is exactly the
ground aitori covers.

## When aitori is the right choice

If the question is "what model traffic is leaving this laptop or this fleet,"
and the answer has to include apps you cannot modify, aitori is the tool. No
in-process SDK reaches a browser tab. Interception is the only lever there.

## When AgentGuard is the right choice

If the question is "can this agent loop, retry, or burn a budget while it
runs," AgentGuard is the tool. It runs wherever the agent runs: a laptop, CI,
bare metal, a local Ollama, or air-gapped.

## They compose

These are not substitutes. aitori gives visibility and gateway policy across
software you do not control. AgentGuard gives runtime limits inside software
you do. Run both. An in-process guard covers the gateway's fail-open window,
and egress interception covers the code you never instrumented.

## Summary

aitori = **traffic governance** at the device boundary, fail-open, bought with
a trust-store change.
AgentGuard = **runtime behavior guard** at the process boundary, fail-closed on
the paths it covers, bought with an import.
