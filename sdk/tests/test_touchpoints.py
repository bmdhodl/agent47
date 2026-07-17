"""Touchpoint tests for the AgentGuard -> bmdpat.com funnel (Build Order Step 1).

The opt-in bridge to the hosted page must stay present on every public surface
(README/PyPI, ``agentguard --help`` footer, first-run welcome) so the funnel
cannot silently regress, and it must stay honest: static links only, framed as
optional, with the "nothing phones home" promise intact. These are the
trust-preserving invariants, not cosmetic copy.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest import mock

import pytest

from agentguard import cli
from agentguard.first_run import SITE_URL, hosted_url, render_welcome

REPO_ROOT = Path(__file__).resolve().parents[2]
HOSTED_HOST = "bmdpat.com/tools/agentguard"


def test_hosted_url_points_at_bmdpat_and_is_utm_tagged():
    url = hosted_url("cli-help")
    assert url.startswith("https://" + HOSTED_HOST)
    assert "utm_source=agentguard47" in url
    assert "utm_medium=cli-help" in url
    assert "utm_campaign=touchpoints" in url


def test_hosted_url_medium_names_the_surface():
    assert "utm_medium=cli-welcome" in hosted_url("cli-welcome")
    assert "utm_medium=readme" in hosted_url("readme")


def test_site_url_is_https_bmdpat():
    assert SITE_URL == "https://" + HOSTED_HOST


def test_readme_bridges_to_bmdpat_and_stays_honest():
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    assert HOSTED_HOST in readme
    # Anti-dark-pattern guardrail: the opt-in framing and the no-telemetry
    # promise must ship alongside the link, never the link alone.
    assert "optional" in readme.lower()
    assert "phones home" in readme


def test_pypi_readme_carries_the_same_bridge():
    # The PyPI page is what ~all installers see; the bridge must survive
    # generation into sdk/PYPI_README.md.
    pypi = (REPO_ROOT / "sdk" / "PYPI_README.md").read_text(encoding="utf-8")
    assert HOSTED_HOST in pypi
    assert "phones home" in pypi


def _run_cli_expecting_exit(argv):
    buf = io.StringIO()
    with mock.patch.object(sys, "argv", argv):
        from contextlib import redirect_stdout

        with redirect_stdout(buf), pytest.raises(SystemExit) as exc:
            cli.main()
    return exc.value.code, buf.getvalue()


def test_cli_help_footer_bridges_to_bmdpat():
    code, out = _run_cli_expecting_exit(["agentguard", "--help"])
    assert code == 0
    assert HOSTED_HOST in out
    assert "phones home" in out


def test_welcome_shows_optional_hosted_bridge():
    buf = io.StringIO()
    render_welcome(stream=buf)
    out = buf.getvalue()
    assert HOSTED_HOST in out
    # Optional framing so the hosted layer never reads as required.
    assert "Optional hosted layer" in out
    # The no-phone-home guarantee must ride along on the first-run surface too,
    # not only in the CLI --help footer.
    assert "phones home" in out
