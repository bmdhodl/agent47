# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 1.1.x   | Yes                |
| 1.0.x   | Security fixes only |
| < 1.0   | No                 |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly.

**Email:** pat@bmdpat.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment (if known)

**Do not** open a public GitHub issue for security vulnerabilities.

## Disclosure Timeline

- **Acknowledgment:** Within 48 hours of report
- **Triage:** Within 7 days
- **Fix:** Target 30 days for critical, 90 days for others
- **Disclosure:** Coordinated with reporter, following 90-day standard

## Scope

This policy applies to:
- The `agentguard47` PyPI package
- The `bmdhodl/agent47` GitHub repository
- The `sdk/agentguard/` source directory

Out of scope:
- Third-party integrations (LangChain, OpenAI, etc.)
- The AgentGuard dashboard (separate security policy)

## Agent Threat Classes

AgentGuard is an in-process runtime guardrail. It is not a filesystem sandbox,
container runtime, or host isolation layer. These threat classes are in scope
for documentation and examples because they affect autonomous coding-agent
blast radius:

- **Sandbox escape via symlink traversal.** CVE-2026-39861 /
  GHSA-vp62-r36r-9xqp showed a Claude Code sandbox escape where a sandboxed
  process could create a symlink that the unsandboxed app later followed,
  allowing writes outside the workspace. AgentGuard does not prevent symlink
  traversal or replace sandbox path validation. `BudgetGuard`, `LoopGuard`,
  `RetryGuard`, `TimeoutGuard`, and session-scoped tracing can still limit how
  long a compromised or prompt-injected autonomous run keeps acting.
- **Provider-managed background work.** Managed-agent systems can add work
  outside the traced application process, such as scheduled memory refinement,
  external graders, or multi-agent orchestration. AgentGuard only enforces
  limits on code paths that run through its tracers and guards. Provider
  console limits and billing alerts remain required for provider-managed
  background phases until explicit integration support exists.
- **Device egress interception as a governance layer.** On-device interceptors
  install a per-device CA, decrypt a listed set of provider hosts, and route
  model and MCP calls through a gateway that logs and enforces policy. They
  reach apps AgentGuard cannot instrument. Check the interceptor's failure
  mode before you rely on its cap: [aitori](https://github.com/truefoundry/aitori)
  fails open, so with no gateway configured, or with the gateway unavailable,
  the request still reaches the provider. Treat a cap enforced only there as
  advisory during an outage, and keep an in-process guard on the code you own.
  AgentGuard neither replaces nor depends on such a layer, and it never
  terminates TLS or adds a trust anchor. See
  [docs/competitive/aitori.md](docs/competitive/aitori.md).

## Security Design

The AgentGuard SDK is designed with security in mind:

- **Zero dependencies** — no transitive supply chain risk
- **SSRF protection** — HttpSink blocks requests to private/loopback IPs, validates redirect targets
- **HTTP header injection prevention** — API keys validated against CRLF injection
- **Input validation** — all public constructors validate parameters
- **Event data size limits** — 64 KB max per event to prevent OOM
- **Thread safety** — all guards and sinks use locks for concurrent access
- **No eval/exec** — no dynamic code execution
- **XSS protection** — Gantt trace viewer escapes all user-supplied data
- **IDN/Punycode normalization** — prevents Unicode SSRF bypasses
