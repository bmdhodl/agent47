"""AG-01: tested enforcement boundary and honest product claims."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / "docs" / "enforcement-boundary.md"
CLASSES = {
    "advisory",
    "recorded-budget preflight",
    "reservation-backed",
    "unsupported",
}
PRODUCT_DOCS = (
    ROOT / "README.md",
    ROOT / "docs" / "cost-guardrails.md",
    ROOT / "docs" / "guides" / "getting-started.md",
    ROOT / "docs" / "README.md",
    ROOT / "ops" / "00-NORTHSTAR.md",
    ROOT / "memory" / "distribution.md",
    ROOT / "skills" / "agentguard" / "SKILL.md",
    ROOT / "llms.txt",
    ROOT / "site" / "index.html",
    ROOT / "site" / "quickstart.html",
    ROOT / "site" / "compare.html",
    ROOT / "site" / "enforcement.html",
)
FORBIDDEN_CLAIM_RE = re.compile(
    r"before they happen|hard dollar (limits?|ceiling|stops?)|"
    r"stop runaway AI bills|guaranteed invoice|invoice cap we enforce|"
    r"stops the moment it exceeds",
    re.I,
)
TABLE_RE = re.compile(
    r"^\| (?!Surface)(?!---)(.+?) \| (advisory|recorded-budget preflight|"
    r"reservation-backed|unsupported) \| (`[^`]+`|[^|]+) \| (.+?) \|\s*$",
    re.M,
)


def _rows():
    text = MAP.read_text(encoding="utf-8")
    rows = TABLE_RE.findall(text)
    assert rows, "enforcement-boundary map table is missing"
    return rows


def test_enforcement_map_classes_and_tests_exist():
    for surface, class_name, test_ref, limitations in _rows():
        assert class_name in CLASSES, surface
        assert limitations.strip(), surface
        ref = test_ref.strip().strip("`")
        path = ref.split("::", 1)[0]
        target = ROOT / path
        assert target.exists(), f"{surface} missing test path {path}"
        if "::" in ref:
            name = ref.split("::", 1)[1]
            body = target.read_text(encoding="utf-8")
            assert name in body, f"{surface} missing {name} in {path}"


def test_map_covers_required_surfaces():
    text = MAP.read_text(encoding="utf-8")
    for needle in (
        "BudgetGuard.check()",
        "OpenAI Chat Completions",
        "Anthropic Messages",
        "LangChain LLM",
        "LangChain tool",
        "LangGraph",
        "CrewAI",
        "skillpack",
        "@agentguard47/mcp-server",
        "agentguard-mcp",
        "OpenAI Responses API",
        "subscription quota",
        "HttpSink",
        "two_worker_overshoot.py",
        "exhausted_budget_blocks_dispatch.py",
        "Direct SDK bypass",
        "In-flight spend",
        "Missing usage",
    ):
        assert needle in text, needle


def test_exhausted_example_prevents_next_dispatch():
    script = ROOT / "examples" / "enforcement_boundary" / "exhausted_budget_blocks_dispatch.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        env=_example_env(),
    )
    payload = json.loads(result.stdout)
    assert payload["next_dispatch_prevented"] is True
    assert payload["mock_provider_requests"] == 1
    assert payload["network_calls"] == 0


def test_two_worker_example_characterizes_overshoot():
    script = ROOT / "examples" / "enforcement_boundary" / "two_worker_overshoot.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
        env=_example_env(),
    )
    payload = json.loads(result.stdout)
    assert payload["overshoot"] is True
    assert payload["fixed"] is False
    assert payload["dispatched"] == 2
    assert payload["recorded_calls"] > 1


def test_examples_run_from_installed_distribution():
    import importlib.metadata as metadata

    import agentguard

    version = metadata.version("agentguard47")
    assert version
    installed = Path(agentguard.__file__).resolve()
    assert "agentguard" in str(installed)
    for name in (
        "exhausted_budget_blocks_dispatch.py",
        "two_worker_overshoot.py",
    ):
        script = ROOT / "examples" / "enforcement_boundary" / name
        subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
            env=_example_env(),
        )


def test_product_docs_reject_invoice_guarantees():
    for path in PRODUCT_DOCS:
        text = path.read_text(encoding="utf-8")
        match = FORBIDDEN_CLAIM_RE.search(text)
        assert match is None, f"{path}: forbidden claim {match.group(0)!r}"
        assert (
            "enforcement-boundary.md" in text
            or "enforcement.html" in text
            or path.name == "enforcement.html"
        )


def test_openai_responses_is_unsupported():
    source = (ROOT / "sdk" / "agentguard" / "instrument.py").read_text(encoding="utf-8")
    assert "chat.completions" in source
    assert "responses.create" not in source
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "chat.completions.create" in readme
    assert "Responses API" in MAP.read_text(encoding="utf-8")


def test_skillpack_is_not_host_enforcement():
    import io

    from agentguard.skillpack import run_skillpack

    buf = io.StringIO()
    code = run_skillpack(json_output=True, stream=buf)
    assert code == 0
    payload = json.loads(buf.getvalue())
    notes = " ".join(payload["notes"])
    assert "onboarding" in notes.lower() or "not" in notes.lower()
    assert "host" in notes.lower() or "intercept" in notes.lower()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "does not" in readme and "intercept" in readme


def test_httpsink_does_not_claim_remote_kill():
    contract = (ROOT / "docs" / "guides" / "dashboard-contract.md").read_text(encoding="utf-8")
    assert "does not poll or execute remote kill" in contract or "does not execute remote kill" in contract
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "does not execute remote kill" in readme


def test_readonly_mcp_allows_reads_and_denies_mutations():
    text = (ROOT / "mcp-server" / "src" / "tools.ts").read_text(encoding="utf-8")
    for allowed in (
        "query_traces",
        "get_trace",
        "get_trace_decisions",
        "get_alerts",
        "get_usage",
        "get_costs",
        "check_budget",
    ):
        assert f'name: "{allowed}"' in text
    for denied in ("record_call", "set_budget", "kill_switch"):
        assert f'name: "{denied}"' not in text
    assert "readOnlyHint: true" in text
    assert text.count("...READ_ONLY") >= 6
    assert "hosted event-quota" in text or "event quota" in text


def test_local_mcp_record_call_allow_and_deny(tmp_path):
    sys.path.insert(0, str(ROOT / "agentguard-mcp"))
    from agentguard_mcp.storage import BudgetStore

    store = BudgetStore(tmp_path / "state.db")
    store.set_budget("global", 1, None, "day")
    allowed = store.record_call("github", "create_issue", 1, 0, 0.0, None)
    denied = store.record_call("github", "create_issue", 1, 0, 0.0, None)
    assert allowed["allowed"] is True
    assert denied["allowed"] is False
    assert store.check_remaining("global")["tokens_used"] == 1


def test_rendered_enforcement_page_states_bounds():
    html = (ROOT / "site" / "enforcement.html").read_text(encoding="utf-8")
    for needle in (
        "recorded-budget preflight",
        "advisory",
        "reservation-backed",
        "unsupported",
        "does not reserve",
        "subscription quota",
    ):
        assert needle in html, needle


def test_site_product_pages_link_enforcement():
    for name in ("index.html", "quickstart.html", "compare.html"):
        text = (ROOT / "site" / name).read_text(encoding="utf-8")
        assert "enforcement.html" in text, name


def _example_env():
    env = os.environ.copy()
    sdk = str(ROOT / "sdk")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = sdk if not existing else os.pathsep.join([sdk, existing])
    return env
