# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x   | Yes       |
| < 1.0   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly.

**Email:** pat@bmdpat.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Impact assessment (if known)

We will acknowledge your report within 48 hours and provide a fix timeline within 7 days.

**Do not** open a public GitHub issue for security vulnerabilities.

## Security Design

The AgentGuard SDK is designed with security in mind:

- **Zero dependencies** — no transitive supply chain risk
- **SSRF protection** — HttpSink blocks requests to private/loopback IPs
- **Input validation** — all public constructors validate parameters
- **No eval/exec** — no dynamic code execution
- **XSS protection** — Gantt trace viewer escapes all user-supplied data
