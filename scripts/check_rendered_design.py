"""Run changed-path design regressions without loading unrelated pytest plugins."""
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    import os
    env=dict(os.environ, PYTHONPATH=str(ROOT / 'sdk'), PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONUTF8="1")
    result=subprocess.run([sys.executable,"-m","pytest",'sdk/tests/test_rendered_design.py',"-q","--basetemp=.showwork/pytest-tmp/design-regression"],cwd=ROOT,env=env,
                          creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0), capture_output=True, text=True, encoding="utf-8")
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    return result.returncode

if __name__=="__main__":
    raise SystemExit(main())
