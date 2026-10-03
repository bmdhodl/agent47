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

## Windows PowerShell

This walkthrough uses the published 1.4.0 wheel, checked on October 2, 2026.
Run it from a directory where `agentguard-first-run` does not already exist.
Use Python 3.9 or newer. The commands call the virtual environment's Python
directly, so they need no activation script or PowerShell policy change.
The pinned package has no runtime dependencies, so `--no-deps` is safe for
this version.

```powershell
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Path agentguard-first-run | Out-Null
Set-Location -LiteralPath agentguard-first-run
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
& .\.venv\Scripts\python.exe -I -m pip --isolated install --index-url https://pypi.org/simple --only-binary=:all: --no-deps agentguard47==1.4.0
if ($LASTEXITCODE -ne 0) { throw 'Package installation failed.' }
& .\.venv\Scripts\python.exe -I -m agentguard doctor
if ($LASTEXITCODE -ne 0) { throw 'The installation check failed.' }
& .\.venv\Scripts\python.exe -I -m agentguard demo --feedback
if ($LASTEXITCODE -ne 0) { throw 'The offline demo failed.' }
& .\.venv\Scripts\python.exe -I -m agentguard report agentguard_demo_traces.jsonl
if ($LASTEXITCODE -ne 0) { throw 'The demo report failed.' }
& .\.venv\Scripts\python.exe -I -m agentguard quickstart --framework raw --write
if ($LASTEXITCODE -ne 0) { throw 'Starter creation failed.' }
& .\.venv\Scripts\python.exe -I agentguard_raw_quickstart.py
if ($LASTEXITCODE -ne 0) { throw 'The raw starter failed.' }
& .\.venv\Scripts\python.exe -I -m agentguard report .agentguard/traces.jsonl
if ($LASTEXITCODE -ne 0) { throw 'The starter report failed.' }
```

The demo must show budget, loop, and retry stops. The raw starter writes a
separate trace, then the last command shows its report. These are local
simulations, not proof of external adoption or a provider invoice cap.

If `python` is absent, install a supported Python version from
[python.org](https://www.python.org/downloads/windows/) before this walkthrough.
If a command fails, stop at that command. Include its error and the package
version in a voluntary report. To read the installed version without a newer
CLI command, run:

```powershell
& .\.venv\Scripts\python.exe -I -c "import importlib.metadata; print(importlib.metadata.version('agentguard47'))"
```

Version 1.4.0 does not have `receipt`, `hook`, `run`, or `--version`. Those
commands are in the unpublished 2.0.0 candidate. This walkthrough needs no
provider key or optional framework package. Keep any trace private until you
have checked its contents.

The demo trace, `agentguard_demo_traces.jsonl`, should contain all three events:

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
