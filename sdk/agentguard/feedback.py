"""Local-only redacted demo feedback. Never sends network traffic."""
from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

ALLOWED_FIELDS = ("version", "adapter", "result", "reproduction")
ISSUE_TEMPLATE_URL = (
    "https://github.com/bmdhodl/agent47/issues/new"
    "?template=activation_feedback.yml"
)
NOTHING_SENT = "Nothing was sent."
DECLINE_HINT = (
    "Optional: inspect a redacted feedback report (nothing is sent):\n"
    "  agentguard demo --feedback\n"
    "Decline by skipping that command."
)


def build_demo_feedback(
    *,
    version: str,
    adapter: str = "offline-demo",
    result: str = "success",
    reproduction: str = "agentguard demo",
    omit: Optional[Sequence[str]] = None,
) -> dict[str, str]:
    """Return the four allowed fields, minus any the user omitted."""
    payload = {
        "version": version,
        "adapter": adapter,
        "result": result,
        "reproduction": reproduction,
    }
    skipped = {name.strip() for name in (omit or ()) if name}
    unknown = skipped - set(ALLOWED_FIELDS)
    if unknown:
        raise ValueError(
            "omit must be one of {}, not {}".format(
                ", ".join(ALLOWED_FIELDS),
                ", ".join(sorted(unknown)),
            )
        )
    return {key: payload[key] for key in ALLOWED_FIELDS if key not in skipped}


def render_feedback_markdown(report: Mapping[str, str]) -> str:
    """Render an inspectable Markdown report with no extra fields."""
    lines = [
        "# AgentGuard demo feedback",
        "",
        NOTHING_SENT,
        "Inspect this locally, redact with `--omit`, then paste into the",
        "GitHub issue template if you want to share it.",
        "",
    ]
    for key in ALLOWED_FIELDS:
        if key in report:
            lines.append(f"- **{key}:** {report[key]}")
    lines.extend(["", f"Share template: {ISSUE_TEMPLATE_URL}", ""])
    return "\n".join(lines)


def assert_redacted(report: Mapping[str, Any]) -> None:
    """Refuse payloads that include anything beyond the four allowed fields."""
    extra = set(report) - set(ALLOWED_FIELDS)
    if extra:
        raise ValueError(
            "feedback payload has forbidden fields: {}".format(", ".join(sorted(extra)))
        )
    for key, value in report.items():
        if not isinstance(value, str):
            raise TypeError(f"{key} must be a string")
