"""Behavior regressions for the unreleased near-duplicate loop changes."""
import io
import json

import pytest

from agentguard.guards import LoopDetected, LoopGuard
from agentguard.hooks import run, signature
from agentguard.instrument import trace_tool
from agentguard.receipt import build_receipt, render
from agentguard.tracing import JsonlFileSink, Tracer


@pytest.mark.parametrize("first,second", [
    ({"file_path": "src/Foo.py"}, {"file_path": "src/foo.py"}),
    ({"content": "if ready:\n    run()"}, {"content": "if ready:\nrun()"}),
    ({"command": "printf 'a b'"}, {"command": "printf 'a  b'"}),
    ({"pattern": "RetryCount"}, {"pattern": "retrycount"}),
])
def test_regression_argument_values_keep_case_and_whitespace(first, second):
    """REGRESSION: different files, code, shell literals and searches are distinct."""
    assert signature("Tool", first) != signature("Tool", second)
    guard = LoopGuard(max_repeats=2, normalize=True)
    guard.check("Tool", first)
    guard.check("Tool", second)


@pytest.mark.parametrize("sample_rate", [0.0, 1.0])
def test_regression_structured_empty_results_reach_guard(tmp_path, sample_rate):
    """REGRESSION: dict results must reach guards before trace string conversion."""
    path = tmp_path / "trace.jsonl"
    tracer = Tracer(sink=JsonlFileSink(str(path)), watermark=False,
                    guards=[LoopGuard(max_repeats=100, window=100, max_no_progress=3)],
                    sampling_rate=sample_rate)

    @trace_tool(tracer)
    def search(query):
        return {"matches": [], "numMatches": 0}

    search("first")
    search("second")
    with pytest.raises(LoopDetected, match="No progress: search came back empty 3 times"):
        search("third")


@pytest.mark.parametrize("sample_rate", [0.0, 1.0])
def test_regression_traced_errors_use_positional_and_keyword_args(tmp_path, sample_rate):
    """REGRESSION: argument-specific failures can be the same no-progress result."""
    secret = "synthetic-token-that-must-stay-in-memory"
    path = tmp_path / "trace.jsonl"
    tracer = Tracer(sink=JsonlFileSink(str(path)), watermark=False,
                    guards=[LoopGuard(max_repeats=100, window=100, max_no_progress=3)],
                    sampling_rate=sample_rate)

    @trace_tool(tracer)
    def read(path, *, token):
        raise FileNotFoundError(f"missing file {path}")

    with pytest.raises(FileNotFoundError):
        read("src/first.py", token=secret)
    with pytest.raises(FileNotFoundError):
        read(path="src/second.py", token=secret)
    with pytest.raises(LoopDetected, match="No progress: read failed with the same error 3 times"):
        read("lib/third.py", token=secret)
    if path.exists():
        assert secret not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("sample_rate", [0.0, 1.0])
def test_tool_guard_uses_raw_results_once_and_progress_resets(tmp_path, sample_rate):
    secret = "synthetic-private-argument"
    path = tmp_path / "trace.jsonl"
    guard = LoopGuard(max_repeats=100, window=100, max_no_progress=2)
    tracer = Tracer(sink=JsonlFileSink(str(path)), watermark=False, guards=[guard],
                    sampling_rate=sample_rate)

    @trace_tool(tracer)
    def search(query, *, token):
        return {"matches": ["found"] if query == "progress" else [], "numMatches": int(query == "progress")}

    search("first", token=secret)
    assert guard._stall["count"] == 1
    search("progress", token=secret)
    assert guard._stall is None
    search("third", token=secret)
    assert guard._stall["count"] == 1
    with pytest.raises(LoopDetected):
        search("fourth", token=secret)
    if path.exists():
        events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        assert all("tool_args" not in event["data"] for event in events)
        assert secret not in path.read_text(encoding="utf-8")


def _hook(project, *, name="PreToolUse", tool="Bash", tool_input=None, **extra):
    payload = {"session_id": "maintenance", "cwd": str(project), "hook_event_name": name,
               "tool_name": tool, "tool_input": tool_input, **extra}
    stderr = io.StringIO()
    return run(io.StringIO(json.dumps(payload)), stderr), stderr.getvalue()


def test_regression_no_progress_default_does_not_block_diagnostic_recovery(tmp_path, monkeypatch):
    """REGRESSION: changed diagnostic commands are allowed unless explicitly opted in."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    for number in range(7):
        args = {"command": f"inspect path-{number}.log"}
        assert _hook(tmp_path, tool_input=args)[0] == 0
        assert _hook(tmp_path, name="PostToolUseFailure", tool_input=args,
                     error=f"missing file path-{number}.log")[0] == 0
    assert _hook(tmp_path, tool_input={"command": "recover files"})[0] == 0


@pytest.mark.parametrize("stop", ["loop", "retry", "budget", "no_progress"])
def test_regression_hook_receipts_never_capture_raw_argument_values(tmp_path, monkeypatch, stop):
    """REGRESSION: labels and JSONL/receipt bodies cannot retain input credentials."""
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    secret = "synthetic-credential-do-not-persist"
    key_secret = "synthetic-key-that-is-private"
    args = {"command": f"curl -H 'Authorization: Bearer {secret}'",
            "url": f"https://example.invalid/?token={secret}",
            "nested": [{key_secret: secret}], "description": secret}
    if stop == "budget":
        # The run() max_calls argument is independent of repository defaults.
        payload = {"session_id": "maintenance", "cwd": str(tmp_path),
                   "hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": args}
        stderr = io.StringIO()
        assert run(io.StringIO(json.dumps(payload)), stderr, max_calls=0) == 2
        error = stderr.getvalue()
    else:
        config = {"no_progress_max": 2, "loop_max": 100, "retry_max": 100} if stop == "no_progress" else {}
        if stop == "retry":
            config = {"loop_max": 100}
        (tmp_path / ".agentguard.json").write_text(json.dumps(config), encoding="utf-8")
        if stop == "loop":
            assert _hook(tmp_path, tool_input=args)[0] == 0
            assert _hook(tmp_path, tool_input=args)[0] == 0
        else:
            for _ in range(2):
                assert _hook(tmp_path, tool_input=args)[0] == 0
                name = "PostToolUseFailure" if stop == "retry" else "PostToolUse"
                assert _hook(tmp_path, name=name, tool_input=args,
                             error=f"connection refused {secret}", tool_response=[])[0] == 0
        code, error = _hook(tmp_path, tool_input=args)
        assert code == 2
    trace = tmp_path / ".agentguard" / "claude-code" / "trace.jsonl"
    receipt = build_receipt(str(trace))
    assert receipt["stops"]
    content = trace.read_text(encoding="utf-8") + error
    for fmt in ("text", "json", "markdown"):
        content += render(receipt, fmt=fmt, ascii_only=True)
    for filename in (tmp_path / ".agentguard").rglob("*.json"):
        content += filename.read_text(encoding="utf-8")
    assert secret not in content
    assert key_secret not in content
