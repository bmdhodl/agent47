# AgentGuard — North Star

**Last reviewed:** 2026-09-18

## What it is

A zero-dependency Python SDK (plus two MCP surfaces and a static site) that
gives developers in-process stops for instrumented agent runs: recorded
budgets, loop detection, retries, and timeouts, with a local JSONL record of
why work stopped.

The hosted dashboard is a separate private product. This public repo does not
implement invoice caps, host-wide interception, or remote kill.

**SDK:** Runtime checks that raise exceptions at tested dispatch boundaries.
See [enforcement-boundary.md](../docs/enforcement-boundary.md) for which paths
are advisory, recorded-budget preflight, reservation-backed, or unsupported.

## Who it's for

Developers and small teams running Python agents or more than one coding-agent
host who need bounded calls, retries, time, or spend estimates without a
gateway. If a single provider's native cap already covers the workflow, use
that first.

## What problem it solves

Agents fail silently. They loop, overspend, and hang. AgentGuard intercepts
those failures **where you instrument them**: OpenAI Chat Completions and
Anthropic Messages patches refuse an exhausted **recorded** budget before the
next dispatch. That is not a guarantee against in-flight spend, missing usage,
concurrent overshoot, or a subscription invoice.

## Non-goals

1. **Not a framework.** We don't orchestrate agents. We guard whatever framework you already use.
2. **Not a full observability platform.** We are not LangSmith, Langfuse, or Helicone.
3. **Not a prompt engineering tool.** We don't evaluate prompt quality or optimize outputs.
4. **Not enterprise governance.** No RBAC, audit logs, or compliance features in V1.
5. **Not an invoice or quota controller.** Provider billing limits stay with the provider.
6. **Not a resurrected public dashboard.** Hosted control-plane work stays in the private repo.

## Repo Boundary

This public repo remains the SDK/MCP wedge: local runtime enforcement, local
proof, package metadata, examples, and release infrastructure. Hosted
dashboard work stays in the private dashboard repo.

The 2026 weekly plan ([#729](https://github.com/bmdhodl/agent47/issues/729))
is the planning authority. Preserve history; do not treat older Now/Next
tables as a second execution queue.
