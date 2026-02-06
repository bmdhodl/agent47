"""dev_agent.py — A code assistant agent that traces itself with AgentGuard.

This is a ReAct agent: it thinks, picks a tool, observes the result, and
repeats until it has an answer. Every step is traced and sent to the
AgentGuard dashboard so you can see exactly what it did.

Setup:
  pip install agentguard47 anthropic

Run:
  export ANTHROPIC_API_KEY=sk-ant-...
  export AGENTGUARD_KEY=ag_...
  python dev_agent.py "What are the main API endpoints in this project?"

Then open the dashboard to see the trace:
  https://app.agentguard47.com/traces
"""
from __future__ import annotations

import glob as globmod
import json
import os
import subprocess
import sys
import time

import anthropic

from agentguard.guards import BudgetGuard, LoopDetected, LoopGuard
from agentguard.sinks.http import HttpSink
from agentguard.tracing import JsonlFileSink, Tracer, TraceSink

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DASHBOARD_URL = os.environ.get(
    "AGENTGUARD_URL",
    "https://app.agentguard47.com/api/ingest",
)
AGENTGUARD_KEY = os.environ.get("AGENTGUARD_KEY", "")
MODEL = os.environ.get("AGENT_MODEL", "claude-sonnet-4-5-20250929")
MAX_STEPS = int(os.environ.get("AGENT_MAX_STEPS", "15"))

# Where to run tools from (defaults to repo root)
WORK_DIR = os.environ.get(
    "AGENT_WORK_DIR",
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
)


# ---------------------------------------------------------------------------
# Tracing setup — send to dashboard AND save locally
# ---------------------------------------------------------------------------
class MultiplexSink(TraceSink):
    """Fan-out to multiple sinks."""

    def __init__(self, sinks: list[TraceSink]) -> None:
        self.sinks = sinks

    def emit(self, event: dict) -> None:
        for s in self.sinks:
            s.emit(event)


def make_sink() -> TraceSink:
    sinks: list[TraceSink] = []

    # Always save a local file for offline inspection
    here = os.path.dirname(os.path.abspath(__file__))
    sinks.append(JsonlFileSink(os.path.join(here, "agent_traces.jsonl")))

    # If we have a dashboard key, also stream there
    if AGENTGUARD_KEY:
        sinks.append(HttpSink(url=DASHBOARD_URL, api_key=AGENTGUARD_KEY))
        print(f"[agent] Tracing → dashboard + agent_traces.jsonl")
    else:
        print(f"[agent] Tracing → agent_traces.jsonl (set AGENTGUARD_KEY to stream to dashboard)")

    return MultiplexSink(sinks) if len(sinks) > 1 else sinks[0]


# ---------------------------------------------------------------------------
# Tools the agent can use
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file. Returns up to 10,000 characters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path from the repo root",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "search_code",
        "description": "Search for a regex pattern across files (like grep -rn). Returns matching lines.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern to search for"},
                "directory": {
                    "type": "string",
                    "description": "Subdirectory to search in (default: entire repo)",
                    "default": ".",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "list_files",
        "description": "List files matching a glob pattern (e.g. '**/*.py', 'dashboard/src/**/*.ts').",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Glob pattern"},
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "run_command",
        "description": "Run a read-only shell command. For inspection only — no writes, no installs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell command to run"},
            },
            "required": ["command"],
        },
    },
]


