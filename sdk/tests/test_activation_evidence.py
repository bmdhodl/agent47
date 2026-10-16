"""AG-02: activation evidence and voluntary demo feedback."""
from __future__ import annotations

import importlib.util
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from agentguard.demo import run_offline_demo
from agentguard.feedback import (
    ALLOWED_FIELDS,
    ISSUE_TEMPLATE_URL,
    NOTHING_SENT,
    build_demo_feedback,
    validate_redacted,
)

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "docs" / "guides" / "activation-baseline-2026-09-18.json"
REPORT_SCRIPT = ROOT / "scripts" / "activation_weekly_report.py"
TEMPLATE = ROOT / ".github" / "ISSUE_TEMPLATE" / "activation_feedback.yml"


def test_feedback_payload_only_allows_four_fields():
    report = build_demo_feedback(
        version="1.3.2",
        adapter="offline-demo",
        result="success",
        reproduction="agentguard demo",
    )
    assert tuple(report) == ALLOWED_FIELDS
    validate_redacted(report)
    with pytest.raises(ValueError):
        validate_redacted({**report, "trace": "secret"})
    omitted = build_demo_feedback(
        version="1.3.2",
        adapter="offline-demo",
        result="success",
        reproduction="agentguard demo",
        omit=("reproduction",),
    )
    assert "reproduction" not in omitted
    assert "version" in omitted


def test_demo_redaction_failure_is_readable(monkeypatch):
    import agentguard.demo as demo_mod

    monkeypatch.setattr(
        demo_mod,
        "build_demo_feedback",
        lambda **_kwargs: {"trace": "secret"},
    )
    with tempfile.TemporaryDirectory() as tmpdir, pytest.raises(
        RuntimeError, match="not redacted"
    ):
        demo_mod.run_offline_demo(
            trace_path=os.path.join(tmpdir, "demo.jsonl"),
            stream=io.StringIO(),
            feedback=True,
        )


def test_demo_feedback_is_local_and_declineable():
    with tempfile.TemporaryDirectory() as tmpdir:
        trace_path = os.path.join(tmpdir, "demo.jsonl")
        default_out = io.StringIO()
        feedback_out = io.StringIO()
        assert run_offline_demo(trace_path=trace_path, stream=default_out) == 0
        default_text = default_out.getvalue()
        assert "agentguard demo --feedback" in default_text
        assert "Decline by skipping" in default_text
        assert "Share template" not in default_text

        assert (
            run_offline_demo(
                trace_path=trace_path,
                stream=feedback_out,
                feedback=True,
            )
            == 0
        )
        text = feedback_out.getvalue()
        assert text.count(NOTHING_SENT) == 2
        assert ISSUE_TEMPLATE_URL in text
        assert "**version:**" in text
        assert "**adapter:** offline-demo" in text
        assert "**result:** success" in text
        assert "**reproduction:** agentguard demo" in text
        feedback_src = (ROOT / "sdk" / "agentguard" / "feedback.py").read_text(
            encoding="utf-8"
        )
        demo_src = (ROOT / "sdk" / "agentguard" / "demo.py").read_text(encoding="utf-8")
        assert "import urllib" not in feedback_src
        assert "import http.client" not in feedback_src
        assert "import urllib" not in demo_src


def test_demo_feedback_makes_no_network_call(monkeypatch):
    def _blocked(*_args, **_kwargs):
        raise AssertionError("demo feedback must not open a socket")

    monkeypatch.setattr(socket.socket, "connect", _blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked)
    with tempfile.TemporaryDirectory() as tmpdir:
        buf = io.StringIO()
        assert (
            run_offline_demo(
                trace_path=os.path.join(tmpdir, "demo.jsonl"),
                stream=buf,
                feedback=True,
            )
            == 0
        )
        assert NOTHING_SENT in buf.getvalue()


def test_weekly_report_does_not_count_landing_page_as_install():
    raw = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert "publish_dates" in raw["exclusions"]
    assert "publish_dates" not in raw
    assert "windows" in raw
    assert "never counts as install" in raw["exclusions"]["landing_page_install_intent"]
    proc = subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), str(BASELINE)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(proc.stdout)
    assert report["install_intent_proven"] == 0
    assert report["page_navigation"]["misclassified_landing_install_intent"] == 2
    assert report["guard_activation"] == 0
    assert report["consented_feedback_failure"] == 0
    assert report["repeat_use"].startswith("unknown")
    assert report["landing_page_never_counts_as_install"] is True
    assert "pypi_7d" in report["windows"]


