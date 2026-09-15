"""Scan every post, image label, and image description; retain exact input hashes."""
import hashlib
import json
from pathlib import Path

import defluff

root = Path(__file__).parent
lexicon = defluff.load_lexicon(no_project_overlay=True)
for name in ("linkedin", "x", "image-copy", "alt"):
    raw = (root / f"{name}.txt").read_bytes()
    result = defluff.to_json(defluff.detect(raw.decode("utf-8-sig"), lexicon=lexicon))
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    (root / f"{name}-slop.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(name, result["slop_score"], result["spans"])
    assert result["slop_score"] <= 0.08
