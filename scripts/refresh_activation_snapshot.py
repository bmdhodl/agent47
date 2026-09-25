#!/usr/bin/env python3
"""Build an activation snapshot from public counts or local fixtures.

Offline unless --fetch-public is set. That flag reads PyPI Stats and the npm
downloads API only. It does not read identities, subscribers, or site events.
"""
from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

PYPI_URL = "https://pypistats.org/api/packages/agentguard47/overall?mirrors=false"
NPM_PACKAGE = "@agentguard47/mcp-server"
RELEASE_DATES = ("2026-09-12", "2026-09-15", "2026-09-18", "2026-09-24")


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


def build_snapshot(
    *,
    retrieved_at: str,
    pypi_rows: list[dict[str, Any]] | None,
    npm: dict[str, Any] | None,
    feedback_reports: list[dict[str, Any]] | None,
    pypi_error: str | None = None,
    npm_error: str | None = None,
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
            "publish_dates": list(RELEASE_DATES),
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
                for day in RELEASE_DATES
                if start30 <= day <= end30
            ],
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
    pypi_error = npm_error = None
    pypi_rows = npm = None
    try:
        pypi_rows = list(_get_json(PYPI_URL).get("data") or [])
    except Exception as exc:
        pypi_error = type(exc).__name__
    retrieved = datetime.fromisoformat(retrieved_at.replace("Z", "+00:00")).date()
    start = (retrieved - timedelta(days=29)).isoformat()
    end = retrieved.isoformat()
    npm_url = f"https://api.npmjs.org/downloads/point/{start}:{end}/{NPM_PACKAGE}"
    try:
        npm = _get_json(npm_url)
    except Exception as exc:
        npm_error = type(exc).__name__
    return build_snapshot(
        retrieved_at=retrieved_at,
        pypi_rows=pypi_rows,
        npm=npm,
        feedback_reports=[],
        pypi_error=pypi_error,
        npm_error=npm_error,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Refresh an activation snapshot.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--fetch-public", action="store_true")
    parser.add_argument("--pypi-json", type=Path)
    parser.add_argument("--npm-json", type=Path)
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
        snapshot = build_snapshot(
            retrieved_at=args.retrieved_at,
            pypi_rows=pypi_rows,
            npm=npm,
            feedback_reports=feedback,
        )
    args.out.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
