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
