# inbox/ — Agent Work Request Path

**PUBLIC REPO — never write sensitive business data here.**
**This inbox is for AI agents to request work from the AgentGuard SDK codebase.**

## Purpose

Agents (Codex sessions, external tools, co-founder standup) write work requests here.
The AgentGuard SDK Builder reads this inbox before each Codex session and prioritizes accordingly.

## Format

File name: `YYYY-MM-DD-<requester>.md`

## Required Header

```
---
from: <agent-name>
date: YYYY-MM-DD
type: feature-request | bug | docs | refactor | release
priority: P1 | P2 | P3
---
```

## Content Guidelines

- Describe what you need, not how to implement it
- Include why it matters to the business or users
- Reference PyPI download data or user feedback if relevant
- No internal business data (revenue, pipeline, customer names)

## What Happens After

SDK Builder reads inbox/ at session start, prioritizes tasks, executes highest priority first, then writes result to context/outbox/standup/ for co-founder review.
