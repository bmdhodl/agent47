"""Weekly distribution pulse for AgentGuard.

Pulls the server-side signals AgentGuard is allowed to rely on (PyPI, npm,
GitHub) and prints them split into two blocks:

- HUMAN SIGNAL  : stars, external issues, unique viewers, referrers
- MACHINE VOLUME: raw downloads and clones, which are dominated by CI/mirrors

The split exists on purpose. Headline download counts for a zero-dependency,
local-first SDK are mostly automation. This script keeps the human-adoption
numbers from getting buried under that noise so the roadmap tracks the metric
that matters.

Stdlib only. Public APIs go over urllib. The authenticated GitHub traffic
endpoints (views/clones/referrers/paths) go through `gh api`; if `gh` is
missing or unauthenticated those rows are skipped with a clear note rather
than failing the whole report.

Usage:
    python scripts/sdk_pulse.py            # human-readable report
    python scripts/sdk_pulse.py --json     # machine-readable snapshot
    python scripts/sdk_pulse.py --append-history proof/pulse/history.jsonl
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

REPO_OWNER = "bmdhodl"
REPO_NAME = "agent47"
REPO = f"{REPO_OWNER}/{REPO_NAME}"
PYPI_PACKAGE = "agentguard47"
NPM_PACKAGE = "@agentguard47/mcp-server"

HTTP_TIMEOUT = 15  # seconds; one slow source must not hang the report
USER_AGENT = "agentguard-pulse/1.0 (+https://github.com/bmdhodl/agent47)"


class SourceError(Exception):
    """A single data source failed. Reported inline, does not abort the run."""


def _get_json(url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise SourceError(f"{url}: {exc}") from exc


def _gh_api(path: str) -> Any:
    """Call an authenticated GitHub API endpoint via the gh CLI.

    Returns parsed JSON, or raises SourceError if gh is unavailable, the user
    is not authenticated, or the call fails.
    """
    if shutil.which("gh") is None:
        raise SourceError("gh CLI not found on PATH")
    try:
        result = subprocess.run(
            ["gh", "api", path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=HTTP_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SourceError(f"gh api {path}: {exc}") from exc
    if result.returncode != 0:
        raise SourceError(f"gh api {path}: {result.stderr.strip() or 'failed'}")
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise SourceError(f"gh api {path}: invalid JSON") from exc


def _sum_by_category(rows: list[dict[str, Any]]) -> Counter:
    counter: Counter = Counter()
    for row in rows:
        counter[row["category"]] += row["downloads"]
    return counter


def collect_pypi() -> dict[str, Any]:
    recent = _get_json(f"https://pypistats.org/api/packages/{PYPI_PACKAGE}/recent")
    overall = _get_json(f"https://pypistats.org/api/packages/{PYPI_PACKAGE}/overall")
    by_system = _get_json(f"https://pypistats.org/api/packages/{PYPI_PACKAGE}/system")
    by_python = _get_json(
        f"https://pypistats.org/api/packages/{PYPI_PACKAGE}/python_minor"
    )
    overall_rows = overall["data"]
    systems = _sum_by_category(by_system["data"])
    linux = systems.get("Linux", 0)
    total_with_os = sum(v for k, v in systems.items() if k != "null")
    return {
        "last_day": recent["data"]["last_day"],
        "last_week": recent["data"]["last_week"],
        "last_month": recent["data"]["last_month"],
        "total_recorded": sum(r["downloads"] for r in overall_rows),
        "range": [overall_rows[0]["date"], overall_rows[-1]["date"]],
        "by_system": dict(systems.most_common()),
        "by_python": dict(_sum_by_category(by_python["data"]).most_common()),
        "linux_share": round(linux / total_with_os, 3) if total_with_os else None,
    }


def collect_npm() -> dict[str, Any]:
    base = "https://api.npmjs.org/downloads/point"
    week = _get_json(f"{base}/last-week/{NPM_PACKAGE}")
    month = _get_json(f"{base}/last-month/{NPM_PACKAGE}")
    return {"last_week": week["downloads"], "last_month": month["downloads"]}


def collect_pypi_latest() -> str:
    data = _get_json(f"https://pypi.org/pypi/{PYPI_PACKAGE}/json")
    return data["info"]["version"]


def collect_npm_latest() -> str:
    data = _get_json(f"https://registry.npmjs.org/{NPM_PACKAGE}")
    return data["dist-tags"]["latest"]


def collect_github_public() -> dict[str, Any]:
    data = _get_json(f"https://api.github.com/repos/{REPO}")
    return {
        "stars": data["stargazers_count"],
        "forks": data["forks_count"],
        "watchers": data["subscribers_count"],
        "open_issues": data["open_issues_count"],
    }


def collect_github_traffic() -> dict[str, Any]:
    views = _gh_api(f"repos/{REPO}/traffic/views")
    clones = _gh_api(f"repos/{REPO}/traffic/clones")
    referrers = _gh_api(f"repos/{REPO}/traffic/popular/referrers")
    return {
        "views_14d": views["count"],
        "views_uniques_14d": views["uniques"],
        "clones_14d": clones["count"],
        "clones_uniques_14d": clones["uniques"],
        "referrers": [
            {"source": r["referrer"], "count": r["count"], "uniques": r["uniques"]}
            for r in referrers
        ],
    }


def collect_external_issues() -> dict[str, Any]:
    """Count open issues NOT authored by the repo owner.

    External issues are the clearest free-text signal of real human use, so
    they get pulled out separately from the owner's own tracking issues.
    """
    issues = _gh_api(
        f"repos/{REPO}/issues?state=open&per_page=100&filter=all"
    )
    external = [
        i
        for i in issues
        if "pull_request" not in i
        and i["user"]["login"] != REPO_OWNER
        and i["user"].get("type") != "Bot"
        and not i["user"]["login"].endswith("[bot]")
    ]
    return {
        "external_open_issues": len(external),
        "external_authors": sorted({i["user"]["login"] for i in external}),
    }


def _safe(label: str, fn) -> tuple[Any, str | None]:
    try:
        return fn(), None
    except SourceError as exc:
        return None, str(exc)


def collect_all() -> dict[str, Any]:
    snapshot: dict[str, Any] = {"repo": REPO, "errors": {}}
    for key, fn in (
        ("pypi", collect_pypi),
        ("pypi_latest", collect_pypi_latest),
        ("npm", collect_npm),
        ("npm_latest", collect_npm_latest),
        ("github", collect_github_public),
        ("github_traffic", collect_github_traffic),
        ("issues", collect_external_issues),
    ):
        value, error = _safe(key, fn)
        if error is None:
            snapshot[key] = value
        else:
            snapshot["errors"][key] = error
    return snapshot


def _fmt(value: Any) -> str:
    return "n/a" if value is None else str(value)


def render(snapshot: dict[str, Any]) -> str:
    lines: list[str] = []
    out = lines.append

    out("AgentGuard distribution pulse")
    out(f"  repo: {snapshot['repo']}")
    out(
        "  latest published: "
        f"PyPI {_fmt(snapshot.get('pypi_latest'))} | "
        f"npm {_fmt(snapshot.get('npm_latest'))}"
    )
    out("")

    gh = snapshot.get("github") or {}
    traffic = snapshot.get("github_traffic") or {}
    issues = snapshot.get("issues") or {}
    out("HUMAN SIGNAL  (the metric that matters)")
    out(f"  GitHub stars            : {_fmt(gh.get('stars'))}")
    out(f"  Forks                   : {_fmt(gh.get('forks'))}")
    out(f"  External open issues    : {_fmt(issues.get('external_open_issues'))}")
    if issues.get("external_authors"):
        out(f"    authors               : {', '.join(issues['external_authors'])}")
    out(f"  Unique viewers (14d)    : {_fmt(traffic.get('views_uniques_14d'))}")
    if traffic.get("referrers"):
        out("  Referrers (where humans arrive from):")
        for ref in traffic["referrers"]:
            out(f"    - {ref['source']}: {ref['count']} ({ref['uniques']} uniq)")
    elif "github_traffic" in snapshot.get("errors", {}):
        out("  Referrers               : n/a (gh traffic unavailable)")
    else:
        out("  Referrers               : none recorded")
    out("")

    pypi = snapshot.get("pypi") or {}
    npm = snapshot.get("npm") or {}
    out("MACHINE VOLUME  (mostly CI / mirrors - caveat heavily)")
    out(
        "  PyPI downloads          : "
        f"day {_fmt(pypi.get('last_day'))} | "
        f"week {_fmt(pypi.get('last_week'))} | "
        f"month {_fmt(pypi.get('last_month'))}"
    )
    if pypi.get("range"):
        out(
            f"  PyPI total recorded     : {_fmt(pypi.get('total_recorded'))} "
            f"({pypi['range'][0]} -> {pypi['range'][1]})"
        )
    if pypi.get("linux_share") is not None:
        out(
            f"  PyPI Linux share        : {pypi['linux_share']:.0%} "
            "(high = CI-dominated)"
        )
    out(
        "  npm downloads           : "
        f"week {_fmt(npm.get('last_week'))} | month {_fmt(npm.get('last_month'))}"
    )
    if traffic.get("clones_14d") is not None:
        clones = traffic["clones_14d"]
        uniques = traffic["clones_uniques_14d"] or 1
        ratio = clones / uniques
        out(
            f"  Clones (14d)            : {clones} total / "
            f"{traffic['clones_uniques_14d']} unique = {ratio:.1f}x per cloner"
        )
        if ratio >= 5:
            out("    ^ ratio >= 5x strongly indicates automated CI, not humans")
    out("")

    if snapshot.get("errors"):
        out("Skipped sources:")
        for key, error in snapshot["errors"].items():
            out(f"  - {key}: {error}")

    return "\n".join(lines)


def append_history(path: Path, snapshot: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(snapshot, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit the raw snapshot as JSON instead of a report",
    )
    parser.add_argument(
        "--append-history",
        metavar="PATH",
        type=Path,
        help="append the JSON snapshot as one line to a history file",
    )
    args = parser.parse_args(argv)

    snapshot = collect_all()

    if args.append_history:
        append_history(args.append_history, snapshot)

    if args.json:
        print(json.dumps(snapshot, indent=2, sort_keys=True))
    else:
        print(render(snapshot))

    # Fail loudly only if every source failed (likely no network), so the
    # report is still useful when a single endpoint is down.
    data_keys = [k for k in snapshot if k not in ("repo", "errors")]
    if not data_keys:
        print("\nERROR: no data sources reachable", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