def execute_tool(name: str, inputs: dict, ctx) -> str:
    """Run a tool, trace it, return the result as a string."""
    with ctx.span(f"tool.{name}", data=inputs):
        try:
            if name == "read_file":
                full = os.path.join(WORK_DIR, inputs["path"])
                with open(full) as f:
                    result = f.read()[:10_000]

            elif name == "search_code":
                proc = subprocess.run(
                    ["grep", "-rn", "--include=*.py", "--include=*.ts", "--include=*.tsx",
                     "--include=*.js", "--include=*.json", "--include=*.md",
                     inputs["pattern"], inputs.get("directory", ".")],
                    capture_output=True, text=True, timeout=10, cwd=WORK_DIR,
                )
                result = proc.stdout[:8_000] or "(no matches)"

            elif name == "list_files":
                matches = sorted(globmod.glob(
                    os.path.join(WORK_DIR, inputs["pattern"]),
                    recursive=True,
                ))
                # Strip the work dir prefix for cleaner output
                prefix = WORK_DIR.rstrip("/") + "/"
                cleaned = [m.replace(prefix, "") for m in matches]
                result = "\n".join(cleaned[:200]) or "(no matches)"

            elif name == "run_command":
                # Safety: block destructive commands
                cmd = inputs["command"]
                blocked = ["rm ", "mv ", "cp ", "chmod", "chown", "sudo", "> ", ">>", "curl", "wget"]
                if any(b in cmd for b in blocked):
                    result = f"Blocked: {cmd} (read-only agent)"
                else:
                    proc = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True,
                        timeout=30, cwd=WORK_DIR,
                    )
                    result = (proc.stdout + proc.stderr)[:8_000]

            else:
                result = f"Unknown tool: {name}"

            ctx.event("tool.result", data={"result": result[:500], "chars": len(result)})
            return result

        except FileNotFoundError:
            ctx.event("tool.error", data={"error": f"File not found: {inputs.get('path', '?')}"})
            return f"Error: file not found"
        except subprocess.TimeoutExpired:
            ctx.event("tool.error", data={"error": "Command timed out"})
            return "Error: command timed out after 30s"
        except Exception as e:
            ctx.event("tool.error", data={"error": str(e)[:200]})
            return f"Error: {e}"


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------
def run(task: str) -> str:
    """Run the agent on a task. Returns the final answer."""

    sink = make_sink()
    tracer = Tracer(sink=sink, service="dev-agent")
    loop_guard = LoopGuard(max_repeats=3, window=8)
    budget_guard = BudgetGuard(max_calls=MAX_STEPS * 3)
    client = anthropic.Anthropic()

    messages: list[dict] = [{"role": "user", "content": task}]
    answer = ""

    with tracer.trace("agent.dev_assistant", data={"task": task, "model": MODEL}) as ctx:
        for step in range(MAX_STEPS):
            ctx.event("reasoning.step", data={"step": step + 1, "max": MAX_STEPS})

            # --- LLM call ---
            with ctx.span(f"llm.anthropic.{MODEL}") as llm_span:
                response = client.messages.create(
                    model=MODEL,
                    max_tokens=4096,
                    system=(
                        "You are a senior developer reviewing a codebase. "
                        "Use the tools to read files, search code, and run commands. "
                        "Be thorough but efficient — don't read files you don't need. "
                        "When you have enough info, give a clear, actionable answer."
                    ),
                    messages=messages,
                    tools=TOOLS,
                )
                llm_span.event("llm.result", data={
                    "stop_reason": response.stop_reason,
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                })
                budget_guard.consume(calls=1)

            # --- Check if done ---
            if response.stop_reason == "end_turn":
                answer = next(
                    (b.text for b in response.content if hasattr(b, "text")), ""
                )
                ctx.event("agent.complete", data={
                    "answer": answer[:500],
                    "steps": step + 1,
                })
                break

            # --- Execute tool calls ---
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if block.type != "tool_use":
                    continue

                # Guard checks
                try:
                    loop_guard.check(block.name, block.input)
                except LoopDetected as e:
                    ctx.event("guard.loop_detected", data={
                        "tool": block.name,
                        "error": str(e),
                    })
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": f"LOOP DETECTED: {e}. Try a different approach.",
                        "is_error": True,
                    })
                    continue

                print(f"  [{step+1}] {block.name}({json.dumps(block.input)[:80]})")
                result = execute_tool(block.name, block.input, ctx)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results})

        else:
            ctx.event("agent.max_steps", data={"steps": MAX_STEPS})
            answer = "Hit maximum steps without completing. Partial results in trace."

    # Give HttpSink time to flush
    time.sleep(3)
    return answer


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python dev_agent.py <task>")
        print()
        print("Examples:")
        print('  python dev_agent.py "What are the API endpoints and what do they do?"')
        print('  python dev_agent.py "Find potential bugs in the ingest route"')
        print('  python dev_agent.py "How does the auth system work?"')
        print('  python dev_agent.py "What tests exist and what do they cover?"')
        sys.exit(1)

    task = " ".join(sys.argv[1:])
    print(f"[agent] Task: {task}")
    print(f"[agent] Working dir: {WORK_DIR}")
    print()

    result = run(task)

    print()
    print("=" * 60)
    print(result)
    print("=" * 60)
    print()
    print("[agent] Trace saved to sdk/examples/agent_traces.jsonl")
    if AGENTGUARD_KEY:
        print("[agent] Trace also sent to dashboard")
