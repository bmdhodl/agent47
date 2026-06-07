"""Tests for scripts/sdk_pulse.py.

The pulse script lives outside the agentguard package, so it is loaded by path
(same pattern as test_ci_tools_requirements_guard.py). All tests are offline:
they exercise the pure parsing/aggregation/render logic and stub the network
collectors, so nothing here makes an HTTP or gh call.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "sdk_pulse.py"
SPEC = importlib.util.spec_from_file_location("sdk_pulse", SCRIPT_PATH)
assert SPEC is not None
pulse = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = pulse
SPEC.loader.exec_module(pulse)


# --- _merge_json_values (the custom paginated-JSON decoder) ----------------

def test_merge_concatenated_arrays_flattens() -> None:
    # gh api --paginate emits per-page arrays back to back
    assert pulse._merge_json_values('[{"a":1},{"a":2}]\n[{"a":3}]') == [
        {"a": 1},
        {"a": 2},
        {"a": 3},
    ]


def test_merge_single_array_and_empty() -> None:
    assert pulse._merge_json_values('[{"x":9}]') == [{"x": 9}]
    assert pulse._merge_json_values("") == []


def test_merge_raises_on_error_object() -> None:
    # A GitHub error object returned with exit 0 must fail loud, not filter to []
    try:
        pulse._merge_json_values('{"message":"Not Found"}')
    except ValueError:
        return
    raise AssertionError("expected ValueError on non-array page")


# --- _sum_by_category (None coercion keeps the snapshot serializable) -------

def test_sum_by_category_coerces_none_to_null_string() -> None:
    counter = pulse._sum_by_category(
        [{"category": None, "downloads": 5}, {"category": "Linux", "downloads": 95}]
    )
    assert dict(counter) == {"null": 5, "Linux": 95}
    # The whole point: this must be JSON-serializable with sorted keys.
    json.dumps(dict(counter), sort_keys=True)


# --- _safe (per-source isolation) ------------------------------------------

def test_safe_isolates_shape_errors() -> None:
    value, error = pulse._safe(lambda: {}["missing"])
    assert value is None
    assert error is not None and "KeyError" in error


def test_safe_passes_through_success() -> None:
    value, error = pulse._safe(lambda: 42)
    assert value == 42 and error is None


# --- collect_pypi_overall (mirror dedup, three cases) ----------------------

def _stub_overall(monkeypatch, rows: list[dict]) -> None:
    monkeypatch.setattr(pulse, "_get_json", lambda url: {"data": rows})


def test_overall_uses_only_without_mirrors(monkeypatch) -> None:
    _stub_overall(
        monkeypatch,
        [
            {"category": "with_mirrors", "date": "2026-06-01", "downloads": 100},
            {"category": "without_mirrors", "date": "2026-06-01", "downloads": 40},
        ],
    )
    assert pulse.collect_pypi_overall()["total_recorded"] == 40


def test_overall_with_mirrors_only_is_unknown(monkeypatch) -> None:
    _stub_overall(
        monkeypatch,
        [{"category": "with_mirrors", "date": "2026-06-01", "downloads": 999}],
    )
    result = pulse.collect_pypi_overall()
    assert result["total_recorded"] is None and result["range"] is None


def test_overall_no_split_sums_all(monkeypatch) -> None:
    _stub_overall(
        monkeypatch,
        [
            {"date": "2026-06-01", "downloads": 12},
            {"date": "2026-06-02", "downloads": 8},
        ],
    )
    result = pulse.collect_pypi_overall()
    assert result["total_recorded"] == 20
    assert result["range"] == ["2026-06-01", "2026-06-02"]


# --- collect_external_issues (bot / PR / deleted-account filtering) --------

def test_next_link_extracts_github_pagination_url() -> None:
    link = (
        '<https://api.github.com/repositories/1/issues?page=2>; rel="next", '
        '<https://api.github.com/repositories/1/issues?page=4>; rel="last"'
    )
    assert pulse._next_link(link) == "https://api.github.com/repositories/1/issues?page=2"


def test_external_issues_filters_owner_bots_prs_and_null_users(monkeypatch) -> None:
    issues = [
        {"user": {"login": "alice", "type": "User"}},
        {"user": None},  # deleted/suspended account
        {"user": {"login": pulse.REPO_OWNER, "type": "User"}},
        {"user": {"login": "dependabot[bot]", "type": "Bot"}},
        {"pull_request": {}, "user": {"login": "bob", "type": "User"}},
    ]
    monkeypatch.setattr(pulse, "_github_public_array", lambda path: issues)
    monkeypatch.setattr(
        pulse,
        "_gh_api",
        lambda path, paginate=False: (_ for _ in ()).throw(AssertionError("gh not used")),
    )
    result = pulse.collect_external_issues()
    assert result["external_open_issues"] == 1
    assert result["external_authors"] == ["alice"]


# --- render (signal classification + zero/None display) --------------------

def test_render_puts_forks_under_machine_not_human() -> None:
    snapshot = {
        "repo": "x",
        "github": {"stars": 3, "forks": 2},
        "pypi_recent": {"last_day": 1, "last_week": 2, "last_month": 3},
        "errors": {},
    }
    human, machine = pulse.render(snapshot).split("MACHINE VOLUME")
    assert "fork" not in human.lower()
    assert "fork" in machine.lower()
    assert "stars" in human.lower()


def test_render_distinguishes_zero_from_absent_uniques() -> None:
    absent = pulse.render({"repo": "x", "github_traffic": {"clones_14d": 50}, "errors": {}})
    zero = pulse.render(
        {"repo": "x", "github_traffic": {"clones_14d": 50, "clones_uniques_14d": 0}, "errors": {}}
    )
    assert "n/a unique" in absent
    assert "0 unique" in zero


# --- main (history hygiene) ------------------------------------------------

def test_main_does_not_write_empty_history_on_total_failure(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(
        pulse,
        "collect_all",
        lambda: {"repo": pulse.REPO, "collected_at": "t", "errors": {"x": "fail"}},
    )
    history = tmp_path / "history.jsonl"
    exit_code = pulse.main(["--append-history", str(history)])
    assert exit_code == 1
    assert not history.exists()
