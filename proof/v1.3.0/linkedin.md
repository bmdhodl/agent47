---
title: ""
excerpt: ""
---
I found a bug in my agent budget guard. It raised the right exception. LangChain logged it and ran the tool anyway.

The test in the picture sets the tool-call budget to zero. With AgentGuard 1.2.13, the tool still runs once. With 1.3.0, it stops before the tool body runs. Same tool. Same framework version. No model call needed to reproduce it.

I used Codex to audit the SDK and ship the fix. This release also adds budgets that persist between local processes and per-goal limits, plus fixes for invalid budget values, payment rollback, and HTTP trace delivery.

I checked a fresh PyPI install and sent a trace through the hosted dashboard, then read it back.

One caveat: the optional CrewAI dependency tree still carries unresolved ChromaDB advisories. The base SDK does not install it. Details are in the release notes.

Upgrade: pip install --upgrade agentguard47

https://github.com/bmdhodl/agent47/releases/tag/v1.3.0
