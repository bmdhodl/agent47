from pathlib import Path
import hashlib
import json
root = Path(__file__).resolve().parent
manifest = json.loads((root / "manifest.json").read_text())
for name, expected in manifest.items():
    data = (root / name).read_bytes()
    if name == "receipt.json":
        data = data.replace(b"\r\n", b"\n")
    assert hashlib.sha256(data).hexdigest() == expected, name
receipt = json.loads((root / "receipt.json").read_text())
assert all(command["exit"] == 0 for command in receipt["commands"])
print(f"Verified {len(manifest)} dependency-review artifacts")
