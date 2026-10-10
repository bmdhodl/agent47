"""Replay a synthetic, offline trace through the real receipt CLI.

Run from the repository root: python proof/receipt-cost-852/verify.py
No provider, account, network request, or invoice is involved.
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    proof = Path(__file__).resolve().parent
    repo = proof.parents[1]
    trace = proof / "trace.jsonl"
    env = dict(os.environ, PYTHONPATH=str(repo / "sdk"), PYTHONIOENCODING="utf-8")
    for fmt, filename in (("text", "text.txt"), ("markdown", "markdown.md"), ("json", "receipt.json")):
        result = subprocess.run(
            [sys.executable, "-m", "agentguard.cli", "receipt", str(trace), "--format", fmt],
            env=env, cwd=repo, check=True, capture_output=True, text=True, encoding="utf-8", timeout=15,
        )
        output = result.stdout
        if fmt == "json":
            receipt = json.loads(output)
            assert receipt["llm_calls"] == 2
            assert receipt["recorded_cost_usd"] == 0.0069
            assert receipt["stops"] == [{"kind": "budget", "detail": "$0.0069 over $0.0050"}]
        else:
            cost_line = next(line for line in output.splitlines() if line.startswith("recorded cost"))
            assert cost_line.endswith("$0.0069"), cost_line
            assert "$0.0069 over $0.0050" in output
            assert "$0.01" not in output
        (proof / filename).write_text(output, encoding="utf-8", newline="\n")
        print(f"{fmt}: passed")
    print(f"trace sha256: {hashlib.sha256(trace.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
