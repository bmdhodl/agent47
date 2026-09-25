#!/usr/bin/env python3
"""Classify a checked-in activation snapshot. Offline by default. No identity scrape."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlparse

INSTALL_HOSTS = {"pypi.org", "pypi.python.org"}
INSTALL_PATH_MARKERS = ("/project/agentguard47",)
INSTALL_COPY = "pip install agentguard47"
UNDIFFERENTIATED_FEEDBACK = (
    "consented_feedback total is not result=success; not counted as guard activation"
)


def is_install_intent_target(target: str) -> bool:
    text = (target or "").strip()
    if text.lower() == INSTALL_COPY:
        return True
    parsed = urlparse(text)
    host = (parsed.netloc or "").lower()
    path = parsed.path or ""
    if host in INSTALL_HOSTS and any(marker in path for marker in INSTALL_PATH_MARKERS):
        return True
    return False


def _reports(snapshot: Mapping[str, Any]) -> list[Mapping[str, Any]] | None:
    raw = snapshot.get("feedback_reports")
    if not isinstance(raw, list):
        return None
    return [item for item in raw if isinstance(item, Mapping)]


def classify_feedback_reports(
    reports: list[Mapping[str, Any]],
) -> tuple[int, int, dict[str, int], str]:
    """Count redacted reports once. Internal and simulated rows are not demand."""
    seen: set[str] = set()
    success = failure = 0
    excluded = {"duplicates": 0, "internal": 0, "simulated": 0}
    repeat = 0
    for item in reports:
        if item.get("simulated") is True:
            excluded["simulated"] += 1
            continue
        if item.get("internal") is True:
            excluded["internal"] += 1
            continue
        ident = str(item.get("id") or "")
        if ident and ident in seen:
            excluded["duplicates"] += 1
            continue
        if ident:
            seen.add(ident)
        result = str(item.get("result") or "")
        if result == "success":
            success += 1
        elif result == "failure":
            failure += 1
        dates = item.get("consent_link_dates")
        if (
            item.get("consent_to_link") is True
            and isinstance(dates, list)
            and len({str(day) for day in dates}) >= 2
        ):
            repeat += 1
    repeat_use = str(repeat) if repeat else "unknown without a consented reporter"
    return success, failure, excluded, repeat_use


def feedback_counts(snapshot: Mapping[str, Any]) -> tuple[int, int, bool]:
    """Return (success, failure, used_undifferentiated_total).

    Guard activation is result=success only. A bare integer
    ``consented_feedback`` total is not an activation count.
    """
    nested = snapshot.get("consented_feedback")
    if isinstance(nested, Mapping):
        return (
            int(nested.get("success") or 0),
            int(nested.get("failure") or 0),
            False,
        )
    if "consented_feedback_success" in snapshot or "consented_feedback_failure" in snapshot:
        return (
            int(snapshot.get("consented_feedback_success") or 0),
            int(snapshot.get("consented_feedback_failure") or 0),
            False,
        )
    total = int(nested or 0) if nested is not None else 0
    return 0, 0, total > 0


def _section(snapshot: Mapping[str, Any], key: str) -> Mapping[str, Any] | None:
    value = snapshot.get(key)
    return value if isinstance(value, Mapping) else None


def classify(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    site = _section(snapshot, "site")
    if site is None:
        proven_intent: int | str = "unknown"
        landing_intent: int | str = "unknown"
        page_navigation: dict[str, int | str] = {
            "view_events": "unknown",
            "cta_clicks": "unknown",
            "ai_crawl_events": "unknown",
            "bot_view_events": "unknown",
            "misclassified_landing_install_intent": "unknown",
        }
    else:
        intent_events = list(site.get("install_intent_events") or [])
        proven = 0
        landing = 0
        for event in intent_events:
            count = int(event.get("count") or 0)
            if is_install_intent_target(str(event.get("target") or "")):
                proven += count
            else:
                landing += count
        proven_intent = proven
        landing_intent = landing
        page_navigation = {
            "view_events": int(site.get("view_events") or 0),
            "cta_clicks": int(site.get("cta_clicks") or 0),
            "ai_crawl_events": int(site.get("ai_crawl_events") or 0),
            "bot_view_events": int(site.get("bot_view_events") or 0),
            "misclassified_landing_install_intent": landing_intent,
        }

    pypi = _section(snapshot, "pypi")
    sources = _section(snapshot, "sources") or {}
    pypi_source = sources.get("pypi") if isinstance(sources.get("pypi"), Mapping) else {}
    if pypi is None or pypi_source.get("status") == "unavailable":
        downloads_7d: int | str = "unknown"
        downloads_30d: int | str = "unknown"
        outside_burst: int | str = "unknown"
    else:
        downloads_7d = int(pypi.get("without_mirrors_7d") or 0)
        downloads_30d = int(pypi.get("without_mirrors_30d") or 0)
        if pypi.get("burst_downloads_in_7d") is None:
            outside_burst = "not computed; release days are annotated, not removed"
        else:
            outside_burst = max(downloads_7d - int(pypi.get("burst_downloads_in_7d") or 0), 0)

    github = _section(snapshot, "github")
    traffic = sources.get("github_traffic") if isinstance(sources.get("github_traffic"), Mapping) else {}
    if traffic.get("status") == "unavailable" or github is None or "views" not in github:
        repository_visits: int | str = "unknown"
    else:
        repository_visits = int(github.get("views") or 0)

    reports = _reports(snapshot)
    excluded = {"duplicates": 0, "internal": 0, "simulated": 0}
    if reports is not None:
        success_feedback, failure_feedback, excluded, repeat_use = classify_feedback_reports(reports)
        undifferentiated = False
    elif any(
        key in snapshot
        for key in ("consented_feedback", "consented_feedback_success", "consented_feedback_failure")
    ):
        success_feedback, failure_feedback, undifferentiated = feedback_counts(snapshot)
        repeat_use = "unknown without a consented reporter"
    else:
        success_feedback, failure_feedback = "unknown", "unknown"
        undifferentiated = False
        repeat_use = "unknown without a consented reporter"

    unknowns = list(snapshot.get("unknowns") or [])
    if undifferentiated and UNDIFFERENTIATED_FEEDBACK not in unknowns:
        unknowns.append(UNDIFFERENTIATED_FEEDBACK)
    if excluded["simulated"] and "simulated reports are not demand" not in unknowns:
        unknowns.append("simulated reports are not demand")
    missing_days = list((pypi or {}).get("missing_days") or []) if pypi else []
    if missing_days:
        unknowns.append("pypi missing days: " + ", ".join(str(day) for day in missing_days))

    report = {
        "as_of": snapshot.get("as_of"),
        "retrieved_at": snapshot.get("retrieved_at"),
        "data_lag": snapshot.get("data_lag"),
        "windows": snapshot.get("windows"),
        "dedup": snapshot.get("dedup"),
        "unknowns": unknowns,
        "exclusions": snapshot.get("exclusions"),
        "page_navigation": page_navigation,
        "downloads": {
            "pypi_without_mirrors_7d": downloads_7d,
            "pypi_without_mirrors_30d": downloads_30d if pypi is not None else "unknown",
            "release_day_events": list((pypi or {}).get("release_day_events") or []) if pypi else [],
            "note": "package events, not unique users; release-day rows are annotated and not removed as CI",
        },
        "repository_visits": repository_visits,
        "install": {
            "pypi_without_mirrors_7d": downloads_7d,
            "pypi_events_outside_publish_burst": outside_burst,
            "note": "package events, not unique users",
        },
        "install_intent_proven": proven_intent,
        "demo_feedback_success": success_feedback,
        "guard_activation": success_feedback,
        "real_workflow_activation": "unknown",
        "consented_feedback_failure": failure_feedback,
        "feedback_excluded": excluded,
        "repeat_use": repeat_use,
        "accepted_contribution": (
            int(snapshot["accepted_external_contributions"])
            if "accepted_external_contributions" in snapshot
            else "unknown"
        ),
        # Policy, not a snapshot quality bit: landing targets never increment
        # install_intent_proven. Proven PyPI/copy events live in that field.
        "landing_page_never_counts_as_install": True,
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Classify an activation snapshot. Does not fetch the network."
    )
    parser.add_argument("snapshot", type=Path, help="JSON snapshot path")
    args = parser.parse_args(argv)
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    json.dump(classify(snapshot), sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
