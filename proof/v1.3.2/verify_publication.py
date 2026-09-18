"""Fail if 1.3.2 publication receipts disagree with the shipped package."""
import json
from pathlib import Path

root = Path(__file__).parent
pypi = json.loads((root / "pypi.json").read_text(encoding="utf-8"))
assert pypi["info"]["version"] == "1.3.2"
assert pypi["info"]["yanked"] is False
smoke = json.loads((root / "public-smoke.json").read_text(encoding="utf-8"))
assert smoke["version"] == "1.3.2"
assert "site-packages" in smoke["import_path"]
assert all(item["exit"] == 0 for item in smoke["results"])
demo = json.loads((root / "public-demo.json").read_text(encoding="utf-8"))
assert demo["version"] == "1.3.2"
assert demo["recorded_tokens"] == 200
assert demo["recorded_calls"] == 1
assert demo["include_usage"] is True
assert demo["network_calls"] == 0
print("passed")
