#!/usr/bin/env python3
"""Build an activation snapshot from public counts or local fixtures.

Offline unless --fetch-public is set. That flag reads PyPI release metadata,
PyPI Stats, the npm downloads API and the GitHub Actions run list for
published-wheel.yml. It does not read identities or site events. GitHub reads
work without a token; set GITHUB_TOKEN or GH_TOKEN to raise the rate limit.
"""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

PYPI_URL = "https://pypistats.org/api/packages/agentguard47/overall?mirrors=false"
PYTHON_MINOR_URL = "https://pypistats.org/api/packages/agentguard47/python_minor?mirrors=false"
PYPI_RELEASES_URL = "https://pypi.org/pypi/agentguard47/json"
NPM_PACKAGE = "@agentguard47/mcp-server"
# Historical offline fixture baseline. Public refreshes always read PyPI metadata.
RELEASE_DATES = ("2026-09-12", "2026-09-15", "2026-09-18", "2026-09-24")
OFF_PUBLISH_METHOD = (
    "Off-publish-day figures sum without_mirrors downloads on the window days whose "
    "date is not in exclusions.publish_dates, divided by the count of those days; "
    "publish-day rows stay in the data, annotated, and are never deleted. The "
    "real-interpreter figures read python_minor?mirrors=false and count only rows "
    "whose category is not null. They are raw; net_of_own_ci also removes the "
    "installs listed in exclusions.published_wheel_ci."
)
INTERPRETER_CAVEAT = (
    "a null interpreter almost always means tooling rather than a person, and a real "
    "interpreter still does not prove a distinct person"
)
GITHUB_API = "https://api.github.com"
GITHUB_REPO = "bmdhodl/agent47"
OWN_CI_WORKFLOW = ".github/workflows/published-wheel.yml"
OWN_CI_RUNS_URL = f"{GITHUB_API}/repos/{GITHUB_REPO}/actions/workflows/published-wheel.yml/runs"
WHEEL_INSTALL_STEP = "Install the published wheel and run the offline example"
OWN_CI_METHOD = (
    "published-wheel.yml installs the published wheel from PyPI once per matrix job, "
    "with a real interpreter. Each run in the reporting window is read from the GitHub "
    "Actions API with its run id, date and count of completed wheel-install jobs, which "
    "are jobs whose install step concluded success. net_of_own_ci subtracts those jobs "
    "from the real-interpreter rows of the same off-publish day, never below zero for a "
    "day. Publish days are already outside the sum and are not subtracted again. Rows "
    "stay in the data and are never deleted."
)
NET_OF_OWN_CI_BOUND = (
    "upper bound: other CI, reinstalls and tooling that reports an interpreter still "
    "count here, and an interpreter does not identify a person"
)


def _window(rows: list[dict[str, Any]], end: date, days: int) -> tuple[str, str, int, list[str]]:
    start = end - timedelta(days=days - 1)
    present = {row["date"] for row in rows if start.isoformat() <= row["date"] <= end.isoformat()}
    total = sum(
        int(row["downloads"])
        for row in rows
        if start.isoformat() <= row["date"] <= end.isoformat()
    )
    missing = []
    cursor = start
    while cursor <= end:
        if cursor.isoformat() not in present:
            missing.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return start.isoformat(), end.isoformat(), total, missing


def _off_publish(
    rows: list[dict[str, Any]], start: str, end: str, publish_dates: tuple[str, ...]
) -> dict[str, Any]:
    """Downloads on window days that are not publish days, and the per-day mean.

    Publish-day rows are skipped in the sum, not removed from the data.
    Callers select the overall no-mirror category or real-interpreter rows first;
    multiple interpreter categories on one date are intentionally aggregated.
    """
    publish = sorted(day for day in publish_dates if start <= day <= end)
    skip = set(publish)
    downloads = sum(
        int(row["downloads"])
        for row in rows
        if start <= row["date"] <= end and row["date"] not in skip
    )
    day_count = 0
    cursor = date.fromisoformat(start)
    last = date.fromisoformat(end)
    while cursor <= last:
        if cursor.isoformat() not in skip:
            day_count += 1
        cursor += timedelta(days=1)
    return {
        "downloads": downloads,
        "day_count": day_count,
        "mean_per_day": round(downloads / day_count, 1) if day_count else 0.0,
        "publish_dates_excluded": publish,
    }


