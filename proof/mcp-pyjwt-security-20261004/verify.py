from pathlib import Path
import gzip
import hashlib
import json
root=Path(__file__).resolve().parent
for name, expected in json.loads((root/"manifest.json").read_text(encoding="utf-8")).items():
    data=(root/name).read_bytes()
    if name.endswith(".json"): data=data.replace(b"\r\n",b"\n")
    if hashlib.sha256(data).hexdigest()!=expected: raise ValueError("Artifact mismatch: "+name)
receipt=json.loads((root/"receipt.json").read_text(encoding="utf-8"))
required={"baseline-regression","patched-runtime","mcp-suite","mcp-lint","sdk-guardrails","sdk-suite","floor-install-runtime-contract","floor-smoke","floor-pip-check"}
names=[c["name"] for c in receipt["commands"]]
if len(names)!=len(set(names)) or not required.issubset(names): raise ValueError("Missing command evidence")
for command in receipt["commands"]:
    if command["name"] in {"floor-install","floor-install-with-pins"}:
        if command["exit"]!=1 or command["expected"]!=0: raise ValueError("Historical harness failure changed")
        continue
    if command["exit"]!=command["expected"]: raise ValueError("Unexpected exit: "+command["name"])
required_sources={".github/requirements/mcp-budget.in",".github/requirements/mcp-budget.txt","agentguard-mcp/pyproject.toml","agentguard-mcp/tests/test_jwt_dependency.py"}
if set(receipt["source_hashes"])!=required_sources: raise ValueError("Missing source evidence")
for path, expected in receipt["source_hashes"].items():
    if hashlib.sha256(gzip.decompress((root/(Path(path).name+".gz")).read_bytes())).hexdigest()!=expected: raise ValueError("Source snapshot mismatch")
if receipt["compile"]["changed"]!=["pyjwt","pywin32"] or receipt["compile"]["mcp_version"]!="1.30.0": raise ValueError("Unexpected compiler scope")
if receipt["sdk_result"]["coverage"]<80: raise ValueError("Coverage below required floor")
print("Verified MCP1 JWT security evidence")
