import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("release_example", ROOT / "scripts/verify_release_example.py")
example = importlib.util.module_from_spec(spec)
spec.loader.exec_module(example)


def test_exit_zero_without_guard_events_is_not_proof():
    with pytest.raises(ValueError):
        example.validate_events([{"name": "trace.end"}])
    example.validate_events([{"name": name} for name in example.EVENTS])


@pytest.mark.parametrize("missing", sorted(example.EVENTS))
def test_each_stop_event_is_required(missing):
    with pytest.raises(ValueError):
        example.validate_events([{"name": name} for name in example.EVENTS - {missing}])


@pytest.mark.parametrize("tag", ["main", "v1.4.0rc1", "--help", "v1.4.0\n"])
def test_bad_tag_never_runs_installer(tag):
    with patch.object(example, "run") as run, pytest.raises(ValueError):
        example.verify_wheel(tag)
    run.assert_not_called()


def test_failed_install_never_runs_demo():
    with patch.object(example, "run", side_effect=[None, RuntimeError("install failed")]) as run, pytest.raises(RuntimeError):
        example.verify_wheel("v1.4.0")
    assert run.call_count == 2
    assert "agentguard47==1.4.0" in run.call_args.args[0]


def test_workflow_verifies_before_email_without_write_access():
    workflow = (ROOT / ".github/workflows/release-content.yml").read_text()
    assert workflow.index("python scripts/verify_release_example.py") < workflow.index("python scripts/send_release_email.py")
    email_job = workflow.split("  email:\n")[1].split("  announce:\n")[0]
    assert "contents: read" in email_job
    assert "continue-on-error" not in email_job


def test_wheel_only_skips_release_metadata(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["verify_release_example.py", "--tag", "v1.4.0", "--wheel-only"])
    with patch.object(example, "get_json") as get_json, patch.object(example, "verify_wheel") as verify:
        example.main()
    get_json.assert_not_called()
    verify.assert_called_once_with("v1.4.0")


def test_default_still_checks_release_metadata_before_wheel(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["verify_release_example.py", "--tag", "v1.4.0"])
    calls = []
    with patch.object(example, "get_json", side_effect=lambda *a: calls.append("get_json") or {}), \
            patch.object(example, "build_payload", side_effect=lambda *a: calls.append("payload")), \
            patch.object(example, "verify_wheel", side_effect=lambda tag: calls.append("wheel")):
        example.main()
    assert calls == ["get_json", "get_json", "payload", "wheel"]


def test_published_wheel_matrix_runs_after_each_publish():
    workflow = (ROOT / ".github/workflows/published-wheel.yml").read_text()
    for runner in ("ubuntu-latest", "macos-latest", "windows-latest"):
        assert runner in workflow
    assert 'python-version: "3.9"' in workflow
    assert "--wheel-only" in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "secrets." not in workflow
    assert "schedule:" not in workflow
    publish = (ROOT / ".github/workflows/publish.yml").read_text()
    assert 'gh workflow run published-wheel.yml -f tag="$TAG"' in publish
