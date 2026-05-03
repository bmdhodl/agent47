from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _normalized(text: str) -> str:
    return " ".join(text.split()).lower()


def test_dashboard_handoff_copy_stays_local_first() -> None:
    readme = _read("README.md")
    dashboard_contract = _read("docs/guides/dashboard-contract.md")
    mcp_readme = _read("mcp-server/README.md")

    combined = "\n".join([readme, dashboard_contract, mcp_readme])
    normalized_readme = _normalized(readme)
    normalized_contract = _normalized(dashboard_contract)

    for phrase in (
        "retained history",
        "alerts",
        "team visibility",
        "spend trends",
        "hosted decision history",
        "dashboard-managed remote kill signals",
    ):
        assert phrase in combined

    assert "The SDK is the free local proof path" in readme
    assert "Start local. Add hosted ingest" in readme
    assert "local guards remain authoritative" in normalized_readme
    assert "it is not required for local safety" in normalized_contract
    assert "does not replace in-process guards" in normalized_contract


def test_handoff_docs_do_not_overstate_httpsink_remote_control() -> None:
    readme = _read("README.md")
    dashboard_contract = _read("docs/guides/dashboard-contract.md")
    reporting = _read("sdk/agentguard/reporting.py")
    normalized_readme = _normalized(readme)

    assert "`HttpSink` mirrors trace and decision events" in readme
    assert "does not execute remote kill signals by itself" in normalized_readme
    assert "`HttpSink` does not poll for kill signals" in dashboard_contract
    assert "Add hosted ingest" in reporting
    assert "retained history, alerts, spend trends" in reporting
