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
