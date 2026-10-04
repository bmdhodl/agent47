from pathlib import Path
import hashlib
import json
root = Path(__file__).resolve().parent
for name, expected in json.loads((root / "manifest.json").read_text(encoding="utf-8")).items():
    data = (root / name).read_bytes()
    if name.endswith(".json"): data = data.replace(b"\r\n", b"\n")
    if hashlib.sha256(data).hexdigest() != expected: raise ValueError(f"Artifact hash mismatch: {name}")
receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
for command in receipt["commands"]:
    if command["name"] in {"sdk-install", "ruff-ci"}:
        if command["exit"] != 1 or command["expected"] != 0: raise ValueError("Initial failure record changed")
        continue
    if command["exit"] != command["expected"]: raise ValueError(f"Unexpected exit: {command['name']}")
if receipt["changed_packages"] != ["importlib-metadata"] or receipt["preserved_other_pins"] != 18: raise ValueError("Unexpected dependency scope")
if receipt["source_result"]["coverage"] < 80: raise ValueError("Coverage below required floor")
print("Verified metadata upgrade evidence")
