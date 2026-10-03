"""Fail closed unless every required CI job group actually passed."""
import json
import os
import sys

# Keep this inventory aligned with ci-required.needs in .github/workflows/ci.yml.
REQUIRED = frozenset({"test", "lint", "mcp", "mcp-budget", "compat", "responses-floor"})


def main():
    try:
        results = json.loads(os.environ.get("CI_NEEDS", ""))
    except json.JSONDecodeError:
        print("Missing or invalid CI evidence", file=sys.stderr)
        return 1
    if not isinstance(results, dict) or set(results) != REQUIRED:
        print("Required CI job groups are missing or unexpected", file=sys.stderr)
        return 1
    failed = [name for name, row in results.items()
              if not isinstance(row, dict) or row.get("result") != "success"]
    if failed:
        print("CI did not pass: " + ", ".join(sorted(failed)), file=sys.stderr)
        return 1
    print(f"All {len(REQUIRED)} CI job groups passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
