"""Regenerate the self-contained HTML brand assets from the shared export."""
import argparse
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / 'sdk/agentguard/_design.py'

def expected():
    css = (ROOT / "design-tokens.css").read_text(encoding="utf-8")
    css += "\n" + (ROOT / "design-surfaces.css").read_text(encoding="utf-8")
    image = base64.b64encode((ROOT / "bmd-loop-mark-512.png").read_bytes()).decode("ascii")
    logo = '<img class="bmd-mark" src="data:image/png;base64,' + image + '" width="48" height="48" alt="">'
    return ('"""Generated offline BMD assets. Run scripts/sync_design_assets.py."""\n\n'
            + 'CSS = """' + css + '"""\n\nLOGO = (\n'
            + ''.join('    ' + repr(logo[i:i+100]) + '\n' for i in range(0, len(logo), 100)) + ')\n')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    value = expected()
    if args.check:
        if TARGET.read_text(encoding="utf-8") != value:
            raise SystemExit("Rendered design assets drifted; run scripts/sync_design_assets.py")
        print("rendered design assets: current")
    else:
        TARGET.write_text(value, encoding="utf-8", newline="\n")
