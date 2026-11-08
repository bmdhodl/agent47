"""REGRESSION: a moved or unreadable rules tag must stop the scanner."""
import importlib.util
import json
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("trustabl_rules", ROOT / "scripts/verify_trustabl_rules.py")
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
EXPECTED = "97918c43909166334a2df941cff64d9f63acb115"
TAG = "87bb6d28ca359db77e9d4d508869a4e59e17b9f4"


def install_api(monkeypatch, objects):
    calls = []

    def read(endpoint):
        calls.append(endpoint)
        result = objects[len(calls) - 1]
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(guard, "read_object", read)
    return calls


@pytest.mark.parametrize("annotated", [True, False])
def test_matching_tag_resolves_to_commit(monkeypatch, capsys, annotated):
    objects = [{"type": "tag", "sha": TAG}, {"type": "commit", "sha": EXPECTED}]
    calls = install_api(monkeypatch, objects if annotated else [objects[1]])
    assert guard.main(["--ref", "v0.2.0", "--expected", EXPECTED]) == 0
    assert calls[0] == "git/ref/tags/v0.2.0"
    assert calls[1:] == ([f"git/tags/{TAG}"] if annotated else [])
    assert f"v0.2.0 matches inspected commit {EXPECTED}" in capsys.readouterr().out


def test_moved_tag_names_expected_and_resolved_commits(monkeypatch, capsys):
    moved = "a" * 40
    install_api(monkeypatch, [{"type": "tag", "sha": TAG}, {"type": "commit", "sha": moved}])
    assert guard.main(["--ref", "v0.2.0", "--expected", EXPECTED]) == 1
    error = capsys.readouterr().err
    assert "v0.2.0" in error and EXPECTED in error and moved in error


@pytest.mark.parametrize("failure_at", [0, 1])
@pytest.mark.parametrize("error", [URLError("network unavailable"), HTTPError("https://api.github.com", 403, "Forbidden", {}, None)])
def test_api_failure_is_fatal(monkeypatch, capsys, failure_at, error):
    objects = [*[{"type": "tag", "sha": TAG}][:failure_at], error]
    calls = install_api(monkeypatch, objects)
    assert guard.main(["--ref", "v0.2.0", "--expected", EXPECTED]) == 1
    assert len(calls) == failure_at + 1
    assert "Could not verify rules tag v0.2.0" in capsys.readouterr().err


@pytest.mark.parametrize("obj", [{}, {"type": "tree", "sha": EXPECTED}, {"type": "tag", "sha": "../bad"}])
def test_invalid_api_object_is_fatal(monkeypatch, obj, capsys):
    install_api(monkeypatch, [obj])
    assert guard.main(["--ref", "v0.2.0", "--expected", EXPECTED]) == 1
    assert "Could not verify" in capsys.readouterr().err


def test_read_object_uses_renamed_repo_and_bounded_authenticated_request(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"object": {"type": "commit", "sha": EXPECTED}}).encode()

    def open_request(request, *, timeout):
        assert request.full_url == "https://api.github.com/repos/trustabl/agent-reliability-rules/git/ref/tags/v0.2.0"
        assert request.get_header("Authorization") == "Bearer fixture-only"
        assert timeout == 20
        return Response()

    monkeypatch.setenv("GITHUB_TOKEN", "fixture-only")
    monkeypatch.setattr(guard, "urlopen", open_request)
    assert guard.read_object("git/ref/tags/v0.2.0") == {"type": "commit", "sha": EXPECTED}


def test_workflow_verifies_before_scanning_and_retains_existing_policy():
    text = (ROOT / ".github/workflows/trustabl.yml").read_text(encoding="utf-8")
    assert f'TRUSTABL_RULES_SHA: "{EXPECTED}"' in text
    assert text.index("python scripts/verify_trustabl_rules.py") < text.index("uses: trustabl/trustabl-action@")
    assert '--ref v0.2.0 --expected "$TRUSTABL_RULES_SHA"' in text
    assert "GITHUB_TOKEN: ${{ github.token }}" in text
    assert "v0.6.0" in text and "re-inspection" in text
    for unchanged in ["rules-ref: v0.2.0", "version: v0.1.6", "continue-on-error: true",
                      'comment-on-pr: "false"', 'TRUSTABL_TELEMETRY: "0"',
                      "test -s trustabl.json", "test -s trustabl.sarif",
                      "trustabl/trustabl-action@d97575c864814bf4965fa2c72c044224d372723a"]:
        assert unchanged in text
