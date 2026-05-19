from __future__ import annotations

from typing import List

LOCAL_TRACE_FILE = ".agentguard/traces.jsonl"
RAW_QUICKSTART_FILE = "agentguard_raw_quickstart.py"
RAW_QUICKSTART_COMMAND = "agentguard quickstart --framework raw --write"


def local_proof_commands(*, include_demo: bool = False) -> List[str]:
    """Return the local-first proof path shown by first-run CLI commands."""
    commands = [
        RAW_QUICKSTART_COMMAND,
        f"python {RAW_QUICKSTART_FILE}",
        f"agentguard report {LOCAL_TRACE_FILE}",
    ]
    if include_demo:
        return ["agentguard demo", *commands]
    return commands
