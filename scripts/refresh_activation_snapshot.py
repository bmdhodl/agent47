#!/usr/bin/env python3
"""Build an activation snapshot from public counts or local fixtures.

Offline unless --fetch-public is set. That flag reads PyPI release metadata,
PyPI Stats, the npm downloads API and this repository's own GitHub Actions runs.
It does not read identities, GitHub traffic or site events.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.request import HTTPRedirectHandler, Request, build_opener

PYPI_URL = "https://pypistats.org/api/packages/agentguard47/overall?mirrors=false"
PYTHON_MINOR_URL = "https://pypistats.org/api/packages/agentguard47/python_minor?mirrors=false"
PYPI_RELEASES_URL = "https://pypi.org/pypi/agentguard47/json"
NPM_PACKAGE = "@agentguard47/mcp-server"
GITHUB_API_ROOT = "https://api.github.com/repos/bmdhodl/agent47"
PUBLISHED_WHEEL_WORKFLOW = ".github/workflows/published-wheel.yml"
RUNS_PAGE_SIZE = 100
PUBLISHED_WHEEL_RUNS_URL = (
    f"{GITHUB_API_ROOT}/actions/workflows/published-wheel.yml/runs"
    f"?per_page={RUNS_PAGE_SIZE}"
)
# The matrix job that installs the wheel. The workflow's resolve job installs
# nothing, so counting every successful job would over-subtract.
WHEEL_INSTALL_STEP = "Install the published wheel and run the offline example"
# The 30-day window plus room for pypistats lag, so the run inventory always
# covers the widest window the snapshot reports.
OWN_CI_LOOKBACK_DAYS = 45
# Historical offline fixture baseline. Public refreshes always read PyPI metadata.
RELEASE_DATES = ("2026-09-12", "2026-09-15", "2026-09-18", "2026-09-24")
OFF_PUBLISH_METHOD = (
    "Off-publish-day figures sum without_mirrors downloads on the window days whose "
    "date is not in exclusions.publish_dates, divided by the count of those days; "
    "publish-day rows stay in the data, annotated, and are never deleted. The "
    "real-interpreter figures read python_minor?mirrors=false and count only rows "
    "whose category is not null. Inside real_interpreter, downloads and "
    "mean_per_day are the raw figures; net_of_own_ci holds the same figures net of "
    "our own published-wheel CI."
)
OWN_CI_EXCLUSION = (
    f"a wheel-install job of our own {PUBLISHED_WHEEL_WORKFLOW} is not an outside user"
)
OWN_CI_METHOD = (
    f"Runs of {PUBLISHED_WHEEL_WORKFLOW} are read from the GitHub Actions API, dated by "
    "the UTC day the run started, and counted by the jobs that completed the step named "
    f"'{WHEEL_INSTALL_STEP}'. Jobs on a window day that is not a publish date are "
    "subtracted from the raw off-publish-day real-interpreter downloads; a run on a "
    "publish date is not subtracted, because that whole day is already out of the sum. "
    "Each day's subtraction is capped at that day's real-interpreter rows, and any "
    "surplus is reported as jobs_not_subtracted rather than taken from another day. "
    "No row is deleted."
)
OWN_CI_UPPER_BOUND = (
    "the net figure is still an upper bound: other CI, reinstalls and "
    "mirrors-excluded tooling also use real interpreters, an interpreter does not "
    "identify a person, and one job is not provably one download"
)
INTERPRETER_CAVEAT = (
    "a null interpreter almost always means tooling rather than a person, and a real "
    "interpreter still does not prove a distinct person"
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
    raw: dict[str, Any],
    interpreter_rows: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    start: str,
    end: str,
    publish_dates: tuple[str, ...],
    runs_from: str | None = None,
) -> dict[str, Any]:
    """Subtract our own published-wheel installs from a raw real-interpreter figure.

    Each day's subtraction is capped at that day's real-interpreter rows, so our
    own jobs can never eat another day's genuine downloads. A run that fell on a
    publish date is not subtracted: that whole day is already outside the
    off-publish sum, so subtracting it would exclude it twice. Nothing is deleted
    from the data.

    ``runs_from`` is the earliest day the run inventory covers. A caller that
    supplies runs for the whole window, such as an offline fixture, passes None.
    """
    if runs_from is not None and runs_from > start:
        return _own_ci_unavailable(
            f"published-wheel runs were read from {runs_from} only, and the window "
            f"starts {start}"
        )
    publish = {day for day in publish_dates if start <= day <= end}
    rows_by_date: dict[str, int] = {}
    for row in interpreter_rows:
        day = str(row["date"])
        if start <= day <= end:
            rows_by_date[day] = rows_by_date.get(day, 0) + int(row["downloads"])
    counted: list[dict[str, Any]] = []
    jobs_by_date: dict[str, int] = {}
    for run in runs:
        day = str(run["date"])
        if not start <= day <= end or day in publish:
            continue
        jobs = int(run["wheel_install_jobs"])
        counted.append({"run_id": int(run["run_id"]), "date": day, "wheel_install_jobs": jobs})
        jobs_by_date[day] = jobs_by_date.get(day, 0) + jobs
    subtracted = sum(min(jobs, rows_by_date.get(day, 0)) for day, jobs in jobs_by_date.items())
    unsubtracted = sum(
        max(0, jobs - rows_by_date.get(day, 0)) for day, jobs in jobs_by_date.items()
    )
    day_count = int(raw["day_count"])
    downloads = int(raw["downloads"]) - subtracted
    block: dict[str, Any] = {
        "status": "ok",
        "downloads": downloads,
        "day_count": day_count,
        "mean_per_day": round(downloads / day_count, 1) if day_count else 0.0,
        "jobs_excluded": subtracted,
        "jobs_not_subtracted": unsubtracted,
        "runs_excluded": sorted(counted, key=lambda run: (run["date"], run["run_id"])),
        "source": PUBLISHED_WHEEL_RUNS_URL,
    }
    if unsubtracted:
        # pypistats and the Actions API are different systems, so a day can show
        # fewer real-interpreter rows than we ran jobs. Say so; do not borrow the
        # difference from another day.
        block["note"] = (
            f"{unsubtracted} of our own wheel-install jobs had no real-interpreter row "
            "on their own day and were not subtracted; each day's subtraction is "
            "capped at that day's rows"
        )
    return block


def _own_ci_unavailable(reason: str) -> dict[str, Any]:
    """Say the subtraction could not be made. Never present raw as net."""
    return {"status": "unavailable", "reason": reason, "source": PUBLISHED_WHEEL_RUNS_URL}


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
    own_ci_runs: list[dict[str, Any]] | None = None,
    own_ci_error: str | None = None,
    own_ci_runs_from: str | None = None,
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
            "published_wheel_ci": OWN_CI_EXCLUSION,
            "published_wheel_ci_runs": sorted(
                (
                    {
                        "run_id": int(run["run_id"]),
                        "date": str(run["date"]),
                        "wheel_install_jobs": int(run["wheel_install_jobs"]),
                    }
                    for run in (own_ci_runs or ())
                ),
                key=lambda run: (run["date"], run["run_id"]),
            ),
        },
        "dedup": {"pypi": "none; each download is a package event, not a unique user"},
    }
    own_ci_available = not own_ci_error and own_ci_runs is not None
    own_ci_reason = own_ci_error or "published-wheel runs not supplied"
    sources["github_published_wheel_runs"] = (
        {"status": "ok", "url": PUBLISHED_WHEEL_RUNS_URL, "retrieved_at": retrieved_at}
        if own_ci_available
        else {"status": "unavailable", "url": PUBLISHED_WHEEL_RUNS_URL, "reason": own_ci_reason}
    )
    if pypi_error or pypi_rows is None:
        sources["pypi"] = {"status": "unavailable", "url": PYPI_URL, "reason": pypi_error or "not supplied"}
        snapshot["data_lag"] = {"pypi": "unavailable"}
    else:
        snapshot["unknowns"].append(INTERPRETER_CAVEAT)
        rows = sorted(
            (
                {"date": row["date"], "downloads": int(row["downloads"])}
                for row in pypi_rows
                if row.get("category", "without_mirrors") == "without_mirrors"
            ),
            key=lambda row: row["date"],
        )
        end = date.fromisoformat(rows[-1]["date"]) if rows else retrieved
        start7, end7, total7, _missing7 = _window(rows, end, 7)
        start30, end30, total30, missing30 = _window(rows, end, 30)
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
        off_publish: dict[str, Any] = {
            "method": OFF_PUBLISH_METHOD,
            "caveat": INTERPRETER_CAVEAT,
            "own_ci_method": OWN_CI_METHOD,
            "own_ci_upper_bound": OWN_CI_UPPER_BOUND,
        }
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
                real["net_of_own_ci"] = (
                    _net_of_own_ci(
                        real,
                        interpreter_rows,
                        own_ci_runs or [],
                        w_start,
                        w_end,
                        release_dates,
                        own_ci_runs_from,
                    )
                    if own_ci_available
                    else _own_ci_unavailable(own_ci_reason)
                )
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
            # A window can fail the subtraction on its own, so each one says so by
            # name. The upper-bound caveat belongs only to the windows that netted.
            netted = []
            not_netted = []
            for label in ("window_7d", "window_30d"):
                net = (off_publish.get(label) or {}).get("real_interpreter", {})
                net = net.get("net_of_own_ci") if isinstance(net, dict) else None
                if not isinstance(net, dict):
                    continue
                if net.get("status") == "ok":
                    netted.append(label)
                    continue
                not_netted.append(label)
                snapshot["unknowns"].append(
                    f"our own published-wheel CI could not be subtracted from the "
                    f"{label} figure: {net.get('reason') or 'no reason given'}"
                )
            if netted:
                snapshot["unknowns"].append(OWN_CI_UPPER_BOUND)
            if not_netted:
                sources["github_published_wheel_runs"]["windows_not_subtracted"] = not_netted
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


class _DropAuthOnHostChange(HTTPRedirectHandler):
    """Strip Authorization when a redirect leaves the host and scheme we sent it to.

    urllib copies every header onto a redirected request, so without this a
    redirect off api.github.com would carry our token to the new host, and an
    https -> http redirect would carry it in cleartext to the same host.
    """

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None:
            return None
        if redirected.host != req.host or redirected.type != req.type:
            redirected.remove_header("Authorization")
        return redirected


_OPENER = build_opener(_DropAuthOnHostChange())


def _get_json(url: str) -> dict[str, Any]:
    headers = {"User-Agent": "agentguard-activation-refresh"}
    if url.startswith(f"{GITHUB_API_ROOT}/"):
        # Only the GitHub host ever sees a token, on this request and on any
        # redirect it follows. Unauthenticated api.github.com allows 60 requests
        # an hour, which one refresh can exhaust.
        headers["Accept"] = "application/vnd.github+json"
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with _OPENER.open(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected object from {url}")
    return payload


def _wheel_install_jobs(payload: dict[str, Any]) -> int:
    """Count the jobs of one run that completed the wheel-install step."""
    jobs = payload.get("jobs")
    if not isinstance(jobs, list):
        raise ValueError("missing Actions job inventory")
    count = 0
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError("invalid Actions job")
        if job.get("status") != "completed":
            # A queued or running job has installed nothing yet.
            continue
        steps = job.get("steps")
        if not isinstance(steps, list):
            raise ValueError(f"Actions job {job.get('id')} is missing its step list")
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError("invalid Actions job step")
            if (
                str(step.get("name") or "").strip() == WHEEL_INSTALL_STEP
                and step.get("conclusion") == "success"
            ):
                count += 1
                break
    return count


def own_ci_runs_from(retrieved_at: str, lookback_days: int = OWN_CI_LOOKBACK_DAYS) -> str:
    """The earliest day a run inventory read at this time covers."""
    retrieved = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00")).date()
    return (retrieved - timedelta(days=lookback_days)).isoformat()


def published_wheel_runs(
    retrieved_at: str, lookback_days: int = OWN_CI_LOOKBACK_DAYS
) -> tuple[list[dict[str, Any]], str]:
    """Read our own published-wheel runs and their wheel-install job counts.

    Returns the runs and the first day the inventory actually covers. Bounded to
    the widest reporting window plus lag, because one job request per run is one
    GitHub API request. Only one page is read, so if that page fills up before it
    reaches the lookback, coverage starts at the oldest run on it, not at the
    lookback. The caller must not claim more coverage than that.
    """
    earliest = own_ci_runs_from(retrieved_at, lookback_days)
    payload = _get_json(PUBLISHED_WHEEL_RUNS_URL)
    runs = payload.get("workflow_runs")
    if not isinstance(runs, list):
        raise ValueError("missing Actions workflow run inventory")
    collected: list[dict[str, Any]] = []
    oldest_seen: str | None = None
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("invalid Actions workflow run")
        run_id = run.get("id")
        created = run.get("created_at")
        if not isinstance(run_id, int) or not isinstance(created, str):
            raise ValueError("Actions run is missing an id or a created_at")
        started = datetime.fromisoformat(created.replace("Z", "+00:00"))
        if started.tzinfo is None:
            raise ValueError("Actions run timestamp needs a timezone")
        day = started.astimezone(timezone.utc).date().isoformat()
        if oldest_seen is None or day < oldest_seen:
            oldest_seen = day
        if day < earliest:
            continue
        collected.append(
            {
                "run_id": run_id,
                "date": day,
                "wheel_install_jobs": _wheel_install_jobs(
                    _get_json(f"{GITHUB_API_ROOT}/actions/runs/{run_id}/jobs?per_page=100")
                ),
            }
        )
    covers_from = earliest
    if len(runs) >= RUNS_PAGE_SIZE and oldest_seen is not None and oldest_seen > earliest:
        # The page ran out before the lookback did, so older runs may exist that
        # we never saw. Report what the data covers, not what we asked for.
        covers_from = oldest_seen
    return sorted(collected, key=lambda run: (run["date"], run["run_id"])), covers_from


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
    own_ci = None
    own_ci_from = None
    own_ci_error = None
    try:
        own_ci, own_ci_from = published_wheel_runs(retrieved_at)
    except Exception as exc:
        own_ci_error = f"{type(exc).__name__}: {exc}"
    retrieved = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00")).date()
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
        own_ci_runs=own_ci,
        own_ci_error=own_ci_error,
        own_ci_runs_from=own_ci_from,
    )
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
        help="Offline published-wheel runs: run_id, date, wheel_install_jobs",
    )
    parser.add_argument(
        "--published-wheel-runs-from",
        help=(
            "First day the offline run file covers, YYYY-MM-DD. A window that "
            "starts earlier reports its net figure as unavailable."
        ),
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
            own_ci_runs=(
                json.loads(args.published_wheel_runs_json.read_text(encoding="utf-8"))
                if args.published_wheel_runs_json
                else None
            ),
            own_ci_runs_from=args.published_wheel_runs_from,
            release_dates=(
                _publish_dates(json.loads(args.pypi_releases_json.read_text(encoding="utf-8")))
                if args.pypi_releases_json else RELEASE_DATES
            ),
        )
    args.out.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
