"""Exercise native Claude Code hook dispatch against a loopback model fixture.

No real provider, credentials, or user settings are used. This is offline host
integration evidence, not a paid-model or production-profile acceptance test.
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "sdk"))
from agentguard.hooks import install_settings  # noqa: E402

CASES = ("allow", "deny", "missing-executable", "crash", "timeout", "malformed-json", "invalid-schema")


def environment(config: Path, sdk: Path, endpoint: str) -> dict[str, str]:
    """Construct a child-only environment with no real provider/proxy variables."""
    keep = {"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
            "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "LOCALAPPDATA"}
    env = {key: value for key, value in os.environ.items() if key.upper() in keep}
    env.update({
        "CLAUDE_CONFIG_DIR": str(config),
        "ANTHROPIC_BASE_URL": endpoint,
        "ANTHROPIC_API_KEY": "offline-fixture-not-a-real-key",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "DISABLE_AUTOUPDATER": "1", "DISABLE_TELEMETRY": "1",
        "DISABLE_ERROR_REPORTING": "1", "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
        "CLAUDE_CODE_DISABLE_FEEDBACK_SURVEY": "1",
        "PYTHONPATH": str(sdk),
    })
    return env


def frames(block: dict, stop_reason: str) -> str:
    message = {"id": "msg_offline", "type": "message", "role": "assistant",
               "model": "offline-fixture", "content": [], "stop_reason": None,
               "stop_sequence": None, "usage": {"input_tokens": 10, "output_tokens": 0}}
    if block["type"] == "tool_use":
        initial = {**block, "input": {}}
        delta = {"type": "input_json_delta", "partial_json": json.dumps(block["input"])}
    else:
        initial = {"type": "text", "text": ""}
        delta = {"type": "text_delta", "text": block["text"]}
    data = [
        {"type": "message_start", "message": message},
        {"type": "content_block_start", "index": 0, "content_block": initial},
        {"type": "content_block_delta", "index": 0, "delta": delta},
        {"type": "content_block_stop", "index": 0},
        {"type": "message_delta", "delta": {"stop_reason": stop_reason, "stop_sequence": None},
         "usage": {"output_tokens": 10}},
        {"type": "message_stop"},
    ]
    return "".join(f"event: {entry['type']}\ndata: {json.dumps(entry)}\n\n" for entry in data)


def run_case(name: str, root: Path, claude: str, sdk: Path) -> dict:
    project = root / name
    project.mkdir()
    config = project / "config"
    config.mkdir()
    marker = project / "tool-ran.txt"
    settings = install_settings({}, sys.executable, 0 if name == "deny" else None)
    handler = settings["hooks"]["PreToolUse"][0]["hooks"][0]
    scripts = {
        "crash": "import sys; sys.stdin.read(); sys.exit(1)",
        "timeout": "import sys,time; sys.stdin.read(); time.sleep(10)",
        "malformed-json": "import sys; sys.stdin.read(); print('{\"hookSpecificOutput\":}')",
        "invalid-schema": "import sys; sys.stdin.read(); print('{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":123}}')",
    }
    if name == "missing-executable":
        handler.update(command=str(project / "does-not-exist"), args=[])
    elif name in scripts:
        handler.update(command=sys.executable, args=["-c", scripts[name]])
    if name == "timeout":
        handler["timeout"] = 1
    settings_path = project / "settings.json"
    settings_path.write_text(json.dumps(settings), encoding="utf-8")
    requests = []
    command = f"printf native-hook-action > {shlex.quote(marker.as_posix())}"

    class Fixture(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            requests.append({"path": self.path, "messages": payload.get("messages", [])})
            if "count_tokens" in self.path:
                body = json.dumps({"input_tokens": 10}).encode()
                content_type = "application/json"
            else:
                # Exactly one scripted tool call; following request ends the turn.
                completed = any(item.get("role") == "assistant" for item in payload.get("messages", []))
                block = ({"type": "text", "text": "Offline fixture complete."} if completed else
                         {"type": "tool_use", "id": "toolu_offline", "name": "Bash",
                          "input": {"command": command, "description": "Write isolated proof marker"}})
                body = frames(block, "end_turn" if completed else "tool_use").encode()
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
    argv = [claude, "-p", "Run the single offline fixture tool call, then finish.",
            "--model", "offline-fixture", "--tools", "Bash", "--allowedTools", "Bash",
            "--permission-mode", "dontAsk", "--permission-prompts", "none", "--setting-sources", "",
            "--settings", str(settings_path), "--strict-mcp-config",
            "--mcp-config", '{"mcpServers":{}}', "--no-session-persistence",
            "--output-format", "stream-json", "--verbose", "--max-turns", "3"]
    timed_out = False
    try:
        try:
            result = subprocess.run(argv, cwd=project, env=environment(config, sdk, endpoint),
                                    capture_output=True, text=True, timeout=45,
                                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            stdout, stderr, returncode = str(exc.stdout or ""), str(exc.stderr or ""), None
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    # A missing marker alone is insufficient: the real host must dispatch the
    # fixture tool and send its actual tool_result back to the loopback server.
    results = [block for request in requests for message in request["messages"]
               if message.get("role") == "user" and isinstance(message.get("content"), list)
               for block in message["content"] if block.get("type") == "tool_result"]
    result_text = json.dumps(results)
    if name == "allow":
        expected_hook = True
    elif name == "deny":
        expected_hook = "AgentGuard refused" in result_text
    else:
        expected_hook = "onFailure" in result_text and "block" in result_text
    passed = (not timed_out and returncode == 0 and bool(results) and expected_hook
              and "InputValidationError" not in result_text
              and marker.exists() == (name == "allow"))
    (project / "stdout.jsonl").write_text(stdout, encoding="utf-8")
    (project / "stderr.txt").write_text(stderr, encoding="utf-8")
    receipt = {"case": name, "passed": passed, "returncode": returncode,
               "timed_out": timed_out, "marker_exists": marker.exists(),
               "tool_results": results, "requests": requests, "argv": argv,
               "endpoint": endpoint, "settings": settings,
               "isolation": "fresh config/project; no user credentials; loopback provider only"}
    (project / "receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return {key: receipt[key] for key in ("case", "passed", "returncode", "timed_out", "marker_exists")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--claude", default=shutil.which("claude"))
    parser.add_argument("--case", choices=CASES, action="append")
    args = parser.parse_args()
    if not args.claude:
        parser.error("Claude Code is not installed")
    args.output.mkdir(parents=True, exist_ok=True)
    version = subprocess.run([args.claude, "--version"], capture_output=True, text=True,
                             check=True, timeout=5,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)).stdout.strip()
    sdk = Path(__file__).resolve().parents[1] / "sdk"
    # Every run gets a new isolated directory. Never reuse an existing profile.
    root = Path(tempfile.mkdtemp(prefix="native-host-", dir=args.output)).resolve()
    results = []
    for case in args.case or CASES:
        result = run_case(case, root, args.claude, sdk)
        results.append(result)
        print(json.dumps(result), flush=True)
    summary = {"host": version, "root": str(root), "cases": results,
               "boundary": "Native host, offline scripted model; no live paid provider or active profile test"}
    (root / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if all(case["passed"] for case in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
