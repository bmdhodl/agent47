"""Local-first agent template, guarded by AgentGuard.

A hand-rolled agent loop -- no framework -- that calls a *local*
OpenAI-compatible model server (llama.cpp, Ollama, LM Studio) while AgentGuard
enforces a budget cap, a rate limit, and a tool allowlist, and writes a JSONL
audit line for every decision.

Defaults to offline mode (no model server, no GPU, no network) so it runs in
CI. Set AGENTGUARD_LOCAL_DEMO=live to call a real server. See README.md.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

# Allow `python examples/local-first-template/agent.py` from a source checkout
# without an editable install. A real consumer just `pip install agentguard47`.
_SDK = Path(__file__).resolve().parents[2] / "sdk"
if _SDK.is_dir() and str(_SDK) not in sys.path:
    sys.path.insert(0, str(_SDK))

from agentguard import (  # noqa: E402
    BudgetExceeded,
    BudgetGuard,
    JsonlFileSink,
    RateLimitGuard,
    Tracer,
    estimate_cost,
)

from config import AgentPolicy  # noqa: E402


class ToolDenied(RuntimeError):
    """Raised when the agent tries to call a tool outside the allowlist."""


class LocalChatClient:
    """Minimal client for an OpenAI-compatible local chat endpoint.

    Uses only the standard library -- no `openai`, no `requests`. llama.cpp's
    `llama-server` and Ollama both serve `POST /v1/chat/completions`.

    In offline mode (`AGENTGUARD_LOCAL_DEMO` != "live") no socket is opened;
    a deterministic canned reply is returned so the example runs in CI.
    """

    def __init__(self, policy: AgentPolicy, *, offline: bool) -> None:
        self._policy = policy
        self._offline = offline

    def complete(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Return a dict with `content`, `prompt_tokens`, `completion_tokens`."""
        if self._offline:
            return self._offline_reply(messages)
        return self._live_reply(messages)

    def _live_reply(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        url = self._policy.base_url.rstrip("/") + "/v1/chat/completions"
        body = json.dumps(
            {"model": self._policy.model, "messages": messages, "stream": False}
        ).encode("utf-8")
        req = urllib.request.Request(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, OSError) as exc:
            raise RuntimeError(
                f"Could not reach local model server at {url}. "
                f"Start llama-server / Ollama first, or run in offline mode. ({exc})"
            ) from exc
        choice = payload["choices"][0]["message"]["content"]
        usage = payload.get("usage") or {}
        # Some local servers omit `usage`. Falling back to 0 would silently
        # disable the token budget, so estimate from text length (~4 chars
        # per token) when the server does not report counts.
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        if prompt_tokens == 0:
            prompt_tokens = max(1, sum(len(m["content"]) for m in messages) // 4)
        if completion_tokens == 0:
            completion_tokens = max(1, len(choice) // 4)
        return {
            "content": choice,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }

    def _offline_reply(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """Deterministic stand-in for a local model. No network.

        Drives the loop through every guard path so the audit log is
        representative: turn 1 attempts a disallowed tool (allowlist denial),
        turn 2 uses the allowed tool, turn 3 answers.
        """
        last = messages[-1]["content"]
        if last.startswith("read_file returned:"):
            content = "The summary is ready; the file describes a local-first agent."
        elif "not allowed" in last:
            content = 'TOOL_CALL: read_file {"path": "sample_task.txt"}'
        else:
            # First user turn: model hallucinates a tool outside the allowlist.
            content = 'TOOL_CALL: run_shell {"cmd": "cat /etc/passwd"}'
        approx_tokens = max(1, len(last) // 4)
        return {
            "content": content,
            "prompt_tokens": approx_tokens,
            "completion_tokens": max(1, len(content) // 4),
        }


def read_file_tool(path: str, *, base_dir: Path) -> str:
    """The one allowed tool: read a text file under base_dir."""
    if not path:
        raise ToolDenied("read_file requires a non-empty 'path' argument")
    target = (base_dir / path).resolve()
    if base_dir.resolve() not in target.parents and target != base_dir.resolve():
        raise ToolDenied(f"read_file refused path outside base dir: {path}")
    if not target.is_file():
        raise ToolDenied(f"read_file: not a readable file: {path}")
    return target.read_text(encoding="utf-8")


def parse_tool_call(content: str) -> Optional[Dict[str, Any]]:
    """Parse a `TOOL_CALL: name {json-args}` line.

    Returns None if the content is not a tool call. For a tool call with
    malformed JSON args, returns the call with ``"valid_args": False`` so the
    loop can treat it as a failed call instead of crashing on empty args.
    """
    if not content.startswith("TOOL_CALL:"):
        return None
    rest = content[len("TOOL_CALL:") :].strip()
    name, _, raw_args = rest.partition(" ")
    valid_args = True
    try:
        args = json.loads(raw_args) if raw_args else {}
        if not isinstance(args, dict):
            args, valid_args = {}, False
    except json.JSONDecodeError:
        args, valid_args = {}, False
    return {"name": name, "args": args, "valid_args": valid_args}


def run_agent(policy: AgentPolicy, *, offline: bool, base_dir: Path) -> int:
    """Run the guarded local agent loop. Returns a process exit code."""
    sink = JsonlFileSink(policy.audit_log_path)
    tracer = Tracer(sink=sink, service="local-first-template")

    budget = BudgetGuard(
        max_tokens=policy.max_tokens,
        max_calls=policy.max_calls,
        max_cost_usd=policy.max_cost_usd,
        warn_at_pct=policy.warn_at_pct,
        on_warning=lambda msg: print(f"  [budget warning] {msg}"),
    )
    rate = RateLimitGuard(max_calls_per_minute=policy.max_calls_per_minute)
    client = LocalChatClient(policy, offline=offline)

    print(f"Model server : {policy.base_url} (offline={offline})")
    print(f"Budget       : {policy.max_tokens} tokens / {policy.max_calls} calls")
    print(f"Rate limit   : {policy.max_calls_per_minute}/min")
    print(f"Allowed tools: {', '.join(policy.allowed_tools)}")
    print(f"Audit log    : {policy.audit_log_path}")
    print("-" * 60)

    messages: List[Dict[str, str]] = [
        {"role": "system", "content": "You are a local agent. Use tools when needed."},
        {"role": "user", "content": "Please summarize the local task file."},
    ]
    for turn in range(1, policy.max_calls + 2):
        try:
            with tracer.trace(f"agent.turn.{turn}") as ctx:
                # Rate check before every model call.
                rate.check()
                ctx.event("guard.rate_check", data={"turn": turn, "ok": True})

                reply = client.complete(messages)
                tokens = reply["prompt_tokens"] + reply["completion_tokens"]
                # estimate_cost is ~0 for an unknown local model, but real if
                # the user points the template at a paid OpenAI-compatible
                # endpoint -- so the dollar budget actually enforces there.
                # A local model name is unpriced; suppress that expected warning.
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    cost = estimate_cost(
                        policy.model,
                        input_tokens=reply["prompt_tokens"],
                        output_tokens=reply["completion_tokens"],
                    )
                budget.consume(tokens=tokens, calls=1, cost_usd=cost)
                ctx.event(
                    "llm.call",
                    data={
                        "turn": turn,
                        "tokens": tokens,
                        "tokens_used": budget.state.tokens_used,
                        "cost_usd": cost,
                        "content": reply["content"][:120],
                    },
                )
                print(
                    f"  [{turn}] tokens={tokens} "
                    f"total={budget.state.tokens_used}/{policy.max_tokens}  "
                    f"{reply['content'][:60]}"
                )

                call = parse_tool_call(reply["content"])
                if call is None:
                    ctx.event("agent.final", data={"answer": reply["content"][:120]})
                    print(f"\nFinal answer: {reply['content']}")
                    break

                # --- Tool allowlist enforcement ---
                if call["name"] not in policy.allowed_tools:
                    ctx.event(
                        "guard.tool_denied",
                        data={"tool": call["name"], "args": call["args"]},
                    )
                    print(f"  [tool DENIED] '{call['name']}' not in allowlist")
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                f"Tool '{call['name']}' is not allowed. "
                                f"Answer directly instead."
                            ),
                        }
                    )
                    continue

                # Malformed tool args: treat as a failed call, do not crash.
                if not call["valid_args"]:
                    ctx.event(
                        "guard.tool_failed",
                        data={"tool": call["name"], "reason": "malformed args"},
                    )
                    print(f"  [tool FAILED] '{call['name']}' had malformed args")
                    messages.append(
                        {
                            "role": "user",
                            "content": f"Tool '{call['name']}' args were invalid. "
                            f"Answer directly instead.",
                        }
                    )
                    continue

                with ctx.span(f"tool.{call['name']}") as tool_ctx:
                    tool_ctx.event("tool.call", data={"tool": call["name"], "args": call["args"]})
                    try:
                        result = read_file_tool(
                            call["args"].get("path", ""), base_dir=base_dir
                        )
                    except ToolDenied as exc:
                        tool_ctx.event("guard.tool_failed", data={"reason": str(exc)})
                        print(f"  [tool FAILED] {exc}")
                        messages.append(
                            {
                                "role": "user",
                                "content": f"read_file failed: {exc}. Answer directly.",
                            }
                        )
                        continue
                    tool_ctx.event("tool.result", data={"chars": len(result)})
                messages.append(
                    {"role": "user", "content": f"read_file returned: {result}"}
                )
        except BudgetExceeded as exc:
            # RateLimitGuard and BudgetGuard both raise BudgetExceeded; use a
            # neutral label since either guard could be the stop reason.
            print(f"\n  [guard STOP] {exc}")
            break
    else:
        print("\n  Loop hit max_calls without a final answer.")

    print("-" * 60)
    print(
        f"Done. {budget.state.calls_used} calls, "
        f"{budget.state.tokens_used} tokens. Audit log: {policy.audit_log_path}"
    )
    print("View it:  agentguard report " + policy.audit_log_path)
    return 0


def main() -> int:
    offline = os.environ.get("AGENTGUARD_LOCAL_DEMO", "offline").lower() != "live"
    policy = AgentPolicy.from_env()
    base_dir = Path(__file__).resolve().parent
    return run_agent(policy, offline=offline, base_dir=base_dir)


if __name__ == "__main__":
    raise SystemExit(main())
