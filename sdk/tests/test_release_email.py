"""Release mail requires both published artifacts and a stable delivery key."""

import importlib.util
import io
import json
import threading
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("release_email", ROOT / "scripts/send_release_email.py")
sender = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sender)


def release():
    return {"tag_name": "v1.3.1", "draft": False, "prerelease": False,
            "published_at": "2026-09-15T00:00:00Z",
            "html_url": "https://github.com/bmdhodl/agent47/releases/tag/v1.3.1"}


def package():
    return {"info": {"version": "1.3.1"}, "urls": [{"yanked": False}]}


def test_stable_release_has_scoped_audience_and_repeatable_campaign():
    payload = sender.build_payload("v1.3.1", release(), package())
    assert payload["audience"] == "agentguard"
    assert payload["campaign_key"] == "agentguard-release:v1.3.1"
    assert "agentguard47==1.3.1" in payload["markdown"]
    assert "python -m agentguard.cli demo --feedback" in payload["markdown"]
    assert "docs/guides/try-release.md" in payload["markdown"]
    assert "reply with your result" in payload["markdown"]
    assert payload == sender.build_payload("v1.3.1", release(), package())


@pytest.mark.parametrize("tag", ["v1.3.2rc1", "main", "v1.3.1\nattack", "--help"])
def test_invalid_tag(tag):
    with pytest.raises(ValueError):
        sender.build_payload(tag, release(), package())


@pytest.mark.parametrize("field,value", [("draft", True), ("prerelease", True),
                                       ("published_at", None), ("tag_name", "v1.3.2"),
                                       ("html_url", "https://example.com")])
def test_unpublished_or_mismatched_release(field, value):
    metadata = release()
    metadata[field] = value
    with pytest.raises(ValueError):
        sender.build_payload("v1.3.1", metadata, package())


@pytest.mark.parametrize("metadata", [{"info": {"version": "1.3.0"}, "urls": [{}]},
                                      {"info": {"version": "1.3.1"}, "urls": []},
                                      {"info": {"version": "1.3.1"}, "urls": [{"yanked": True}]}])
def test_package_must_exist_and_not_be_yanked(metadata):
    with pytest.raises(ValueError):
        sender.build_payload("v1.3.1", release(), metadata)


def test_missing_credentials_never_sends():
    with patch.object(sender, "urlopen") as request:
        with pytest.raises(ValueError):
            sender.send({}, None)
        request.assert_not_called()


def test_send_uses_scoped_payload_and_redacts_response_details():
    payload = sender.build_payload("v1.3.1", release(), package())
    response = io.BytesIO(json.dumps({"ok": True, "accepted": 2, "private": "must-not-log"}).encode())
    with patch.object(sender, "urlopen", return_value=response) as request:
        assert sender.send(payload, "test-key") == {"ok": True, "accepted": 2}
    outgoing = request.call_args.args[0]
    assert outgoing.full_url == sender.ENDPOINT
    assert json.loads(outgoing.data)["campaign_key"] == "agentguard-release:v1.3.1"


def test_partial_service_failure_is_not_success():
    with patch.object(sender, "urlopen", return_value=io.BytesIO(b'{"ok": false}')), pytest.raises(RuntimeError):
        sender.send({}, "test-key")


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
def test_credentials_are_never_forwarded_on_redirect(status):
    paths = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            paths.append(self.path)
            self.send_response(status)
            self.send_header("Location", f"http://localhost:{self.server.server_port}/target")
            self.end_headers()

        def log_message(self, *args):
            pass

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with pytest.raises(urllib.error.HTTPError):
                sender.get_json(f"http://127.0.0.1:{server.server_port}/start", "test-secret")
            assert paths == ["/start"]
        finally:
            server.shutdown()
            thread.join()


def test_email_job_is_independent_of_discussions_and_existing_publish_dispatches_it():
    workflow = (ROOT / ".github/workflows/release-content.yml").read_text()
    assert "  email:\n" in workflow
    assert "python scripts/send_release_email.py" in workflow
    assert "gh workflow run release-content.yml" in (ROOT / ".github/workflows/publish.yml").read_text()
