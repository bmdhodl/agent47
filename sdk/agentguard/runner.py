"""``agentguard run``: guard an existing Python script without editing it.

Calls ``agentguard.init()`` (flags, then env vars, then ``.agentguard.json``),
which patches the OpenAI and Anthropic clients, then runs the script or module
in this interpreter as ``__main__``. A guard stop ends the run with exit 1.
"""
from __future__ import annotations

import os
import re
import runpy
import sys
from typing import List, Optional, TextIO

from agentguard.guards import BudgetExceeded, LoopDetected, RetryLimitExceeded, TimeoutExceeded
from agentguard.setup import init, shutdown

_PYTHON = re.compile(r"python(\d+(\.\d+)?)?(\.exe)?", re.I)
_STOPS = (BudgetExceeded, LoopDetected, RetryLimitExceeded, TimeoutExceeded)


def split_target(target: List[str]) -> tuple:
    """Return (module or None, argv) from ``script.py args`` or ``python -m mod args``."""
    if target[:1] == ["--"]:
        target = target[1:]
    if target and _PYTHON.fullmatch(os.path.basename(target[0])):
        target = target[1:]
    module = None
    if target[:1] == ["-m"]:
        if len(target) < 2:
            raise SystemExit("agentguard run: -m needs a module name")
        module, target = target[1], target[2:]
    if module is None and not target:
        raise SystemExit("agentguard run: name a script, e.g. agentguard run agent.py")
    return module, target


def run(target: List[str], *, budget_usd: Optional[float] = None,
        service: Optional[str] = None, trace_file: Optional[str] = None,
        profile: Optional[str] = None, err: TextIO = sys.stderr) -> int:
    module, argv = split_target(target)
    tracer = init(budget_usd=budget_usd, service=service, trace_file=trace_file, profile=profile)
    trace_path = getattr(tracer._sink, "_path", None)
    try:
        if module:
            sys.argv = [module, *argv]
            sys.path.insert(0, os.getcwd())
            runpy.run_module(module, run_name="__main__", alter_sys=True)
        else:
            sys.argv = argv
            sys.path.insert(0, os.path.dirname(os.path.abspath(argv[0])))
            runpy.run_path(argv[0], run_name="__main__")
    except _STOPS as stop:
        err.write(f"agentguard: stopped the run. {stop}\n")
        return 1
    finally:
        shutdown()
        if trace_path:
            err.write(f"agentguard: trace written to {trace_path}. "
                      f"See the stops with: agentguard receipt {trace_path}\n")
    return 0
