# Try an AgentGuard release without API keys

An agent repeating a tool call or retrying forever can waste time and tokens.
This example shows three limits stopping simulated work. It runs locally and
needs no provider account.

## Install the version in your release email

Run the pinned install command from the email or the
[release page](https://github.com/bmdhodl/agent47/releases).
Use a new directory: the demo writes `agentguard_demo_traces.jsonl` and replaces
that file on another run. A fresh Python virtual environment keeps the example
separate from your projects.

```bash
python -m agentguard.cli demo --feedback
python -m agentguard.cli report agentguard_demo_traces.jsonl
```

The trace should contain all three events:

| Event | What happened in this example |
| --- | --- |
| `guard.budget_exceeded` | Simulated usage passed the configured budget. |
| `guard.loop_detected` | Repeated work reached the loop limit. |
| `guard.retry_limit_exceeded` | Repeated failures reached the retry limit. |

Before sending a release email, the workflow installs the exact published PyPI
wheel into a fresh environment, runs these commands, and checks the trace for
all three events. Its public Actions summary records the result. A failed
install, demo, trace check, or report blocks the email.

## What this proves

The example proves these local guard paths work in that published package.
The costs are simulated. This is not a provider invoice cap, evidence of money
saved, or protection for calls outside instrumented Python paths. Read the
[enforcement boundary](../enforcement-boundary.md) before adding it to real work.

## Help choose the next improvement

`--feedback` prints a redacted report on your computer. It sends nothing.
Review it before sharing. If you want, reply to the release email with the
result and the workflow you tried. Include what stopped you if setup failed.

A successful demo is the first milestone. Using a guard in a real workflow is
the next. Replies help distinguish those outcomes; downloads alone cannot.