def test_weekly_report_policy_stays_true_when_pypi_intent_exists(tmp_path):
    raw = json.loads(BASELINE.read_text(encoding="utf-8"))
    raw["site"]["install_intent_events"] = [
        {"target": "https://agentguard47.com/", "count": 2},
        {"target": "https://pypi.org/project/agentguard47/", "count": 3},
        {"target": "pip install agentguard47", "count": 1},
    ]
    snapshot = tmp_path / "mixed.json"
    snapshot.write_text(json.dumps(raw), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), str(snapshot)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(proc.stdout)
    assert report["install_intent_proven"] == 4
    assert report["page_navigation"]["misclassified_landing_install_intent"] == 2
    assert report["landing_page_never_counts_as_install"] is True


def test_weekly_report_counts_only_successful_feedback(tmp_path):
    raw = json.loads(BASELINE.read_text(encoding="utf-8"))
    raw["consented_feedback_success"] = 2
    raw["consented_feedback_failure"] = 3
    snapshot = tmp_path / "feedback-split.json"
    snapshot.write_text(json.dumps(raw), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), str(snapshot)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(proc.stdout)
    assert report["guard_activation"] == 2
    assert report["consented_feedback_failure"] == 3


def test_weekly_report_does_not_treat_undifferentiated_feedback_as_activation(tmp_path):
    raw = json.loads(BASELINE.read_text(encoding="utf-8"))
    raw.pop("consented_feedback_success", None)
    raw.pop("consented_feedback_failure", None)
    raw["consented_feedback"] = 4
    snapshot = tmp_path / "feedback-total.json"
    snapshot.write_text(json.dumps(raw), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), str(snapshot)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    report = json.loads(proc.stdout)
    assert report["guard_activation"] == 0
    assert report["consented_feedback_failure"] == 0
    assert any("not result=success" in item for item in report["unknowns"])


def test_issue_template_captures_allowed_fields_only():
    text = TEMPLATE.read_text(encoding="utf-8")
    for field in ("version", "adapter", "result", "reproduction"):
        assert f"id: {field}" in text
    assert "I inspected this report locally" in text
    assert "Do not attach traces" in text


def test_omit_requires_at_least_one_field(monkeypatch):
    import agentguard.cli as cli

    monkeypatch.setattr(sys, "argv", ["agentguard", "demo", "--omit"])
    with pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2


def test_docs_and_site_reject_page_view_as_install():
    design = (ROOT / "docs" / "guides" / "activation-metrics-design.md").read_text(
        encoding="utf-8"
    )
    contract = (ROOT / "docs" / "guides" / "bmdpat-measurement-contract.md").read_text(
        encoding="utf-8"
    )
    activation = (ROOT / "site" / "activation.html").read_text(encoding="utf-8")
    index = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    assert "never counts as install" in design
    assert "install_intent" in contract
    assert "This page view is not an install" in activation
    assert "activation.html" in index
    assert 'data-ag-metric="page-navigation"' in index
    assert 'data-ag-metric="install-intent-candidate"' in index
    for name in ("index.html", "quickstart.html", "compare.html", "enforcement.html"):
        page = (ROOT / "site" / name).read_text(encoding="utf-8")
        assert "activation.html" in page, name


def test_activation_page_states_bounds():
    html = (ROOT / "site" / "activation.html").read_text(encoding="utf-8")
    for needle in (
        "Page navigation",
        "Guard activation",
        "Repeat use",
        "Nothing is sent",
        "max-width: 860px",
    ):
        assert needle in html, needle


def _classify(tmp_path, payload):
    path = tmp_path / "snapshot.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def test_weekly_report_empty_input_stays_unknown(tmp_path):
    report = _classify(tmp_path, {})
    assert report["downloads"]["pypi_without_mirrors_7d"] == "unknown"
    assert report["repository_visits"] == "unknown"
    assert report["install_intent_proven"] == "unknown"
    assert report["demo_feedback_success"] == "unknown"
    assert report["real_workflow_activation"] == "unknown"
    assert report["repeat_use"].startswith("unknown")
    assert report["guard_activation"] == "unknown"


