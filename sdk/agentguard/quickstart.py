from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any, Callable, Dict, List, Optional, TextIO, Tuple

FRAMEWORK_CHOICES: Tuple[str, ...] = (
    "raw",
    "openai",
    "anthropic",
    "langchain",
    "langgraph",
    "crewai",
)


def run_quickstart(
    framework: str = "raw",
    service: str = "my-agent",
    budget_usd: float = 5.0,
    trace_file: str = ".agentguard/traces.jsonl",
    stream: Optional[TextIO] = None,
    json_output: bool = False,
    write_file: bool = False,
    output_path: Optional[str] = None,
    force: bool = False,
) -> int:
    """Render a framework-specific starter snippet for AgentGuard."""
    out = stream or sys.stdout
    normalized = framework.strip().lower()

    try:
        payload = _build_quickstart_payload(
            framework=normalized,
            service=service,
            budget_usd=budget_usd,
            trace_file=trace_file,
        )
    except ValueError as exc:
        error = {
            "status": "error",
            "error": str(exc),
            "frameworks": list(FRAMEWORK_CHOICES),
        }
        if json_output:
            out.write(json.dumps(error) + "\n")
        else:
            _print(out, "AgentGuard quickstart")
            _print(out, f"[fail] {exc}")
            _print(out, f"Available frameworks: {', '.join(FRAMEWORK_CHOICES)}")
        return 1

    destination: Optional[str] = None
    if write_file:
        try:
            destination = _write_quickstart_file(
                payload,
                output_path=output_path,
                force=force,
            )
        except (ValueError, OSError) as exc:
            error = {
                "status": "error",
                "error": str(exc),
                "framework": normalized,
            }
            if json_output:
                out.write(json.dumps(error) + "\n")
            else:
                _print(out, "AgentGuard quickstart")
                _print(out, f"[fail] {exc}")
            return 1
        payload["written_file"] = destination

    if json_output:
        out.write(json.dumps(payload) + "\n")
        return 0

    if destination is not None:
        _render_written_text(payload, destination, out)
    else:
        _render_text(payload, out)
    return 0


def _build_quickstart_payload(
    framework: str,
    service: str,
    budget_usd: float,
    trace_file: str,
) -> Dict[str, Any]:
    if framework not in _TEMPLATES:
        raise ValueError(f"Unknown framework '{framework}'")

    payload = _TEMPLATES[framework](service, budget_usd, trace_file)
    payload["status"] = "ok"
    payload["framework"] = framework
    payload["service"] = service
    payload["budget_usd"] = round(budget_usd, 2)
    payload["trace_file"] = trace_file
    payload["verify_command"] = "agentguard doctor"
    return payload


def _render_text(payload: Dict[str, Any], out: TextIO) -> None:
    _print(out, "AgentGuard quickstart")
    _print(out, f"Framework: {payload['framework']}")
    _print(out, "")
    _print(out, "Install:")
    _print(out, f"  {payload['install_command']}")
    if payload["requires_env"]:
        _print(out, "Environment:")
        for env_name in payload["requires_env"]:
            _print(out, f"  export {env_name}=...")
    _print(out, f"Suggested file: {payload['filename']}")
    _print(out, "")
    _print(out, payload["summary"])
    _print(out, "")
    _print(out, payload["snippet"])
    if payload["notes"]:
        _print(out, "")
        _print(out, "Notes:")
        for note in payload["notes"]:
            _print(out, f"  - {note}")
    _print(out, "")
    _print(out, "Next commands:")
    for command in payload["next_commands"]:
        _print(out, f"  {command}")
    _render_module_fallback(payload["next_commands"], out)


def _render_written_text(payload: Dict[str, Any], destination: str, out: TextIO) -> None:
    _print(out, "AgentGuard quickstart")
    _print(out, f"Framework: {payload['framework']}")
    _print(out, f"Wrote starter: {destination}")
    _print(out, "")
    _print(out, "Install:")
    _print(out, f"  {payload['install_command']}")
    _print(out, "")
    _print(out, payload["summary"])
    if payload["requires_env"]:
        _print(out, "")
        _print(out, "Environment:")
        for env_name in payload["requires_env"]:
            _print(out, f"  export {env_name}=...")
    if payload["notes"]:
        _print(out, "")
        _print(out, "Notes:")
        for note in payload["notes"]:
            _print(out, f"  - {note}")
    _print(out, "")
    _print(out, "Next commands:")
    rendered_commands = _rendered_next_commands(payload["next_commands"], payload["filename"], destination)
    for command in rendered_commands:
        _print(out, f"  {command}")
    _render_module_fallback(rendered_commands, out)


