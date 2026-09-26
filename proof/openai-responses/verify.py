"""Re-checks the AG-06 claims. Exit 0 means all hold."""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
subprocess.run(
    [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
     "sdk/tests/test_instrument_stream.py", "sdk/tests/test_enforcement_boundary.py",
     "sdk/tests/test_architecture.py", "sdk/tests/test_real_dispatch.py"],
    cwd=ROOT, check=True,
)
real = (ROOT / "proof/openai-responses/real-deps.txt").read_text(encoding="utf-8")
assert "test_agents_sdk_run_stops_a_tool_loop_before_the_next_model_call[True] PASSED" in real
assert "FAILED" not in real
before = (ROOT / "proof/openai-responses/before-fix.txt").read_text(encoding="utf-8")
assert "8 failed" in before
example = (ROOT / "proof/openai-responses/agents-sdk-example-run.txt").read_text(encoding="utf-8")
assert "AgentGuard stopped the run: Cost budget exceeded" in example
assert "model call 5" in example and "model call 6" not in example
print("AG-06 claims hold")
