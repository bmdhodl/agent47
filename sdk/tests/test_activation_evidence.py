"""AG-02: activation evidence and voluntary demo feedback."""
from __future__ import annotations

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
