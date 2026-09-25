"""Slop-scan the visible text of every site page with defluff; write JSON results."""
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import defluff

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).parent


def visible_text(page: str) -> str:
    page = re.sub(r"(?is)<(script|style|pre|code)\b.*?</\1>", " ", page)
    page = re.sub(r"(?s)<[^>]+>", " ", page)
    return re.sub(r"\s+", " ", html.unescape(page)).strip()


lexicon = defluff.load_lexicon(no_project_overlay=True)
label = sys.argv[1] if len(sys.argv) > 1 else "after"
results = {}
for path in sorted((ROOT / "site").rglob("*.html")):
    raw = path.read_bytes()
    result = defluff.to_json(defluff.detect(visible_text(raw.decode("utf-8")), lexicon=lexicon))
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    name = path.relative_to(ROOT / "site").as_posix()
    results[name] = result
    spans = [s.get("text") or s for s in result["spans"]]
    print(f"{name:40s} score={result['slop_score']:.3f} words={result['n_words']:5d} spans={spans}")
(OUT / f"site-slop-{label}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
