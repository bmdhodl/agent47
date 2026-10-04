# Move to Python 3.11 for AgentGuard 2.0

The unpublished AgentGuard 2.0.0 candidate requires Python 3.11 or newer.
It replaces the planned 1.4.1 candidate. This is a breaking support change;
the latest published package remains 1.4.0. The Python import name, public
guard APIs, MIT license, and zero runtime dependencies stay the same.

Python 3.9 reached end of life in October 2025. Python 3.10 reached end of
life on October 1, 2026. Python 3.11 is the oldest supported interpreter;
its security support is scheduled through October 2027.
See the [official Python support schedule](https://devguide.python.org/versions/).

## Upgrade the interpreter first

Install Python 3.11 or newer, then create a new virtual environment. Existing
virtual environments keep their original interpreter; installing a newer
Python does not update them. Keep your old environment until the replacement
passes your application's tests.

On Windows PowerShell:

```powershell
py -3.11 -m venv .venv-py311
& .\.venv-py311\Scripts\python.exe -m pip install agentguard47
& .\.venv-py311\Scripts\python.exe -m agentguard doctor
& .\.venv-py311\Scripts\python.exe -m agentguard demo
```

On Linux or macOS:

```bash
python3.11 -m venv .venv-py311
.venv-py311/bin/python -m pip install agentguard47
.venv-py311/bin/python -m agentguard doctor
.venv-py311/bin/python -m agentguard demo
```

These commands install the published release, currently 1.4.0. After 2.0.0
is published, update your application's package constraint to allow it, install
the new version in this environment, and rerun your application tests.
For the candidate from a checkout, use `python -m pip install ./sdk` with the
new environment's Python. No release tag or PyPI publication is part of #831.

## Stay on an older interpreter

If your application must use Python 3.9 or 3.10, pin the existing release:

```bash
python -m pip install agentguard47==1.4.0
```

That preserves the previously released SDK. It does not supply Python runtime
security updates or the candidate's new SDK fixes. AgentGuard 2.0 metadata
rejects installation on these retired interpreters; do not bypass that check.
