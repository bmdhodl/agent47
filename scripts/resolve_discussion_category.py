#!/usr/bin/env python3
"""Resolve a GitHub Discussions category node_id from API JSON.

The GitHub REST endpoint can return an error object when Discussions are
disabled or unavailable. This helper accepts only the expected category list
shape so release announcement automation can skip safely instead of sending a
bad GraphQL mutation.
"""
from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Optional


def extract_category_node_id(payload: Any, category_name: str) -> Optional[str]:
    """Return a non-empty node_id for category_name, or None if unavailable."""
    if not isinstance(payload, list):
        return None

    for category in payload:
        if not isinstance(category, dict):
            continue
        if category.get("name") != category_name:
            continue
        node_id = category.get("node_id")
        if isinstance(node_id, str) and node_id.strip():
            return node_id
    return None


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", default="Announcements")
    args = parser.parse_args(argv)

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 1

    node_id = extract_category_node_id(payload, args.category)
    if not node_id:
        return 1

    print(node_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