def _base_payload(
    *,
    install_command: str,
    filename: str,
    summary: str,
    snippet: str,
    next_commands: List[str],
    requires_env: Optional[List[str]] = None,
    notes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    return {
        "install_command": install_command,
        "filename": filename,
        "summary": summary,
        "snippet": snippet.strip(),
        "next_commands": next_commands,
        "requires_env": requires_env or [],
        "notes": notes or [],
    }


def _write_quickstart_file(
    payload: Dict[str, Any],
    *,
    output_path: Optional[str],
    force: bool,
) -> str:
    destination = Path(output_path or payload["filename"])
    if destination.exists() and not force:
        raise ValueError(
            f"Refusing to overwrite existing file: {destination}. Re-run with --force."
        )
    if destination.parent != Path("."):
        destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(payload["snippet"] + "\n", encoding="utf-8")
    return destination.as_posix()


def _rendered_next_commands(
    commands: List[str],
    filename: str,
    destination: str,
) -> List[str]:
    rendered_destination = _shell_quote_path(destination)
    rendered: List[str] = []
    for command in commands:
        rendered.append(command.replace(filename, rendered_destination))
    return rendered


def _render_module_fallback(commands: List[str], out: TextIO) -> None:
    fallback_commands = _module_command_fallbacks(commands)
    if not fallback_commands:
        return

    _print(out, "")
    _print(out, "If 'agentguard' is not on PATH:")
    for command in fallback_commands:
        _print(out, f"  {command}")


def _module_command_fallbacks(commands: List[str]) -> List[str]:
    fallback_commands: List[str] = []
    for command in commands:
        if command.startswith("agentguard "):
            fallback_commands.append("python -m agentguard.cli " + command[len("agentguard ") :])
    return fallback_commands


def _shell_quote_path(path: str) -> str:
    if not any(char.isspace() or char in {'"', "'"} for char in path):
        return path
    return '"' + path.replace('"', '\\"') + '"'


def _py_string_literal(value: str) -> str:
    """Render a Python-safe string literal for generated snippets."""
    return json.dumps(value)


def _raw_payload(service: str, budget_usd: float, trace_file: str) -> Dict[str, Any]:
    service_literal = _py_string_literal(service)
    trace_file_literal = _py_string_literal(trace_file)
    snippet = dedent(
        f"""
        import agentguard

        tracer = agentguard.init(
            profile="coding-agent",
            service={service_literal},
            budget_usd={budget_usd:.2f},
            trace_file={trace_file_literal},
            local_only=True,
        )

        @agentguard.trace_tool(tracer)
        def search_docs(query: str) -> str:
            return f"results for {{query}}"

        with tracer.trace("agent.run") as span:
            result = search_docs("agentguard quickstart")
            span.event("agent.answer", data={{"result": result}})

        print("Traces saved to " + {trace_file_literal})
        """
    )
    return _base_payload(
        install_command="pip install agentguard47",
        filename="agentguard_raw_quickstart.py",
        summary="Offline starter that proves local tracing and guard wiring without any API keys.",
        snippet=snippet,
        next_commands=[
            "agentguard doctor",
            "python agentguard_raw_quickstart.py",
            f"agentguard report {trace_file}",
        ],
        notes=[
            "This path is fully local. No dashboard and no provider API keys are required.",
            "Start here if you want a safe first run before wiring a real LLM client.",
            "Commit a .agentguard.json file if you want coding agents to reuse the same local defaults.",
        ],
    )


def _openai_payload(service: str, budget_usd: float, trace_file: str) -> Dict[str, Any]:
    service_literal = _py_string_literal(service)
    trace_file_literal = _py_string_literal(trace_file)
    snippet = dedent(
        f"""
        import agentguard
        from openai import OpenAI

        agentguard.init(
            profile="coding-agent",
            service={service_literal},
            budget_usd={budget_usd:.2f},
            trace_file={trace_file_literal},
            local_only=True,
        )

        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{{"role": "user", "content": "Give me a one-line summary of AgentGuard."}}],
        )

        print(response.choices[0].message.content)
        print("Traces saved to " + {trace_file_literal})
        """
    )
    return _base_payload(
        install_command="pip install agentguard47 openai",
        filename="agentguard_openai_quickstart.py",
        summary="Smallest OpenAI path: init once, keep local traces, let AgentGuard auto-patch the client.",
        snippet=snippet,
        next_commands=[
            "agentguard doctor",
            "python agentguard_openai_quickstart.py",
            f"agentguard incident {trace_file}",
        ],
        requires_env=["OPENAI_API_KEY"],
        notes=[
            "local_only=True keeps trace output local. Your OpenAI call still uses OPENAI_API_KEY.",
            "Auto-patching is on by default in agentguard.init().",
            "For coding agents, prefer committing .agentguard.json so the same local defaults travel with the repo.",
        ],
    )


def _anthropic_payload(service: str, budget_usd: float, trace_file: str) -> Dict[str, Any]:
    service_literal = _py_string_literal(service)
    trace_file_literal = _py_string_literal(trace_file)
    snippet = dedent(
        f"""
        import agentguard
        from anthropic import Anthropic

        agentguard.init(
            profile="coding-agent",
            service={service_literal},
            budget_usd={budget_usd:.2f},
            trace_file={trace_file_literal},
            local_only=True,
        )

        client = Anthropic()
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=128,
            messages=[{{"role": "user", "content": "Give me a one-line summary of AgentGuard."}}],
        )

        print(response.content[0].text)
        print("Traces saved to " + {trace_file_literal})
        """
    )
    return _base_payload(
        install_command="pip install agentguard47 anthropic",
        filename="agentguard_anthropic_quickstart.py",
        summary="Minimal Anthropic path with local trace output and automatic message tracing.",
        snippet=snippet,
        next_commands=[
            "agentguard doctor",
            "python agentguard_anthropic_quickstart.py",
            f"agentguard incident {trace_file}",
        ],
        requires_env=["ANTHROPIC_API_KEY"],
        notes=[
            "local_only=True affects the trace sink only. Anthropic requests still use ANTHROPIC_API_KEY.",
            "Anthropic auto-patching is enabled by default through agentguard.init().",
            "For coding agents, prefer committing .agentguard.json so the same local defaults travel with the repo.",
        ],
    )


def _langchain_payload(service: str, budget_usd: float, trace_file: str) -> Dict[str, Any]:
    service_literal = _py_string_literal(service)
    trace_file_literal = _py_string_literal(trace_file)
    snippet = dedent(
        f"""
        from agentguard import BudgetGuard, JsonlFileSink, LoopGuard, Tracer
        from agentguard.integrations.langchain import AgentGuardCallbackHandler
        from langchain_openai import ChatOpenAI

        tracer = Tracer(
            sink=JsonlFileSink({trace_file_literal}),
            service={service_literal},
        )
        loop_guard = LoopGuard(max_repeats=3, window=6)
        budget_guard = BudgetGuard(max_cost_usd={budget_usd:.2f}, max_calls=20)
        handler = AgentGuardCallbackHandler(
            tracer=tracer,
            loop_guard=loop_guard,
            budget_guard=budget_guard,
        )

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        response = llm.invoke(
            "Give me a one-line summary of AgentGuard.",
            config={{"callbacks": [handler]}},
        )

        print(response.content)
        print("Traces saved to " + {trace_file_literal})
        """
    )
    return _base_payload(
        install_command="pip install agentguard47[langchain] langchain langchain-openai",
        filename="agentguard_langchain_quickstart.py",
        summary="Callback-based LangChain starter with explicit loop and budget guards.",
        snippet=snippet,
        next_commands=[
            "agentguard doctor",
            "python agentguard_langchain_quickstart.py",
            f"agentguard report {trace_file}",
        ],
        requires_env=["OPENAI_API_KEY"],
        notes=[
            "LangChain uses the callback handler rather than agentguard.init() auto-patching.",
            "This mirrors the production wiring used by the SDK's LangChain integration.",
        ],
    )


def _langgraph_payload(service: str, budget_usd: float, trace_file: str) -> Dict[str, Any]:
    service_literal = _py_string_literal(service)
    trace_file_literal = _py_string_literal(trace_file)
    snippet = dedent(
        f"""
        from langgraph.graph import END, START, StateGraph

        from agentguard import BudgetGuard, JsonlFileSink, LoopGuard, Tracer
        from agentguard.integrations.langgraph import guard_node

        tracer = Tracer(
            sink=JsonlFileSink({trace_file_literal}),
            service={service_literal},
        )
        loop_guard = LoopGuard(max_repeats=3, window=6)
        budget_guard = BudgetGuard(max_cost_usd={budget_usd:.2f}, max_calls=20)

        def research_node(state: dict) -> dict:
            question = state["question"]
            return {{"question": question, "answer": f"local answer for {{question}}"}}

        builder = StateGraph(dict)
        builder.add_node(
            "research",
            guard_node(
                research_node,
                tracer=tracer,
                loop_guard=loop_guard,
                budget_guard=budget_guard,
            ),
        )
        builder.add_edge(START, "research")
        builder.add_edge("research", END)

        graph = builder.compile()
        result = graph.invoke({{"question": "What is AgentGuard?"}})
        print(result["answer"])
        print("Traces saved to " + {trace_file_literal})
        """
    )
    return _base_payload(
        install_command="pip install agentguard47[langgraph] langgraph",
        filename="agentguard_langgraph_quickstart.py",
        summary="Local LangGraph starter with node wrappers and no provider dependency in the example itself.",
        snippet=snippet,
        next_commands=[
            "agentguard doctor",
            "python agentguard_langgraph_quickstart.py",
            f"agentguard report {trace_file}",
        ],
        notes=[
            "This example is fully local. It uses a simple node function instead of a hosted model call.",
            "Switch the node body to your real agent logic once the guard wiring is in place.",
        ],
    )


def _crewai_payload(service: str, budget_usd: float, trace_file: str) -> Dict[str, Any]:
    service_literal = _py_string_literal(service)
    trace_file_literal = _py_string_literal(trace_file)
    snippet = dedent(
        f"""
        from crewai import Agent, Crew, Task

        from agentguard import BudgetGuard, JsonlFileSink, LoopGuard, Tracer
        from agentguard.integrations.crewai import AgentGuardCrewHandler

        tracer = Tracer(
            sink=JsonlFileSink({trace_file_literal}),
            service={service_literal},
        )
        loop_guard = LoopGuard(max_repeats=3, window=6)
        budget_guard = BudgetGuard(max_cost_usd={budget_usd:.2f}, max_calls=20)
        handler = AgentGuardCrewHandler(
            tracer=tracer,
            loop_guard=loop_guard,
            budget_guard=budget_guard,
        )

        agent = Agent(
            role="researcher",
            goal="Answer one short question clearly.",
            backstory="You are concise and careful.",
            llm="gpt-4o-mini",
            step_callback=handler.step_callback,
            verbose=True,
        )
        task = Task(
            description="Explain what AgentGuard does in one short paragraph.",
            agent=agent,
            callback=handler.task_callback,
        )

        crew = Crew(agents=[agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        print(result)
        print("Traces saved to " + {trace_file_literal})
        """
    )
    return _base_payload(
        install_command="pip install agentguard47[crewai] crewai",
        filename="agentguard_crewai_quickstart.py",
        summary="CrewAI starter that wires AgentGuard into step and task callbacks.",
        snippet=snippet,
        next_commands=[
            "agentguard doctor",
            "python agentguard_crewai_quickstart.py",
            f"agentguard incident {trace_file}",
        ],
        requires_env=["OPENAI_API_KEY"],
        notes=[
            "CrewAI still needs its normal model credentials. AgentGuard only changes tracing and guard enforcement.",
            "Use this after the offline raw or langgraph starter if you want a no-risk first run.",
        ],
    )


_TEMPLATES: Dict[str, Callable[[str, float, str], Dict[str, Any]]] = {
    "raw": _raw_payload,
    "openai": _openai_payload,
    "anthropic": _anthropic_payload,
    "langchain": _langchain_payload,
    "langgraph": _langgraph_payload,
    "crewai": _crewai_payload,
}


def _print(stream: TextIO, line: str) -> None:
    stream.write(line + "\n")
