# Show HN Launch Plan

## Post Title

```
Show HN: AgentGuard – Stop AI agents from burning through your API budget (Python, MIT)
```

## Post URL

```
https://github.com/bmdhodl/agent47
```

## Post Text

```
Hi HN,

I built AgentGuard because my AI agent burned $200 in a single run. It got stuck in a loop calling GPT-4, and by the time I noticed, the damage was done. Every existing tool (LangSmith, Langfuse, Portkey) would have shown me a nice dashboard of the carnage — after the fact.

AgentGuard is different: it kills the agent mid-run.

**What it does:**

- BudgetGuard: set a dollar limit ($5, $50, whatever). Get a warning at 80%. Agent dies at 100%.
- LoopGuard: detects repeated tool calls and A-B-A-B patterns. Raises an exception.
- CostTracker: built-in pricing for GPT-4o, Claude, Gemini, Llama, etc. Updated monthly.
- Full tracing: JSONL output, spans, events, cost data. CLI reports and Gantt viewer.

**4 lines to stop runaway costs:**

    from agentguard import Tracer, BudgetGuard, patch_openai

    tracer = Tracer(guards=[BudgetGuard(max_cost_usd=5.00)])
    patch_openai(tracer)
    # Every OpenAI call is now tracked. Agent dies at $5.

**Technical choices:**

- Zero dependencies. Pure Python stdlib. No transitive supply chain risk.
- Works with LangChain, LangGraph, CrewAI, or raw OpenAI/Anthropic calls.
- MIT licensed. Free forever.
- Optional paid dashboard ($39/mo) for teams that want centralized monitoring and a remote kill switch.

The demo script in the repo (examples/demo_budget_kill.py) shows a simulated agent burning through a $1 budget and getting killed. No API keys needed to try it.

I'm a solo dev. This is the tool I wished existed when I was debugging agent cost blowouts at 2am. Happy to answer questions about the architecture, the cost tracking accuracy, or anything else.

GitHub: https://github.com/bmdhodl/agent47
PyPI: pip install agentguard47
Docs: https://agentguard47.com
```

## Timing

- **Best days:** Monday-Wednesday
- **Best time:** 8-10 AM ET (HN peak)
- **Avoid:** Fridays, weekends, holidays

## Pre-Launch Checklist

- [ ] `pip install agentguard47==1.2.1` works
- [ ] README hero is cost guardrail (done)
- [ ] Demo GIF embedded in README (need to record with VHS)
- [ ] All README links resolve (no 404s)
- [ ] `examples/demo_budget_kill.py` runs without API keys
- [ ] Repo description updated (done)
- [ ] Topics include cost-control, budget-enforcement (done)
- [ ] FUNDING.yml created (done)
- [ ] GitHub Discussions enabled (done)
- [ ] Landing page (agentguard47.com) loads and pricing is correct

## Post-Launch (first 4 hours)

1. **Monitor comments** — respond to every question within 30 minutes
2. **Technical questions** — give honest, specific answers. Show code.
3. **Criticism** — acknowledge it. "Good point, I should add X" wins more than defending.
4. **"How is this different from X?"** — Focus on what AgentGuard does that X doesn't (hard budget enforcement, kill switch). Don't trash competitors.
5. **Ask friends/colleagues to upvote** — first 30 minutes matter most for ranking

## Alternate Titles (if main doesn't perform)

- `Show HN: I open-sourced the tool I built after my AI agent burned $200 in one run`
- `Show HN: AgentGuard – Runtime budget enforcement for AI agents (kills them at $5)`
- `Show HN: Zero-dependency Python SDK that kills AI agents when they exceed spend limits`

## Distribution After HN

If the post gets traction (50+ points):

1. **Cross-post to Reddit:** r/MachineLearning, r/LangChain, r/LocalLLaMA
2. **Tweet thread:** Problem → solution → demo GIF → link
3. **LangChain Discord:** Share in #showcase
4. **Dev.to / Hashnode:** "How I built runtime cost guardrails for AI agents"
5. **LinkedIn:** Technical post targeting AI/ML engineering managers
