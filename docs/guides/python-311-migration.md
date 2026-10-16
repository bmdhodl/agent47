# Move to Python 3.11 for AgentGuard 2.0

AgentGuard 2.0.0 requires Python 3.11 or newer.
It replaces the planned 1.4.1 patch. This is a breaking support change;
1.4.0 is the last release for Python 3.9 and 3.10. The Python import name, public
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

These commands install the latest release. Update your application's package
constraint to allow 2.0.0, install it in this environment, and rerun your
application tests.

## Stay on an older interpreter

If your application must use Python 3.9 or 3.10, pin the existing release:

```bash
python -m pip install agentguard47==1.4.0
```

That preserves the previously released SDK. It does not supply Python runtime
security updates or the SDK fixes in 2.0.0. AgentGuard 2.0 metadata
rejects installation on these retired interpreters; do not bypass that check.
