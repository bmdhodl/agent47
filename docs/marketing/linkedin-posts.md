# LinkedIn Posts — "Why should anyone care that AI agents are unguarded?"

Ready to post. Space these out — one per week recommended.

---

## Post 1 — The problem statement

AI agents are getting more autonomy. But almost nobody is putting guardrails on them.

A LangChain agent gets a question it can't answer. It retries the same search. Again. And again. 200 times. Each retry costs tokens. Your API bill doesn't care that the agent was stuck.

A CrewAI workflow hits an edge case. One agent keeps delegating to another. Back and forth. A-B-A-B. For 4 minutes. You find out when you check Stripe.

These aren't hypothetical. They happen every day to teams running agents in production.

The fix isn't better prompts. It's runtime enforcement. Hard budget caps. Loop detection. Automatic kill switches.

I built AgentGuard for this. Zero dependencies, MIT licensed, works with LangChain/CrewAI/any Python agent. It stops agents mid-execution when they go off the rails.

It won't make your agents smarter. But it'll keep them from draining your account while being dumb.

https://github.com/bmdhodl/agent47

---

## Post 2 — Why zero dependencies matters

When I tell engineers AgentGuard has zero dependencies, they think it's a flex.

It's not. It's a security decision.

Every dependency you add to your AI agent stack is a supply chain risk. Every transitive package is an attack surface. And agent systems — which by design have access to tools, APIs, and sometimes databases — are the worst place to have vulnerable dependencies.

AgentGuard is pure Python stdlib. One package. One audit target. Nothing that can get hijacked in a left-pad scenario.

If you're building agents that touch production data, the libraries you put around them should be as minimal as possible.

Not because minimalism is cool. Because the blast radius of a compromised agent is enormous.

---

## Post 3 — What I learned building this

I've been building AgentGuard — runtime guardrails for AI agents. Here's what surprised me:

1. Most agent failures are boring. Not hallucinations. Just loops. Same tool, same arguments, over and over.

2. Cost visibility changes behavior. When engineers see a single run cost $3.40, they write better prompts. Because the number is right there.

3. Nobody budgets for agent costs. A single runaway agent can burn through a monthly allocation in minutes.

4. "Just add max_iterations" doesn't work. An agent doing 20 different things is fine. Doing the same thing 20 times is broken. Iteration caps can't tell the difference.

5. Guardrails are easier to add before you need them. After your first $50 incident, you're patching in a panic. Before it, you're adding 3 lines of code.

Open source, zero dependencies, works with any Python agent framework: https://github.com/bmdhodl/agent47
