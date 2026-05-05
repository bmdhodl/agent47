# AgentGuard skills

Packaged AgentGuard skills for AI coding agent harnesses.

| Format | File | Use with |
|---|---|---|
| Anthropic / Claude Code | [`agentguard/SKILL.md`](./agentguard/SKILL.md) | Claude Code, claude.ai skills, Anthropic SDK |
| Codex | [`codex/agentguard.md`](./codex/agentguard.md) | Codex CLI, OpenAI agent harnesses |

The canonical reference is the root [`SKILL.md`](../SKILL.md). The files in this folder are terser, harness-specific entry points that link back to the canonical doc.

## Install

All skills install AgentGuard the same way:

```bash
pip install agentguard47
agentguard doctor
```

Python 3.9+. Zero dependencies for the core. Optional extras for LangChain, LangGraph, CrewAI.
