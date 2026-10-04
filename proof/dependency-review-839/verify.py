from pathlib import Path
import argparse
import gzip
import hashlib
import json
import re

parser = argparse.ArgumentParser()
parser.add_argument('--check-source', action='store_true', help='Also compare this checkout with the historical tested source')
args = parser.parse_args()
root = Path(__file__).resolve().parent
for name, expected in json.loads((root / "manifest.json").read_text(encoding="utf-8")).items():
    data = (root / name).read_bytes()
    if name.endswith(".json"): data = data.replace(b"\r\n", b"\n")
    if hashlib.sha256(data).hexdigest() != expected: raise ValueError(f"Artifact hash mismatch: {name}")
receipt = json.loads((root / "receipt.json").read_text(encoding="utf-8"))
required_commands = {
    'venv', 'hash-install', 'sdk-install-build-isolation', 'pip-check',
    'metadata-smoke', 'focused-guard', 'source-suite-r2', 'ruff-make-final',
    'bandit', 'floor-guard', 'release-guard', 'review-readiness',
    'readme-sync', 'wheel-build',
    'merged-pr-834', 'merged-pr-835', 'merged-pr-836', 'merged-pr-838',
    'main-ci-37170840939', 'main-ci-37171935709',
    'main-ci-37172114738', 'main-ci-37173337552',
}
names = [command['name'] for command in receipt['commands']]
if len(names) != len(set(names)) or not required_commands.issubset(names):
    raise ValueError('Missing or duplicate required command evidence')
required_sources = {
    '.github/requirements/ci-tools.in', '.github/requirements/ci-tools.txt',
    'scripts/review_readiness_guard.py',
}
if set(receipt['source_hashes']) != required_sources:
    raise ValueError('Missing or unexpected tested source evidence')
for command in receipt["commands"]:
    if not command['argv'] or not all(isinstance(arg, str) and arg for arg in command['argv']):
        raise ValueError('Invalid recorded command')
    if not isinstance(command['cwd'], str) or not re.match(r'^[A-Za-z]:[\\/]', command['cwd']):
        raise ValueError('Missing absolute Windows working directory')
    if command["name"] in {"sdk-install", "ruff-ci"}:
        if command["exit"] != 1 or command["expected"] != 0: raise ValueError("Initial failure record changed")
        continue
    if command["exit"] != command["expected"]: raise ValueError(f"Unexpected exit: {command['name']}")
source_log = gzip.decompress((root / 'source-suite-r2.log.gz').read_bytes()).decode('utf-8')
if not re.search(r'platform win32 -- Python 3\.11\.9\b', source_log):
    raise ValueError('Missing actual Windows Python3.11 source-test platform')
for path, expected in receipt['source_hashes'].items():
    snapshot = gzip.decompress((root / (Path(path).name + '.gz')).read_bytes())
    if hashlib.sha256(snapshot).hexdigest() != expected:
        raise ValueError('Tested source snapshot differs: ' + path)
    if args.check_source:
        data = (root.parents[1] / path).read_bytes().replace(b'\r\n', b'\n')
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Current checkout differs from historical tested source: ' + path)
if receipt["changed_packages"] != ["importlib-metadata"] or receipt["preserved_other_pins"] != 18: raise ValueError("Unexpected dependency scope")
if receipt["source_result"]["coverage"] < 80: raise ValueError("Coverage below required floor")
print("Verified metadata upgrade evidence")
