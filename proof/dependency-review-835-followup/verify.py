from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parent
for name, expected in json.loads((root / "manifest.json").read_text(encoding="utf-8")).items():
    data = (root / name).read_bytes()
    if name.endswith(".json"):
        data = data.replace(b"\r\n", b"\n")
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Artifact hash mismatch: {name}")
commands = json.loads((root / "commands.json").read_text(encoding="utf-8"))
for command in commands:
    if command["exit"] != command["expected"]:
        raise ValueError(f"Unexpected command exit: {command['name']}")
tamper = [c for c in commands if "tamper" in c["name"]]
if len(tamper) != 4 or any(c["exit"] != 1 for c in tamper):
    raise ValueError("Missing normal/optimized rejection evidence for both packets")
print("Verified optimized tamper rejection receipts")
