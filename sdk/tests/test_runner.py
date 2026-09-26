import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from agentguard.runner import split_target

SDK = str(Path(__file__).resolve().parents[1])

SPENDER = """
import sys
import agentguard
print("argv", sys.argv[1:])
guard = agentguard.get_budget_guard()
for _ in range(10):
    guard.consume(calls=1, cost_usd=1.5)
"""


def _run(tmp_path, *args):
    env = {**os.environ, "AGENTGUARD_API_KEY": "", "AGENTGUARD_BUDGET_USD": "", "PYTHONPATH": SDK}
    return subprocess.run(
        [sys.executable, "-m", "agentguard.cli", "run", *args],
        cwd=tmp_path, capture_output=True, text=True, env=env,
    )


@pytest.mark.parametrize(
    "target, expected",
    [
        (["agent.py", "-x"], (None, ["agent.py", "-x"])),
        (["--", "python", "agent.py"], (None, ["agent.py"])),
        (["python3.12", "-m", "pkg.cli", "go"], ("pkg.cli", ["go"])),
        (["-m", "pkg.cli", "--profile", "x"], ("pkg.cli", ["--profile", "x"])),
    ],
)
def test_split_target(target, expected):
    assert split_target(target) == expected


@pytest.mark.parametrize("target", [[], ["python"], ["python", "-m"], ["-m"]])
def test_split_target_needs_a_script(target):
    with pytest.raises(SystemExit):
        split_target(target)


def test_budget_stop_ends_the_run(tmp_path):
    (tmp_path / "agent.py").write_text(SPENDER, encoding="utf-8")
    proc = _run(tmp_path, "--budget-usd", "5", "--trace-file", "t.jsonl", "python", "agent.py", "--flag")
    assert proc.returncode == 1
    assert "argv ['--flag']" in proc.stdout
    assert "stopped the run. Cost budget exceeded: $6.0000 > $5.0000" in proc.stderr
    assert "agentguard receipt t.jsonl" in proc.stderr


def test_repo_config_budget_applies_without_flags(tmp_path):
    (tmp_path / ".agentguard.json").write_text(json.dumps({"budget_usd": 2}), encoding="utf-8")
    (tmp_path / "agent.py").write_text(SPENDER, encoding="utf-8")
    proc = _run(tmp_path, "agent.py")
    assert proc.returncode == 1
    assert "$3.0000 > $2.0000" in proc.stderr


def test_script_exit_code_passes_through(tmp_path):
    (tmp_path / "agent.py").write_text("import sys\nsys.exit(7)\n", encoding="utf-8")
    proc = _run(tmp_path, "agent.py")
    assert proc.returncode == 7
    assert "trace written to traces.jsonl" in proc.stderr


def test_module_mode_runs_as_main(tmp_path):
    pkg = tmp_path / "mypkg"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "cli.py").write_text(
        "import sys\nif __name__ == '__main__':\n    print('main', sys.argv[1:])\n", encoding="utf-8"
    )
    for args in (["-m", "mypkg.cli", "a", "--profile", "x"], ["python", "-m", "mypkg.cli", "a", "--profile", "x"]):
        proc = _run(tmp_path, *args)
        assert proc.returncode == 0, proc.stderr
        assert "main ['a', '--profile', 'x']" in proc.stdout


def test_script_imports_its_own_directory(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "helper.py").write_text("VALUE = 42\n", encoding="utf-8")
    (tmp_path / "src" / "agent.py").write_text("import helper\nprint(helper.VALUE)\n", encoding="utf-8")
    proc = _run(tmp_path, "src/agent.py")
    assert proc.returncode == 0, proc.stderr
    assert "42" in proc.stdout


def test_run_restores_argv_and_path(tmp_path, monkeypatch):
    from agentguard.runner import run

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTGUARD_API_KEY", "")
    (tmp_path / "agent.py").write_text("import sys\nassert sys.argv == ['agent.py', 'x']\n", encoding="utf-8")
    argv, path = sys.argv[:], sys.path[:]
    assert run(["agent.py", "x"], trace_file=str(tmp_path / "t.jsonl"), err=io.StringIO()) == 0
    assert sys.argv == argv and sys.path == path
