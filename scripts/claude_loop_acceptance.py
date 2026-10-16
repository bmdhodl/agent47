"""Check actual Claude Code loop-hook payloads with an offline scripted model.

Fresh config and project directories isolate both cases from user settings.
The environment/SSE isolation pattern matches the separate hook-failure
acceptance fixture. No real provider credentials or model service are used.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "sdk"))
from agentguard.hooks import install_settings  # noqa: E402


def environment(config: Path, endpoint: str) -> dict[str, str]:
    keep = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
            "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "LOCALAPPDATA"}
    env = {key: value for key, value in os.environ.items() if key.upper() in keep}
    env.update({
        "CLAUDE_CONFIG_DIR": str(config), "ANTHROPIC_BASE_URL": endpoint,
        "ANTHROPIC_API_KEY": "offline-fixture-not-a-real-key",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1", "DISABLE_AUTOUPDATER": "1",
        "DISABLE_TELEMETRY": "1", "DISABLE_ERROR_REPORTING": "1",
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1", "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1",
        "PYTHONPATH": str(ROOT / "sdk"),
    })
    return env


def frames(block: dict, stop: str) -> bytes:
    message = {"id": "msg_offline", "type": "message", "role": "assistant",
               "model": "offline-fixture", "content": [], "stop_reason": None,
               "stop_sequence": None, "usage": {"input_tokens": 10, "output_tokens": 0}}
    if block["type"] == "tool_use":
        initial = {**block, "input": {}}
        delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])}
    else:
        initial = {"type": "text", "text": ""}
        delta = {"type": "text_delta", "text": block["text"]}
    entries = [
        {"type": "message_start", "message": message},
        {"type": "content_block_start", "index": 0, "content_block": initial},
        {"type": "content_block_delta", "index": 0, "delta": delta},
        {"type": "content_block_stop", "index": 0},
        {"type": "message_delta", "delta": {"stop_reason": stop, "stop_sequence": None},
         "usage": {"output_tokens": 10}},
        {"type": "message_stop"},
    ]
    return "".join(f"event: {entry['type']}\ndata: {json.dumps(entry)}\n\n"
                   for entry in entries).encode("utf-8")


def results_from(messages: list) -> list[dict]:
    return [block for message in messages if message.get("role") == "user"
            and isinstance(message.get("content"), list) for block in message["content"]
            if block.get("type") == "tool_result"]


def run_case(case: str, parent: Path, claude: str) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"claude-loop-{case}-") as temporary:
        project = Path(temporary)
        config = project / "config"
        config.mkdir()
        marker = project / "recovered.txt"
        payloads = project / "hook-payloads.jsonl"
        shim = project / "capture_hook.py"
        shim.write_text(
            "import io,json,sys\nfrom agentguard.hooks import run\n"
            "raw=sys.stdin.read()\n"
            "with open(sys.argv[1], 'a', encoding='utf-8') as output:\n"
            "    output.write(json.dumps(json.loads(raw))+'\\n')\n"
            "raise SystemExit(run(io.StringIO(raw),sys.stderr))\n", encoding="utf-8")
        settings = install_settings({}, sys.executable, None)
        for groups in settings["hooks"].values():
            for group in groups:
                for handler in group["hooks"]:
                    handler["args"] = [str(shim), str(payloads)]
        settings_path = project / "settings.json"
        settings_path.write_text(json.dumps(settings), encoding="utf-8")
        (project / ".agentguard.json").write_text(
            json.dumps({"no_progress_max": 5} if case == "opt-in" else {}), encoding="utf-8")
        commands = [f"cat agentguard-missing-{name}.log" for name in
                    ("alpha", "bravo", "charlie", "delta", "echo")]
        commands.append(f"printf recovered > {shlex.quote(marker.as_posix())}")
        requests = []

        class Fixture(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                messages = payload.get("messages", [])
                requests.append({"path": self.path, "messages": messages})
                if "count_tokens" in self.path:
                    body, content_type = b'{"input_tokens":10}', "application/json"
                else:
                    completed = len({block.get("tool_use_id") for block in results_from(messages)})
                    if completed < len(commands):
                        block = {"type": "tool_use", "id": f"toolu_loop_{completed}", "name": "Bash",
                                 "input": {"command": commands[completed], "description": "Offline diagnostic proof"}}
                        body = frames(block, "tool_use")
                    else:
                        body = frames({"type": "text", "text": "Offline proof complete."}, "end_turn")
                    content_type = "text/event-stream"
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        endpoint = f"http://127.0.0.1:{server.server_port}"
        argv = [claude, "-p", "Run each scripted offline diagnostic call and finish.",
                "--model", "offline-fixture", "--tools", "Bash", "--allowedTools", "Bash",
                "--permission-mode", "dontAsk", "--permission-prompts", "none", "--setting-sources", "",
                "--settings", str(settings_path), "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                "--no-session-persistence", "--output-format", "stream-json", "--verbose", "--max-turns", "8"]
        try:
            result = subprocess.run(argv, cwd=project, env=environment(config, endpoint),
                                    capture_output=True, text=True, encoding="utf-8", timeout=90,
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
        events = [json.loads(line) for line in payloads.read_text(encoding="utf-8").splitlines()]
        failures = [event for event in events if event["hook_event_name"] == "PostToolUseFailure"]
        pre = [event for event in events if event["hook_event_name"] == "PreToolUse"]
        results = {block["tool_use_id"]: block for request in requests
                   for block in results_from(request["messages"])}
        last = results.get("toolu_loop_5", {})
        states = list((project / ".agentguard" / "claude-code" / "sessions").glob("*.json"))
        state = json.loads(states[0].read_text(encoding="utf-8")) if len(states) == 1 else None
        refused = "AgentGuard refused" in json.dumps(last)
        expected_stop = case == "opt-in"
        passed = (result.returncode == 0 and len(failures) == 5 and len(pre) == 6
                  and len(results) == 6 and refused == expected_stop
                  and marker.exists() != expected_stop)
        output = parent / case
        output.mkdir()
        receipt = {"case": case, "passed": passed, "returncode": result.returncode,
                   "failure_hook_count": len(failures), "pre_hook_count": len(pre),
                   "marker_exists": marker.exists(), "refused": refused, "state": state,
                   "tool_results": results, "settings": settings, "argv": argv,
                   "boundary": "Native host, scripted loopback model; no live provider or active profile"}
        (output / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        (output / "hook-payloads.jsonl").write_text(payloads.read_text(encoding="utf-8"), encoding="utf-8")
        (output / "stdout.jsonl").write_text(result.stdout, encoding="utf-8")
        (output / "stderr.txt").write_text(result.stderr, encoding="utf-8")
        return {key: receipt[key] for key in ("case", "passed", "returncode", "failure_hook_count",
                                             "pre_hook_count", "marker_exists", "refused")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claude", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    version = subprocess.run([args.claude, "--version"], capture_output=True, text=True,
                             check=True, timeout=5,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout.strip()
    with tempfile.TemporaryDirectory(prefix="claude-loop-acceptance-") as temporary:
        output = args.output or Path(temporary)
        output.mkdir(parents=True, exist_ok=True)
        results = []
        for case in ("default-off", "opt-in"):
            result = run_case(case, output, args.claude)
            results.append(result)
            print(json.dumps(result), flush=True)
        (output / "summary.json").write_text(json.dumps({"host": version, "cases": results}, indent=2), encoding="utf-8")
    return 0 if all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
