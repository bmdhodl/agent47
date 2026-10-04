from pathlib import Path
import hashlib
import json
root = Path(__file__).resolve().parent
manifest = json.loads((root / "manifest.json").read_text())
for name, expected in manifest.items():
    data = (root / name).read_bytes()
    if name == "receipt.json":
        data = data.replace(b"\r\n", b"\n")
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Artifact hash mismatch: {name}")
receipt = json.loads((root / "receipt.json").read_text())
if any(command["exit"] != 0 for command in receipt["commands"]):
    raise ValueError("A retained acceptance command failed")
print(f"Verified {len(manifest)} dependency-review artifacts")
