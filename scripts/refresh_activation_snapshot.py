#!/usr/bin/env python3
"""Build an activation snapshot from public counts or local fixtures.

Offline unless --fetch-public is set. That flag reads PyPI release metadata,
PyPI Stats and the npm downloads API. It does not read identities or site events.
"""
from __future__ import annotations

import argparse
import json
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
    "whose category is not null."
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
    request = Request(url, headers={"User-Agent": "agentguard-activation-refresh"})
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
        )
    args.out.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