def test_weekly_report_unavailable_pypi_is_not_zero(tmp_path):
    report = _classify(tmp_path, {"sources": {"pypi": {"status": "unavailable"}}, "pypi": {}})
    assert report["downloads"]["pypi_without_mirrors_7d"] == "unknown"
    assert report["install"]["pypi_without_mirrors_7d"] == "unknown"


def test_weekly_report_records_missing_days(tmp_path):
    raw = json.loads(BASELINE.read_text(encoding="utf-8"))
    raw["pypi"]["missing_days"] = ["2026-09-25"]
    report = _classify(tmp_path, raw)
    assert any("2026-09-25" in item for item in report["unknowns"])


def test_weekly_report_excludes_internal_duplicate_and_simulated(tmp_path):
    report = _classify(
        tmp_path,
        {
            "feedback_reports": [
                {"id": "a", "result": "success"},
                {"id": "a", "result": "success"},
                {"id": "internal-1", "result": "success", "internal": True},
                {"id": "sim", "result": "success", "simulated": True},
            ]
        },
    )
    assert report["demo_feedback_success"] == 1
    assert report["guard_activation"] == 1
    assert report["real_workflow_activation"] == "unknown"
    assert report["feedback_excluded"]["duplicates"] == 1
    assert report["feedback_excluded"]["internal"] == 1
    assert report["feedback_excluded"]["simulated"] == 1
    assert "simulated reports are not demand" in report["unknowns"]


def test_refresh_from_fixtures_does_not_invent_users(tmp_path):
    pypi = tmp_path / "pypi.json"
    npm = tmp_path / "npm.json"
    out = tmp_path / "snapshot.json"
    pypi.write_text(
        json.dumps(
            [
                {"category": "without_mirrors", "date": "2026-09-24", "downloads": 86},
                {"category": "without_mirrors", "date": "2026-09-23", "downloads": 2},
            ]
        ),
        encoding="utf-8",
    )
    npm.write_text(json.dumps({"downloads": 3, "start": "2026-08-26", "end": "2026-09-24"}), encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "refresh_activation_snapshot.py"),
            "--pypi-json",
            str(pypi),
            "--npm-json",
            str(npm),
            "--retrieved-at",
            "2026-09-25T00:00:00Z",
            "--out",
            str(out),
        ],
        check=True,
        cwd=ROOT,
    )
    snapshot = json.loads(out.read_text(encoding="utf-8"))
    assert snapshot["sources"]["github_traffic"]["status"] == "unavailable"
    assert snapshot["sources"]["site_events"]["status"] == "unavailable"
    assert "site" not in snapshot
    assert snapshot["pypi"]["without_mirrors_7d"] == 88
    report = _classify(tmp_path, snapshot)
    assert report["real_workflow_activation"] == "unknown"
    assert report["repeat_use"].startswith("unknown")


def _off_publish_fixture(tmp_path, extra_args=()):
    """The 2026-09-20..2026-09-26 window from the AG-29 focus review.

    It holds one publish day (09-24) and two 100%-null interpreter days
    (09-20, 09-21), which is why figure two matters more than figure one.
    """
    overall = [
        {"category": "without_mirrors", "date": "2026-09-20", "downloads": 51},
        {"category": "without_mirrors", "date": "2026-09-21", "downloads": 18},
        {"category": "without_mirrors", "date": "2026-09-22", "downloads": 5},
        {"category": "without_mirrors", "date": "2026-09-23", "downloads": 10},
        {"category": "without_mirrors", "date": "2026-09-24", "downloads": 86},
        {"category": "without_mirrors", "date": "2026-09-25", "downloads": 12},
        {"category": "without_mirrors", "date": "2026-09-26", "downloads": 8},
    ]
    python_minor = [
        {"category": "null", "date": "2026-09-20", "downloads": 51},
        {"category": "null", "date": "2026-09-21", "downloads": 18},
        {"category": "3.12", "date": "2026-09-22", "downloads": 3},
        {"category": "null", "date": "2026-09-22", "downloads": 2},
        {"category": "3.11", "date": "2026-09-23", "downloads": 4},
        {"category": "null", "date": "2026-09-23", "downloads": 6},
        {"category": "3.12", "date": "2026-09-24", "downloads": 16},
        {"category": "null", "date": "2026-09-24", "downloads": 70},
        {"category": "3.13", "date": "2026-09-25", "downloads": 3},
        {"category": "null", "date": "2026-09-25", "downloads": 9},
        {"category": "3.12", "date": "2026-09-26", "downloads": 2},
        {"category": "null", "date": "2026-09-26", "downloads": 6},
    ]
    pypi = tmp_path / "pypi.json"
    minor = tmp_path / "python_minor.json"
    out = tmp_path / "snapshot.json"
    pypi.write_text(json.dumps(overall), encoding="utf-8")
    minor.write_text(json.dumps(python_minor), encoding="utf-8")
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "refresh_activation_snapshot.py"),
            "--pypi-json",
            str(pypi),
            "--python-minor-json",
            str(minor),
            "--retrieved-at",
            "2026-09-27T00:00:00Z",
            "--out",
            str(out),
            *extra_args,
        ],
        check=True,
        cwd=ROOT,
        capture_output=True,
    )
    return json.loads(out.read_text(encoding="utf-8"))


