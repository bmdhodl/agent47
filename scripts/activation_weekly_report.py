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


def classify(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    site = snapshot.get("site") or {}
    intent_events = list(site.get("install_intent_events") or [])
    proven_intent = 0
    landing_intent = 0
    for event in intent_events:
        count = int(event.get("count") or 0)
        if is_install_intent_target(str(event.get("target") or "")):
            proven_intent += count
        else:
            landing_intent += count

    pypi = snapshot.get("pypi") or {}
    downloads_7d = int(pypi.get("without_mirrors_7d") or 0)
    burst = int(pypi.get("burst_downloads_in_7d") or 0)
    labeled_install_events = downloads_7d
    outside_burst = max(downloads_7d - burst, 0)

    page_navigation = {
        "view_events": int(site.get("view_events") or 0),
        "cta_clicks": int(site.get("cta_clicks") or 0),
        "ai_crawl_events": int(site.get("ai_crawl_events") or 0),
        "bot_view_events": int(site.get("bot_view_events") or 0),
        "misclassified_landing_install_intent": landing_intent,
    }

    report = {
        "as_of": snapshot.get("as_of"),
        "windows": snapshot.get("windows"),
        "dedup": snapshot.get("dedup"),
        "unknowns": snapshot.get("unknowns"),
        "exclusions": snapshot.get("exclusions"),
        "page_navigation": page_navigation,
        "install": {
            "pypi_without_mirrors_7d": labeled_install_events,
            "pypi_events_outside_publish_burst": outside_burst,
            "note": "package events, not unique users",
        },
        "install_intent_proven": proven_intent,
        "guard_activation": int(snapshot.get("consented_feedback") or 0),
        "repeat_use": "unknown without a consented reporter",
        "accepted_contribution": int(snapshot.get("accepted_external_contributions") or 0),
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