def _real_interpreter_rows(python_minor_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep only rows that report an actual Python minor version.

    pypistats returns the string "null" for an unknown interpreter.
    """
    kept = []
    for row in python_minor_rows:
        category = row.get("category")
        if category is None or str(category).strip().lower() == "null":
            continue
        kept.append({"date": row["date"], "downloads": int(row["downloads"])})
    return kept


def _window_total(rows: list[dict[str, Any]], start: str, end: str) -> int:
    return sum(int(row["downloads"]) for row in rows if start <= row["date"] <= end)


def _net_of_own_ci(
    interpreter_rows: list[dict[str, Any]],
    start: str,
    end: str,
    publish_dates: tuple[str, ...],
    ci_runs: list[dict[str, Any]],
) -> dict[str, Any]:
    """Real-interpreter off-publish figures less our own published-wheel installs.

    A day never goes below zero. Days where our jobs outnumber the rows are listed.
    """
    skip = set(publish_dates)
    ci_by_day: Counter[str] = Counter()
    for run in ci_runs:
        if start <= run["date"] <= end and run["date"] not in skip:
            ci_by_day[run["date"]] += int(run["wheel_install_jobs"])
    real_by_day: Counter[str] = Counter()
    for row in interpreter_rows:
        if start <= row["date"] <= end:
            real_by_day[row["date"]] += int(row["downloads"])
    net_rows = [
        {"date": day, "downloads": max(0, real_by_day[day] - ci_by_day[day])}
        for day in sorted(set(real_by_day) | set(ci_by_day))
    ]
    block = _off_publish(net_rows, start, end, publish_dates)
    block["own_ci_wheel_install_jobs"] = sum(ci_by_day.values())
    block["own_ci_dates"] = sorted(day for day, jobs in ci_by_day.items() if jobs)
    block["days_clamped_at_zero"] = sorted(
        day for day, jobs in ci_by_day.items() if real_by_day[day] < jobs
    )
    block["bound"] = NET_OF_OWN_CI_BOUND
    return block


def _without_mirrors_rows(pypi_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (
            {"date": row["date"], "downloads": int(row["downloads"])}
            for row in pypi_rows
            if row.get("category", "without_mirrors") == "without_mirrors"
        ),
        key=lambda row: row["date"],
    )


def _series_end(rows: list[dict[str, Any]], retrieved: date) -> date:
    return date.fromisoformat(rows[-1]["date"]) if rows else retrieved


def _utc_day(stamp: Any) -> str:
    if not isinstance(stamp, str):
        raise TypeError("missing GitHub timestamp")
    moment = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("GitHub timestamp needs a timezone")
    return moment.astimezone(timezone.utc).date().isoformat()


def _github_list(url: str, key: str) -> list[dict[str, Any]]:
    """Read every page of a GitHub list endpoint. A short or malformed page raises."""
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        payload = _get_json(f"{url}&per_page=100&page={page}")
        batch = payload.get(key)
        total = payload.get("total_count")
        if not isinstance(batch, list) or not isinstance(total, int):
            raise TypeError(f"GitHub response has no {key} list or total_count")
        if not all(isinstance(item, dict) for item in batch):
            raise TypeError(f"GitHub {key} entry is not an object")
        items.extend(batch)
        if len(items) >= total:
            return items
        if not batch:
            raise ValueError(f"GitHub {key} stopped at {len(items)} of {total}")
        page += 1


def _run_records(run: dict[str, Any], jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """One record per run and UTC day, with the count of finished wheel installs."""
    run_id = run["id"]
    per_day: Counter[str] = Counter()
    for job in jobs:
        for step in job.get("steps") or []:
            if step.get("name") == WHEEL_INSTALL_STEP and step.get("conclusion") == "success":
                per_day[_utc_day(step.get("started_at") or job.get("started_at"))] += 1
    if not per_day:
        if run.get("conclusion") == "success":
            raise ValueError(
                f"run {run_id} succeeded without the {WHEEL_INSTALL_STEP!r} install step"
            )
        per_day[_utc_day(run.get("created_at"))] = 0
    return [
        {"run_id": run_id, "date": day, "event": run.get("event"), "wheel_install_jobs": count}
        for day, count in sorted(per_day.items())
    ]


def fetch_published_wheel_runs(start: str, end: str) -> list[dict[str, Any]]:
    """Read published-wheel.yml runs for the window from the GitHub Actions API.

    Re-run attempts count, because each attempt installs the wheel again.
    """
    created_from = (date.fromisoformat(start) - timedelta(days=1)).isoformat()
    runs = _github_list(f"{OWN_CI_RUNS_URL}?created={created_from}..{end}", "workflow_runs")
    records: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run.get("id"), int):
            raise TypeError("GitHub workflow run has no id")
        jobs = _github_list(
            f"{GITHUB_API}/repos/{GITHUB_REPO}/actions/runs/{run['id']}/jobs?filter=all",
            "jobs",
        )
        records.extend(_run_records(run, jobs))
    return sorted(records, key=lambda record: (record["date"], record["run_id"]))


def _run_records_from_file(payload: Any) -> list[dict[str, Any]]:
    """Validate run records saved from an earlier API read, for offline fixtures."""
    if not isinstance(payload, list):
        raise TypeError("published-wheel run records must be a list")
    for record in payload:
        if not (
            isinstance(record, dict)
            and isinstance(record.get("run_id"), int)
            and isinstance(record.get("date"), str)
            and isinstance(record.get("wheel_install_jobs"), int)
        ):
            raise TypeError("published-wheel run record needs run_id, date and wheel_install_jobs")
    return payload


def _publish_dates(metadata: dict[str, Any]) -> tuple[str, ...]:
    """Use the first artifact upload in each release, in UTC."""
    releases = metadata.get("releases")
    if not isinstance(releases, dict):
        raise ValueError("missing PyPI release inventory")
    days = set()
    for files in releases.values():
        if not isinstance(files, list):
            raise ValueError("invalid PyPI release files")
        if not files:
            continue
        uploads = []
        for file in files:
            if not isinstance(file, dict):
                raise ValueError("invalid PyPI artifact")
            timestamp = file.get("upload_time_iso_8601")
            if not isinstance(timestamp, str):
                raise ValueError("missing PyPI upload timestamp")
            uploaded = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if uploaded.tzinfo is None:
                raise ValueError("PyPI upload timestamp needs a timezone")
            uploads.append(uploaded.astimezone(timezone.utc))
        days.add(min(uploads).date().isoformat())
    if not days:
        raise ValueError("no PyPI release uploads found")
    return tuple(sorted(days))


def build_snapshot(
    *,
    retrieved_at: str,
    pypi_rows: list[dict[str, Any]] | None,
    npm: dict[str, Any] | None,
    feedback_reports: list[dict[str, Any]] | None,
    pypi_error: str | None = None,
    npm_error: str | None = None,
    python_minor_rows: list[dict[str, Any]] | None = None,
    python_minor_error: str | None = None,
    release_dates: tuple[str, ...] | None = RELEASE_DATES,
    releases_error: str | None = None,
    published_wheel_runs: list[dict[str, Any]] | None = None,
    published_wheel_error: str | None = None,
) -> dict[str, Any]:
    retrieved = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00")).date()
    sources: dict[str, Any] = {
        "github_traffic": {
            "status": "unavailable",
            "reason": "GitHub traffic API is not available to this refresh",
        },
        "site_events": {
            "status": "unavailable",
            "reason": "no fresh site-event export was retrieved",
        },
    }
    snapshot: dict[str, Any] = {
        "as_of": retrieved.isoformat(),
        "retrieved_at": retrieved_at,
        "feedback_reports": feedback_reports or [],
        "accepted_external_contributions": 0,
        "sources": sources,
        "unknowns": [
            "unique PyPI installers",
            "repeat use without a consented reporter",
            "repository visits; GitHub traffic was not retrieved",
            "site events were not retrieved; 2026-09-18 landing-page install_intent rows stay navigation in that baseline and are not reused here",
            "real-workflow activation; demo success is not production use",
        ],
        "exclusions": {
            "publish_dates": list(release_dates or ()),
            "mirrors": "PyPI counts use without_mirrors",
            "landing_page_install_intent": "a marketing-origin target never counts as install",
            "simulated_reports": "a simulated report cannot count as demand",
        },
        "dedup": {"pypi": "none; each download is a package event, not a unique user"},
    }
    own_ci_available = not published_wheel_error and published_wheel_runs is not None
    own_ci: dict[str, Any] = {"workflow": OWN_CI_WORKFLOW, "method": OWN_CI_METHOD, "source": OWN_CI_RUNS_URL}
    snapshot["exclusions"]["published_wheel_ci"] = own_ci
    if not own_ci_available:
        own_ci["status"] = "unavailable"
        own_ci["reason"] = published_wheel_error or "published-wheel.yml runs not supplied"
    if pypi_error or pypi_rows is None:
        sources["pypi"] = {"status": "unavailable", "url": PYPI_URL, "reason": pypi_error or "not supplied"}
        snapshot["data_lag"] = {"pypi": "unavailable"}
    else:
        snapshot["unknowns"].append(INTERPRETER_CAVEAT)
        rows = _without_mirrors_rows(pypi_rows)
        end = _series_end(rows, retrieved)
        start7, end7, total7, _missing7 = _window(rows, end, 7)
        start30, end30, total30, missing30 = _window(rows, end, 30)
        if own_ci_available:
            own_ci["runs"] = [
                run for run in published_wheel_runs or [] if start30 <= run["date"] <= end30
            ]
        lag_days = []
        cursor = end + timedelta(days=1)
        while cursor <= retrieved:
            lag_days.append(cursor.isoformat())
            cursor += timedelta(days=1)
        by_date = {row["date"]: row["downloads"] for row in rows}
        snapshot["pypi"] = {
            "without_mirrors_7d": total7,
            "without_mirrors_30d": total30,
            "missing_days": missing30 + [day for day in lag_days if day not in missing30],
            "release_day_events": [
                {"date": day, "downloads": by_date.get(day, 0), "annotated_not_removed": True}
                for day in (release_dates or ())
                if start30 <= day <= end30
            ],
        }
        interpreter_rows = _real_interpreter_rows(list(python_minor_rows or []))
        interpreter_available = not python_minor_error and python_minor_rows is not None
        off_publish: dict[str, Any] = {"method": OFF_PUBLISH_METHOD, "caveat": INTERPRETER_CAVEAT}
        for label, (w_start, w_end, w_total) in {
            "window_7d": (start7, end7, total7),
            "window_30d": (start30, end30, total30),
        }.items():
            if release_dates is None:
                continue
            block = _off_publish(rows, w_start, w_end, release_dates)
            block["window"] = {"start": w_start, "end": w_end}
            block["window_downloads"] = w_total
            if interpreter_available:
                real = _off_publish(interpreter_rows, w_start, w_end, release_dates)
                real["window_downloads"] = _window_total(interpreter_rows, w_start, w_end)
                real["source"] = PYTHON_MINOR_URL
                if own_ci_available:
                    real["net_of_own_ci"] = _net_of_own_ci(
                        interpreter_rows, w_start, w_end, release_dates, published_wheel_runs or []
                    )
                else:
                    real["net_of_own_ci"] = {
                        "status": "unavailable",
                        "reason": own_ci["reason"],
                        "source": OWN_CI_RUNS_URL,
                    }
                block["real_interpreter"] = real
            else:
                block["real_interpreter"] = {
                    "status": "unavailable",
                    "reason": python_minor_error or "not supplied",
                    "source": PYTHON_MINOR_URL,
                }
            off_publish[label] = block
        snapshot["pypi"]["off_publish_days"] = off_publish
        if release_dates is None:
            off_publish["status"] = "unavailable"
            off_publish["reason"] = releases_error or "release dates not supplied"
            snapshot["unknowns"].append("off-publish downloads: release dates unavailable")
        if interpreter_available:
            sources["pypi_python_minor"] = {
                "status": "ok",
                "url": PYTHON_MINOR_URL,
                "retrieved_at": retrieved_at,
            }
        else:
            sources["pypi_python_minor"] = {
                "status": "unavailable",
                "url": PYTHON_MINOR_URL,
                "reason": python_minor_error or "not supplied",
            }
        snapshot["windows"] = {
            "pypi_7d": {"start": start7, "end": end7, "query": PYPI_URL, "note": "calendar window, without_mirrors"},
            "pypi_30d": {"start": start30, "end": end30, "query": PYPI_URL, "note": "calendar window, without_mirrors"},
        }
        snapshot["data_lag"] = {
            "pypi": f"series ends {end.isoformat()}; retrieved {retrieved.isoformat()}; later days are lag, not zero"
        }
        sources["pypi"] = {"status": "ok", "url": PYPI_URL, "retrieved_at": retrieved_at}
    if npm_error or npm is None:
        sources["npm"] = {"status": "unavailable", "reason": npm_error or "not supplied"}
    else:
        snapshot["npm"] = {"downloads_window": int(npm.get("downloads") or 0)}
        snapshot.setdefault("windows", {})["npm_30d"] = {
            "start": npm.get("start"),
            "end": npm.get("end"),
            "query": f"https://api.npmjs.org/downloads/point/{npm.get('start')}:{npm.get('end')}/{NPM_PACKAGE}",
        }
        sources["npm"] = {"status": "ok", "retrieved_at": retrieved_at}
    return snapshot


def _get_json(url: str) -> dict[str, Any]:
    headers = {"User-Agent": "agentguard-activation-refresh"}
    if url.startswith(f"{GITHUB_API}/"):
        headers["Accept"] = "application/vnd.github+json"
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object from {url}")
    return payload


def fetch_public(retrieved_at: str) -> dict[str, Any]:
    pypi_error = npm_error = python_minor_error = None
    pypi_rows = npm = python_minor_rows = None
    release_dates = None
    releases_error = None
    try:
        release_dates = _publish_dates(_get_json(PYPI_RELEASES_URL))
    except Exception as exc:
        releases_error = f"{type(exc).__name__}: {exc}"
    try:
        pypi_rows = list(_get_json(PYPI_URL).get("data") or [])
    except Exception as exc:
        pypi_error = type(exc).__name__
    try:
        python_minor_rows = list(_get_json(PYTHON_MINOR_URL).get("data") or [])
    except Exception as exc:
        python_minor_error = type(exc).__name__
    retrieved = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00")).date()
    published_wheel_runs = None
    published_wheel_error = "PyPI series unavailable, so there is no reporting window"
    if pypi_rows is not None:
        series_end = _series_end(_without_mirrors_rows(pypi_rows), retrieved)
        try:
            published_wheel_runs = fetch_published_wheel_runs(
                (series_end - timedelta(days=29)).isoformat(), series_end.isoformat()
            )
            published_wheel_error = None
        except (OSError, TypeError, ValueError) as exc:
            published_wheel_error = f"{type(exc).__name__}: {exc}"
    start = (retrieved - timedelta(days=29)).isoformat()
    end = retrieved.isoformat()
    npm_url = f"https://api.npmjs.org/downloads/point/{start}:{end}/{NPM_PACKAGE}"
    try:
        npm = _get_json(npm_url)
    except Exception as exc:
        npm_error = type(exc).__name__
    snapshot = build_snapshot(
        retrieved_at=retrieved_at,
        pypi_rows=pypi_rows,
        npm=npm,
        feedback_reports=[],
        pypi_error=pypi_error,
        npm_error=npm_error,
        python_minor_rows=python_minor_rows,
        python_minor_error=python_minor_error,
        release_dates=release_dates,
        releases_error=releases_error,
        published_wheel_runs=published_wheel_runs,
        published_wheel_error=published_wheel_error,
    )
    snapshot["sources"]["github_actions"] = {
        "status": "unavailable" if published_wheel_error else "ok",
        "url": OWN_CI_RUNS_URL,
        **({"reason": published_wheel_error} if published_wheel_error else {"retrieved_at": retrieved_at}),
    }
    snapshot["sources"]["pypi_releases"] = {
        "status": "unavailable" if releases_error else "ok",
        "url": PYPI_RELEASES_URL,
        **({"reason": releases_error} if releases_error else {"retrieved_at": retrieved_at}),
    }
    return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh an activation snapshot.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fetch-public", action="store_true")
    parser.add_argument("--pypi-json", type=Path)
    parser.add_argument("--npm-json", type=Path)
    parser.add_argument("--python-minor-json", type=Path)
    parser.add_argument("--pypi-releases-json", type=Path, help="Offline PyPI release metadata")
    parser.add_argument(
        "--published-wheel-runs-json",
        type=Path,
        help="Offline published-wheel.yml run records saved from an earlier API read",
    )
    parser.add_argument("--feedback-json", type=Path)
    parser.add_argument("--retrieved-at", default=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    args = parser.parse_args(argv)
    feedback = json.loads(args.feedback_json.read_text(encoding="utf-8")) if args.feedback_json else []
    if args.fetch_public:
        snapshot = fetch_public(args.retrieved_at)
        snapshot["feedback_reports"] = feedback
    else:
        pypi_rows = json.loads(args.pypi_json.read_text(encoding="utf-8")) if args.pypi_json else None
        npm = json.loads(args.npm_json.read_text(encoding="utf-8")) if args.npm_json else None
        python_minor_rows = (
            json.loads(args.python_minor_json.read_text(encoding="utf-8"))
            if args.python_minor_json
            else None
        )
        snapshot = build_snapshot(
            retrieved_at=args.retrieved_at,
            pypi_rows=pypi_rows,
            npm=npm,
            feedback_reports=feedback,
            python_minor_rows=python_minor_rows,
            release_dates=(
                _publish_dates(json.loads(args.pypi_releases_json.read_text(encoding="utf-8")))
                if args.pypi_releases_json else RELEASE_DATES
            ),
            published_wheel_runs=(
                _run_records_from_file(
                    json.loads(args.published_wheel_runs_json.read_text(encoding="utf-8"))
                )
                if args.published_wheel_runs_json else None
            ),
        )
    args.out.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