def test_off_publish_downloads_are_numeric_in_the_snapshot(tmp_path):
    snapshot = _off_publish_fixture(tmp_path)
    week = snapshot["pypi"]["off_publish_days"]["window_7d"]
    assert week["window"] == {"start": "2026-09-20", "end": "2026-09-26"}
    assert week["window_downloads"] == 190
    # 190 total less the 86 on the 09-24 publish day, over the other six days.
    assert isinstance(week["downloads"], int)
    assert week["downloads"] == 104
    assert week["day_count"] == 6
    assert week["mean_per_day"] == 17.3
    assert week["publish_dates_excluded"] == ["2026-09-24"]

    real = week["real_interpreter"]
    # 28 of the 190 name an interpreter; 16 of those land on the publish day.
    assert isinstance(real["downloads"], int)
    assert real["window_downloads"] == 28
    assert real["downloads"] == 12
    assert real["day_count"] == 6
    assert real["mean_per_day"] == 2.0

    # Release-day rows stay in the data, annotated.
    assert {row["date"] for row in snapshot["pypi"]["release_day_events"]} >= {"2026-09-24"}
    assert all(row["annotated_not_removed"] for row in snapshot["pypi"]["release_day_events"])
    assert any("null interpreter" in note for note in snapshot["unknowns"])


def test_off_publish_downloads_are_numeric_in_the_classifier(tmp_path):
    snapshot = _off_publish_fixture(tmp_path)
    report = _classify(tmp_path, snapshot)
    install = report["install"]
    assert install["pypi_events_outside_publish_burst"] == 104
    assert install["pypi_events_outside_publish_burst_day_count"] == 6
    assert install["pypi_events_outside_publish_burst_mean_per_day"] == 17.3
    assert install["pypi_real_interpreter_events_outside_publish_burst"] == 12
    assert install["pypi_real_interpreter_events_outside_publish_burst_day_count"] == 6
    assert install["pypi_real_interpreter_events_outside_publish_burst_mean_per_day"] == 2.0
    assert install["publish_dates_excluded"] == ["2026-09-24"]
    for key, value in install.items():
        assert "not computed" not in str(value), key
    assert "publish_dates" in str(install["off_publish_method"])
    assert any("null interpreter" in note for note in report["unknowns"])


def test_off_publish_stays_unknown_without_the_interpreter_feed(tmp_path):
    """An older snapshot must not turn a missing figure into a silent zero."""
    report = _classify(tmp_path, {})
    assert report["install"]["pypi_events_outside_publish_burst"] == "unknown"
    assert "not computed" not in json.dumps(report["install"])


