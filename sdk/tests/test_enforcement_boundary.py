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
    "recorded-event preflight",
    "reservation-backed",
    "unsupported",
}
PRODUCT_DOCS = (
    ROOT / "README.md",
    ROOT / "docs" / "cost-guardrails.md",
    ROOT / "docs" / "guides" / "getting-started.md",
    ROOT / "docs" / "README.md",
    ROOT / "docs" / "launch" / "show-hn.md",
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
    r"before they happen|hard dollar (limits?|ceiling|stops?|budgets?)|"
    r"stop runaway AI (bills|agent costs)|guaranteed invoice|"
    r"invoice cap we enforce|stops the moment it exceeds|"
    r"Hard budget limits that (actually )?stop|"
    r"Budget enforcement that actually stops",
    re.I,
)
TABLE_RE = re.compile(
    r"^\| (?!Surface)(?!---)(.+?) \| (advisory|recorded-budget preflight|"
    r"recorded-event preflight|reservation-backed|unsupported) \| "
    r"(`[^`]+`|[^|]+) \| (.+?) \|\s*$",
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
        "recorded-event preflight",
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
    assert payload["consume_succeeded"] == 1
    assert payload["consume_blocked"] == 1
    assert payload["recorded_calls"] == 2
    assert "consume() increments then raises" in payload["note"]


def test_examples_run_from_installed_distribution(tmp_path):
    target = tmp_path / "site-packages"
    target.mkdir()
    install = subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            str(ROOT / "sdk"),
            "--target",
            str(target),
            "--no-deps",
            "--disable-pip-version-check",
        ],
        capture_output=True,
        text=True,
    )
    assert install.returncode == 0, install.stderr or install.stdout
    env = os.environ.copy()
    env["PYTHONPATH"] = str(target)
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import importlib.metadata as m, pathlib, agentguard; "
                "print(m.version('agentguard47')); "
                "print(pathlib.Path(agentguard.__file__).resolve())"
            ),
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert probe.returncode == 0, probe.stderr
    lines = [line.strip() for line in probe.stdout.splitlines() if line.strip()]
    assert len(lines) >= 2
    version, installed = lines[0], lines[1]
    assert version
    installed_path = Path(installed).resolve()
    target_resolved = target.resolve()
    assert target_resolved == installed_path or target_resolved in installed_path.parents
    repo_init = (ROOT / "sdk" / "agentguard" / "__init__.py").resolve()
    assert installed_path != repo_init
    scripts = [
        ROOT / "examples" / "enforcement_boundary" / name
        for name in (
            "exhausted_budget_blocks_dispatch.py",
            "two_worker_overshoot.py",
            "reserved_one_dispatch.py",
        )
    ]
    scripts.append(ROOT / "examples" / "shared_call_limit.py")
    for script in scripts:
        completed = subprocess.run(
            [sys.executable, str(script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
            env=env,
        )
        if script.name == "reserved_one_dispatch.py":
            payload = json.loads(completed.stdout)
            assert payload["dispatched"] == 1
            assert payload["blocked"] == 1
            assert payload["fixed"] is True
            assert installed_path != repo_init
        if script.name == "shared_call_limit.py":
            source = script.read_text(encoding="utf-8")
            assert "_traced_openai_create" not in source
            assert "patch_openai" in source
            result_line = next(
                line for line in completed.stdout.splitlines() if line.startswith("RESULT ")
            )
            payload = json.loads(result_line.removeprefix("RESULT "))
            assert payload["dispatched"] == 1
            assert payload["stopped"] == 1
            assert payload["fixed"] is True
            assert payload["provider"] == "simulated"
            assert "Not a provider invoice cap." in completed.stdout


def test_cli_demo_budget_path_is_advisory():
    source = (ROOT / "sdk" / "agentguard" / "demo.py").read_text(encoding="utf-8")
    budget_fn = source.split("def _run_budget_demo", 1)[1].split("def _run_loop_demo", 1)[0]
    assert '"llm.result"' in budget_fn or "'llm.result'" in budget_fn
    assert budget_fn.find("llm.result") < budget_fn.find("budget.consume")
    rows = {surface: class_name for surface, class_name, _, _ in _rows()}
    assert rows["CLI `demo`"] == "advisory"


def test_live_html_meta_rejects_invoice_guarantees():
    meta_re = re.compile(
        r"<meta[^>]+(?:name|property)=['\"](?:description|og:description|twitter:description)['\"][^>]*content=['\"]([^'\"]+)['\"]",
        re.I,
    )
    meta_re_alt = re.compile(
        r"<meta[^>]+content=['\"]([^'\"]+)['\"][^>]+(?:name|property)=['\"](?:description|og:description|twitter:description)['\"]",
        re.I,
    )
    for path in (ROOT / "site").rglob("*.html"):
        text = path.read_text(encoding="utf-8")
        contents = meta_re.findall(text) + meta_re_alt.findall(text)
        for content in contents:
            match = FORBIDDEN_CLAIM_RE.search(content)
            assert match is None, f"{path}: forbidden meta {match.group(0)!r}"


def test_historical_surfaces_link_enforcement():
    paths = list((ROOT / "site" / "blog").glob("*.html"))
    paths.extend(p for p in (ROOT / "docs" / "blog").glob("*.md") if p.name != "PUBLISHING.md")
    paths.extend((ROOT / "docs" / "discussions").glob("*.md"))
    assert paths
    for path in paths:
        text = path.read_text(encoding="utf-8")
        assert "enforcement-boundary.md" in text or "enforcement.html" in text, path.name


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def test_langgraph_public_copy_uses_call_budget():
    pages = (
        ROOT / "docs" / "integrations" / "langgraph.md",
        ROOT / "docs" / "discussions" / "05_langgraph_cost_tracking.md",
        ROOT / "site" / "blog" / "langchain-cost-tracking.html",
    )
    for path in pages:
        text = _strip_tags(path.read_text(encoding="utf-8"))
        assert "max_calls" in text, path
        assert "consume(calls=1)" in text.replace(" ", "")
        assert "$5 limit" not in text
        assert "guard_node(budget_guard=budget)" not in text.replace(" ", "")
        assert "+ [result]" not in text
        assert "+ [summary]" not in text
    guide = (ROOT / "docs" / "integrations" / "langgraph.md").read_text(encoding="utf-8")
    assert "BudgetGuard(max_calls=20)" in guide


def test_crewai_quickstart_constructs_valid_agent():
    text = (ROOT / "docs" / "integrations" / "crewai.md").read_text(encoding="utf-8")
    assert "from crewai import Agent" in text
    assert 'goal="Answer one short question clearly."' in text
    assert 'backstory="You are concise and careful."' in text
    assert "AgentGuardCrewCallback" in text


def test_live_blogs_do_not_claim_all_openai_surfaces():
    for path in (ROOT / "site" / "blog").glob("*.html"):
        text = _strip_tags(path.read_text(encoding="utf-8"))
        lowered = text.lower()
        assert "every openai call is intercepted" not in lowered, path.name
        assert "intercepting every openai api call" not in lowered, path.name


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
    assert "onboarding" in notes.lower()
    assert "intercept" in notes.lower()
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
    original_path = list(sys.path)
    sys.path.insert(0, str(ROOT / "agentguard-mcp"))
    try:
        from agentguard_mcp.storage import BudgetStore

        store = BudgetStore(tmp_path / "state.db")
        store.set_budget("global", 1, None, "day")
        allowed = store.record_call("github", "create_issue", 1, 0, 0.0, None)
        denied = store.record_call("github", "create_issue", 1, 0, 0.0, None)
        assert allowed["allowed"] is True
        assert denied["allowed"] is False
        assert store.check_remaining("global")["tokens_used"] == 1
    finally:
        sys.path[:] = original_path


def test_rendered_enforcement_page_states_bounds():
    html = (ROOT / "site" / "enforcement.html").read_text(encoding="utf-8")
    for needle in (
        "recorded-budget preflight",
        "recorded-event preflight",
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


def test_site_patch_examples_pass_a_budget_guard():
    # patch_openai(tracer) alone records cost but never raises; compare.html once shipped it.
    for path in (ROOT / "site").rglob("*.html"):
        text = _strip_tags(path.read_text(encoding="utf-8"))
        for match in re.finditer(r"patch_(?:openai|anthropic)\(", text):
            depth, end = 1, match.end()
            while depth:
                depth += {"(": 1, ")": -1}.get(text[end], 0)
                end += 1
            call = text[match.start():end]
            assert "budget_guard=" in call, f"{path.name}: {call}"
