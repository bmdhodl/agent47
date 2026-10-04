from pathlib import Path
import hashlib, json
root=Path(__file__).resolve().parent
for name,expected in json.loads((root/"manifest.json").read_text(encoding="utf-8")).items():
    data=(root/name).read_bytes()
    if name.endswith(".json"): data=data.replace(b"\r\n",b"\n")
    if hashlib.sha256(data).hexdigest()!=expected:
        raise ValueError(f"Artifact hash mismatch: {name}")
receipt=json.loads((root/"receipt.json").read_text(encoding="utf-8"))
for c in receipt["commands"]:
    if c["name"] in receipt["acceptance"] and c["exit"]!=c["expected"]:
        raise ValueError(f"Acceptance command failed: {c['name']}")
if receipt["source_result"]!=dict(passed=1477,skipped=114,coverage=91.36):
    raise ValueError("Unexpected source test result")
print("Verified dependency review artifacts")