def _refresh_module():
    spec = importlib.util.spec_from_file_location(
        "refresh_activation_snapshot", ROOT / "scripts/refresh_activation_snapshot.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _mock_public_feeds(monkeypatch, module, releases):
    def get_json(url):
        if url == "https://pypi.org/pypi/agentguard47/json":
            if isinstance(releases, Exception):
                raise releases
            return releases
        if url == module.PYPI_URL:
            return {"data": [
                {"category": "without_mirrors", "date": "2026-09-30", "downloads": 6},
                {"category": "without_mirrors", "date": "2026-10-01", "downloads": 100},
            ]}
        if url == module.PYTHON_MINOR_URL:
            return {"data": [
                {"category": "3.12", "date": "2026-09-30", "downloads": 2},
                {"category": "3.12", "date": "2026-10-01", "downloads": 50},
            ]}
        return {"downloads": 0, "start": "2026-09-03", "end": "2026-10-02"}
    monkeypatch.setattr(module, "_get_json", get_json)


def test_release_metadata_excludes_a_future_publish_day(monkeypatch, tmp_path):
    module = _refresh_module()
    _mock_public_feeds(monkeypatch, module, {"releases": {
        "1.4.0": [{"upload_time_iso_8601": "2026-09-24T12:00:00Z"}],
        "1.4.1": [
            {"upload_time_iso_8601": "2026-10-01T23:30:00Z"},
            {"upload_time_iso_8601": "2026-10-02T00:01:00Z"},
        ],
        "1.4.2": [],
    }})
    snapshot = module.fetch_public("2026-10-02T08:00:00Z")
    week = snapshot["pypi"]["off_publish_days"]["window_7d"]
    assert snapshot["exclusions"]["publish_dates"] == ["2026-09-24", "2026-10-01"]
    assert week["downloads"] == 6
    assert week["day_count"] == 6
    assert week["real_interpreter"]["downloads"] == 2
    assert week["publish_dates_excluded"] == ["2026-10-01"]
    assert _classify(tmp_path, snapshot)["install"]["pypi_events_outside_publish_burst"] == 6


@pytest.mark.parametrize("metadata", [
    OSError("release endpoint unavailable"), {}, {"releases": {}},
    {"releases": {"1.4.1": [{}]}},
    {"releases": {"1.4.1": [{"upload_time_iso_8601": "invalid"}]}},
])
def test_release_metadata_unavailable_keeps_off_publish_unknown(monkeypatch, tmp_path, metadata):
    module = _refresh_module()
    _mock_public_feeds(monkeypatch, module, metadata)
    snapshot = module.fetch_public("2026-10-02T08:00:00Z")
    report = _classify(tmp_path, snapshot)
    assert snapshot["pypi"]["without_mirrors_7d"] == 106
    assert snapshot["sources"]["pypi_releases"]["status"] == "unavailable"
    assert snapshot["exclusions"]["publish_dates"] == []
    assert ": " in snapshot["sources"]["pypi_releases"]["reason"]
    assert report["install"]["pypi_events_outside_publish_burst"] == "unknown"


WHEEL_STEP = "Install the published wheel and run the offline example"
# Live pypistats rows for 2026-09-24..2026-10-03, read 2026-10-04 (AG-08 card).
# 09-24 is a publish day. 09-25 and 10-03 each carry a four-job
# published-wheel.yml run that installed the wheel with a real interpreter.
OWN_CI_OVERALL = {
    "2026-09-24": 86, "2026-09-25": 21, "2026-09-26": 10, "2026-09-27": 3,
    "2026-09-28": 8, "2026-09-29": 5, "2026-09-30": 7, "2026-10-01": 2,
    "2026-10-02": 1, "2026-10-03": 6,
}
OWN_CI_REAL = {
    "2026-09-24": 16, "2026-09-25": 8, "2026-09-26": 3, "2026-09-27": 0,
    "2026-09-28": 1, "2026-09-29": 2, "2026-09-30": 5, "2026-10-01": 2,
    "2026-10-02": 0, "2026-10-03": 5,
}


def _wheel_job(name, day, conclusion="success"):
    return {"name": name, "steps": [
        {"name": "Run actions/checkout", "conclusion": "success", "started_at": f"{day}T08:56:30Z"},
        {"name": WHEEL_STEP, "conclusion": conclusion, "started_at": f"{day}T08:57:00Z"},
    ]}


def _run_jobs(day):
    release = {"name": "release", "steps": [
        {"name": "Resolve one stable release for the whole matrix", "conclusion": "success",
         "started_at": f"{day}T08:56:25Z"},
    ]}
    matrix = ("windows-latest / Python 3.12", "ubuntu-latest / Python 3.9",
              "ubuntu-latest / Python 3.12", "macos-latest / Python 3.12")
    return [release] + [_wheel_job(name, day) for name in matrix]


OWN_CI_RUNS = [
    {"id": 37111363411, "event": "schedule", "status": "completed", "conclusion": "success",
     "created_at": "2026-10-03T08:56:23Z"},
    {"id": 36190628659, "event": "workflow_dispatch", "status": "completed", "conclusion": "success",
     "created_at": "2026-09-25T21:16:25Z"},
]
OWN_CI_JOBS = {37111363411: _run_jobs("2026-10-03"), 36190628659: _run_jobs("2026-09-25")}


def _mock_own_ci_feeds(monkeypatch, module, *, runs=OWN_CI_RUNS, jobs=OWN_CI_JOBS, github_error=None):
    def get_json(url):
        if url == module.PYPI_RELEASES_URL:
            return {"releases": {"1.4.0": [{"upload_time_iso_8601": "2026-09-24T12:00:00Z"}]}}
        if url == module.PYPI_URL:
            return {"data": [
                {"category": "without_mirrors", "date": day, "downloads": count}
                for day, count in OWN_CI_OVERALL.items()
            ]}
        if url == module.PYTHON_MINOR_URL:
            rows = [{"category": "null", "date": day, "downloads": OWN_CI_OVERALL[day] - count}
                    for day, count in OWN_CI_REAL.items()]
            rows += [{"category": "3.12", "date": day, "downloads": count}
                     for day, count in OWN_CI_REAL.items() if count]
            return {"data": rows}
        if url.startswith("https://api.github.com/"):
            if github_error is not None:
                raise github_error
            if "/actions/workflows/published-wheel.yml/runs?" in url:
                return {"total_count": len(runs), "workflow_runs": runs}
            for run_id, run_jobs in jobs.items():
                if f"/actions/runs/{run_id}/jobs?" in url:
                    return {"total_count": len(run_jobs), "jobs": run_jobs}
            raise AssertionError(f"unexpected GitHub URL {url}")
        return {"downloads": 0, "start": "2026-09-05", "end": "2026-10-04"}
    monkeypatch.setattr(module, "_get_json", get_json)


def test_net_of_own_ci_is_lower_than_raw_on_a_published_wheel_day(monkeypatch, tmp_path):
    module = _refresh_module()
    _mock_own_ci_feeds(monkeypatch, module)
    snapshot = module.fetch_public("2026-10-04T08:00:00Z")
    off = snapshot["pypi"]["off_publish_days"]

    week = off["window_7d"]["real_interpreter"]
    assert off["window_7d"]["window"] == {"start": "2026-09-27", "end": "2026-10-03"}
    net = week["net_of_own_ci"]
    assert isinstance(week["downloads"], int) and isinstance(net["downloads"], int)
    assert isinstance(week["mean_per_day"], float) and isinstance(net["mean_per_day"], float)
    # 15 raw real-interpreter rows; four of them are the 10-03 matrix installs.
    assert week["downloads"] == 15
    assert net["downloads"] == 11
    assert net["downloads"] < week["downloads"]
    assert net["mean_per_day"] < week["mean_per_day"]
    assert net["day_count"] == 7
    assert net["own_ci_wheel_install_jobs"] == 4
    assert net["own_ci_dates"] == ["2026-10-03"]
    assert "upper bound" in net["bound"]
    assert "does not identify a person" in net["bound"]

    month = off["window_30d"]["real_interpreter"]
    # 09-25 + 09-26 + the 15 above; 09-24 is a publish day and stays out.
    assert month["downloads"] == 26
    assert month["net_of_own_ci"]["downloads"] == 18
    assert month["net_of_own_ci"]["downloads"] < month["downloads"]
    assert month["net_of_own_ci"]["own_ci_dates"] == ["2026-09-25", "2026-10-03"]

    exclusions = snapshot["exclusions"]
    assert {"mirrors", "simulated_reports", "publish_dates"} <= set(exclusions)
    own_ci = exclusions["published_wheel_ci"]
    assert own_ci["workflow"] == ".github/workflows/published-wheel.yml"
    assert "published-wheel.yml" in own_ci["method"]
    assert own_ci["runs"] == [
        {"run_id": 36190628659, "date": "2026-09-25", "event": "workflow_dispatch",
         "wheel_install_jobs": 4},
        {"run_id": 37111363411, "date": "2026-10-03", "event": "schedule",
         "wheel_install_jobs": 4},
    ]
    assert snapshot["sources"]["github_actions"]["status"] == "ok"

    install = _classify(tmp_path, snapshot)["install"]
    assert install["pypi_real_interpreter_events_outside_publish_burst"] == 15
    assert install["pypi_real_interpreter_events_outside_publish_burst_net_of_own_ci"] == 11
    assert install["pypi_real_interpreter_events_outside_publish_burst_net_of_own_ci_mean_per_day"] == 1.6
    assert "upper bound" in install["pypi_real_interpreter_events_outside_publish_burst_net_of_own_ci_bound"]
    for key, value in install.items():
        assert "not computed" not in str(value), key


def test_net_of_own_ci_is_unavailable_when_the_actions_api_fails(monkeypatch, tmp_path):
    module = _refresh_module()
    _mock_own_ci_feeds(monkeypatch, module, github_error=OSError("actions api down"))
    snapshot = module.fetch_public("2026-10-04T08:00:00Z")
    for label in ("window_7d", "window_30d"):
        real = snapshot["pypi"]["off_publish_days"][label]["real_interpreter"]
        assert isinstance(real["downloads"], int)
        net = real["net_of_own_ci"]
        assert net["status"] == "unavailable"
        assert "OSError" in net["reason"]
        assert "downloads" not in net and "mean_per_day" not in net
    own_ci = snapshot["exclusions"]["published_wheel_ci"]
    assert own_ci["status"] == "unavailable"
    assert "runs" not in own_ci
    assert snapshot["sources"]["github_actions"]["status"] == "unavailable"
    install = _classify(tmp_path, snapshot)["install"]
    net_value = install["pypi_real_interpreter_events_outside_publish_burst_net_of_own_ci"]
    assert str(net_value).startswith("unavailable; ")
    assert net_value != install["pypi_real_interpreter_events_outside_publish_burst"]


def test_net_of_own_ci_stays_unknown_in_an_older_snapshot(tmp_path):
    older = json.loads(
        (ROOT / "docs" / "guides" / "activation-snapshot-2026-09-28.json").read_text(encoding="utf-8")
    )
    install = _classify(tmp_path, older)["install"]
    assert install["pypi_real_interpreter_events_outside_publish_burst"] == 12
    assert install["pypi_real_interpreter_events_outside_publish_burst_net_of_own_ci"] == "unknown"


def test_offline_refresh_reads_saved_run_records(tmp_path):
    runs = tmp_path / "runs.json"
    runs.write_text(json.dumps([
        {"run_id": 36190628659, "date": "2026-09-25", "event": "workflow_dispatch",
         "wheel_install_jobs": 2},
    ]), encoding="utf-8")
    snapshot = _off_publish_fixture(tmp_path, ("--published-wheel-runs-json", str(runs)))
    real = snapshot["pypi"]["off_publish_days"]["window_7d"]["real_interpreter"]
    assert real["downloads"] == 12
    assert real["net_of_own_ci"]["downloads"] == 10
    assert snapshot["exclusions"]["published_wheel_ci"]["runs"][0]["run_id"] == 36190628659

    without = _off_publish_fixture(tmp_path)
    net = without["pypi"]["off_publish_days"]["window_7d"]["real_interpreter"]["net_of_own_ci"]
    assert net == {
        "status": "unavailable",
        "reason": "published-wheel.yml runs not supplied",
        "source": _refresh_module().OWN_CI_RUNS_URL,
    }

    runs.write_text(json.dumps([{"run_id": "x", "date": "2026-09-25"}]), encoding="utf-8")
    with pytest.raises(subprocess.CalledProcessError):
        _off_publish_fixture(tmp_path, ("--published-wheel-runs-json", str(runs)))


def test_published_wheel_collector_pages_and_counts_only_finished_installs(monkeypatch):
    module = _refresh_module()
    jobs = _run_jobs("2026-10-03")
    jobs[1] = _wheel_job("windows-latest / Python 3.12", "2026-10-03", conclusion="failure")
    jobs.append(_wheel_job("windows-latest / Python 3.12", "2026-10-03"))  # re-run attempt
    jobs.append({"name": "macos-latest / Python 3.12", "steps": None})  # queued, no steps yet
    pages = {1: OWN_CI_RUNS[:1], 2: OWN_CI_RUNS[1:]}

    def get_json(url):
        if "/actions/workflows/published-wheel.yml/runs?" in url:
            page = int(url.rsplit("page=", 1)[1])
            return {"total_count": 2, "workflow_runs": pages[page]}
        if "/actions/runs/37111363411/jobs?" in url:
            assert "filter=all" in url
            return {"total_count": len(jobs), "jobs": jobs}
        if "/actions/runs/36190628659/jobs?" in url:
            return {"total_count": 5, "jobs": _run_jobs("2026-09-25")}
        raise AssertionError(url)

    monkeypatch.setattr(module, "_get_json", get_json)
    records = module.fetch_published_wheel_runs("2026-09-04", "2026-10-03")
    assert records == [
        {"run_id": 36190628659, "date": "2026-09-25", "event": "workflow_dispatch",
         "wheel_install_jobs": 4},
        {"run_id": 37111363411, "date": "2026-10-03", "event": "schedule",
         "wheel_install_jobs": 4},
    ]


@pytest.mark.parametrize("payload,error", [
    ({"workflow_runs": []}, TypeError),
    ({"total_count": 1, "workflow_runs": None}, TypeError),
    ({"total_count": 1, "workflow_runs": ["not an object"]}, TypeError),
    ({"total_count": 3, "workflow_runs": OWN_CI_RUNS[:1]}, ValueError),
])
def test_published_wheel_collector_rejects_bad_or_partial_pages(monkeypatch, payload, error):
    module = _refresh_module()

    def get_json(url):
        if "/actions/workflows/published-wheel.yml/runs?" in url:
            return payload if url.endswith("&page=1") else {"total_count": 3, "workflow_runs": []}
        return {"total_count": 5, "jobs": _run_jobs("2026-10-03")}

    monkeypatch.setattr(module, "_get_json", get_json)
    with pytest.raises(error):
        module.fetch_published_wheel_runs("2026-09-04", "2026-10-03")


def test_published_wheel_collector_refuses_a_renamed_install_step(monkeypatch):
    """A successful run with no install step must not read as zero CI installs."""
    module = _refresh_module()
    renamed = [{"name": "ubuntu-latest / Python 3.12", "steps": [
        {"name": "Install wheel", "conclusion": "success", "started_at": "2026-10-03T08:57:00Z"},
    ]}]
    _mock_own_ci_feeds(monkeypatch, module, runs=OWN_CI_RUNS[:1], jobs={37111363411: renamed})
    with pytest.raises(ValueError, match="install step"):
        module.fetch_published_wheel_runs("2026-09-04", "2026-10-03")


def test_empty_report_has_no_interpreter_caveat(tmp_path):
    assert not any("null interpreter" in note for note in _classify(tmp_path, {})["unknowns"])


@pytest.mark.parametrize("rows,error", [(None, None), ([], "OSError")])
def test_empty_pypi_refresh_has_no_interpreter_caveat(tmp_path, rows, error):
    snapshot = _refresh_module().build_snapshot(
        retrieved_at="2026-10-02T08:00:00Z", pypi_rows=rows, pypi_error=error,
        npm=None, feedback_reports=[],
    )
    assert not any("null interpreter" in note for note in snapshot["unknowns"])
    assert not any("null interpreter" in note for note in _classify(tmp_path, snapshot)["unknowns"])


@pytest.mark.integration
def test_feedback_runs_from_installed_distribution(tmp_path):
    target = tmp_path / "site-packages"
    subprocess.run(
        [sys.executable, "-m", "pip", "install", str(ROOT / "sdk"), "--target", str(target)],
        check=True,
        capture_output=True,
        text=True,
    )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(target)
    env.pop("PYTHONHOME", None)
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import io, os, tempfile, pathlib, agentguard.demo as demo, agentguard.feedback as fb;"
                "path=os.path.join(tempfile.mkdtemp(), 't.jsonl');"
                "buf=io.StringIO();"
                "code=demo.run_offline_demo(trace_path=path, stream=buf, feedback=True);"
                "text=buf.getvalue();"
                "src=pathlib.Path(demo.__file__).read_text()+pathlib.Path(fb.__file__).read_text();"
                "print(code);"
                "print('SENT' if 'Nothing was sent.' in text else 'MISSING');"
                "print(demo.__file__);"
                "print(fb.__file__);"
                "print('SRC_OK' if 'import urllib' not in src and 'import http.client' not in src else 'SRC_BAD');"
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
    assert lines[0] == "0"
    assert lines[1] == "SENT"
    installed = Path(lines[2]).resolve()
    feedback_installed = Path(lines[3]).resolve()
    assert lines[4] == "SRC_OK"
    assert target.resolve() in installed.parents or installed.parent == target.resolve()
    assert target.resolve() in feedback_installed.parents or feedback_installed.parent == target.resolve()
    assert installed != (ROOT / "sdk" / "agentguard" / "demo.py").resolve()
