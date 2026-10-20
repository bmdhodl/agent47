"""Replay a reworded Claude Code loop through the real hook CLI, then print the receipt.

Run from the repo root: python proof/near-duplicate-loops/hook_session.py
Each hook call is a separate process, as Claude Code runs it.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

NO_MATCHES = {"mode": "files_with_matches", "filenames": [], "numFiles": 0}


def hook(project, name, tool, tool_input, **extra):
    payload = {"session_id": "demo", "hook_event_name": name, "cwd": str(project),
               "tool_name": tool, "tool_input": tool_input, **extra}
    done = subprocess.run([sys.executable, "-m", "agentguard.cli", "hook", "claude-code"],
                          input=json.dumps(payload), capture_output=True, text=True)
    return done.returncode, done.stderr.strip()


def call(project, tool, tool_input, **result):
    code, err = hook(project, "PreToolUse", tool, tool_input)
    shown = json.dumps(tool_input)
    if code == 2:
        print(f"REFUSED {tool} {shown}\n  {err}")
        return False
    name = "PostToolUseFailure" if "error" in result else "PostToolUse"
    hook(project, name, tool, tool_input, **result)
    print(f"allowed {tool} {shown} -> {json.dumps(result)[:70]}")
    return True


with tempfile.TemporaryDirectory() as tmp:
    project = Path(tmp)
    print("== legit: paginate and mkdir quietly (never refused)")
    for page in range(1, 7):
        call(project, "WebFetch", {"url": f"https://api.example.com/items?page={page}"},
             tool_response={"result": f"10 items on page {page}"})
    for i in range(6):
        call(project, "Bash", {"command": f"mkdir -p out/{i}"},
             tool_response={"stdout": "", "stderr": "", "interrupted": False})
    print("\n== near-duplicate: same command, reworded only in case and spacing")
    for command in ["npm test", "npm  test", "NPM test"]:
        call(project, "Bash", {"command": command, "description": "run tests"},
             tool_response={"stdout": "ok"})
    print("\n== reworded search loop: every grep comes back empty")
    for pattern in ["retry_count", "retryCount", "retries", "max_retry", "RETRY_LIMIT", "retry_max"]:
        if not call(project, "Grep", {"pattern": pattern, "path": "src"}, tool_response=NO_MATCHES):
            break
    print("\n== agent changes approach: another tool, then grep is allowed again")
    call(project, "Read", {"file_path": "src/config.py"}, tool_response={"content": "MAX = 3"})
    call(project, "Grep", {"pattern": "MAX", "path": "src"},
         tool_response={"mode": "files_with_matches", "filenames": ["src/config.py"], "numFiles": 1})
    print("\n== agentguard receipt")
    trace = project / ".agentguard" / "claude-code" / "trace.jsonl"
    print(subprocess.run([sys.executable, "-m", "agentguard.cli", "receipt", str(trace)],
                         capture_output=True, text=True).stdout)
