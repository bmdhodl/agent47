"""Matching rules shared by LoopGuard and the Claude Code hook.

Two ways a stuck agent repeats itself without repeating a call byte for byte:

- structural differences in the same call, such as JSON key order;
- the same tool coming back empty, or with the same error, call after call
  while the agent rewords the input each time.

Stdlib only, and imports nothing from agentguard.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

EMPTY = "empty"
_ERROR = "error:"
# Count fields that mean "nothing found" when zero, e.g. Claude Code Grep and Glob.
_COUNT_KEYS = ("numFiles", "numLines", "numMatches", "count", "total", "total_count")
# Result payload fields. Bash's stdout is left out on purpose: a quiet success is progress.
_RESULT_KEYS = ("results", "matches", "filenames", "files", "items", "content", "output", "result")
_EMPTY_TEXT = {"", "[]", "{}", "none", "null", "no matches found", "no files found",
               "no results found"}
_DIGITS = re.compile(r"\d+")
_MIN_ARG_LEN = 3
_MAX_OUTCOME_LEN = 200


def stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str)


def _text(value: str) -> str:
    return " ".join(value.split()).casefold()


def normalize_args(value: Any) -> Any:
    """Canonicalize containers without changing meaningful argument values.

    Case and whitespace can select different files or alter code and shell
    literals. They must remain exact even when normalization is requested.
    Key order is handled by stable_json.
    """
    if isinstance(value, dict):
        return {str(k): normalize_args(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize_args(v) for v in value]
    return value


def is_empty_result(value: Any) -> bool:
    """True for a result that found nothing. Unknown shapes count as progress."""
    if value is None:
        return True
    if isinstance(value, str):
        return _text(value) in _EMPTY_TEXT
    if isinstance(value, (list, tuple, set)):
        return not value
    if not isinstance(value, dict):
        return False
    if not value:
        return True
    counts = [value[k] for k in _COUNT_KEYS
              if isinstance(value.get(k), int) and not isinstance(value.get(k), bool)]
    if counts:
        return all(c == 0 for c in counts)
    found = [value[k] for k in _RESULT_KEYS if k in value]
    return bool(found) and all(is_empty_result(v) for v in found)


def _arg_strings(args: Any) -> List[str]:
    out: List[str] = []
    if isinstance(args, str):
        # Errors quote pieces of a command ("cat: a.log: no such file"), so mask tokens too.
        text = _text(args)
        out.append(text)
        out.extend(text.split(" "))
    elif isinstance(args, dict):
        for v in args.values():
            out.extend(_arg_strings(v))
    elif isinstance(args, (list, tuple)):
        for v in args:
            out.extend(_arg_strings(v))
    return out


def outcome_of(result: Any = None, error: Any = None, args: Any = None) -> Optional[str]:
    """Return ``"empty"``, ``"error:<normalized message>"``, or None for progress.

    Error text is folded like arguments, the call's own argument strings are
    masked, and digits collapse, so "no file a.py" and "no file b.py" from two
    reworded calls match.
    """
    if error is None:
        return EMPTY if is_empty_result(result) else None
    if isinstance(error, BaseException):
        error = f"{type(error).__name__}: {error}"
    text = _text(str(error))
    for arg in sorted(set(_arg_strings(args)), key=len, reverse=True):
        if len(arg) >= _MIN_ARG_LEN:
            text = text.replace(arg, "<arg>")
    return _ERROR + _DIGITS.sub("#", text)[:_MAX_OUTCOME_LEN]


def describe_outcome(outcome: str) -> str:
    return "came back empty" if outcome == EMPTY else "failed with the same error"


def advance_streak(streak: Optional[Dict[str, Any]], tool_name: str,
                   outcome: Optional[str]) -> Optional[Dict[str, Any]]:
    """Update the run of consecutive results from one tool with one outcome.

    Any progress, another tool, or a different outcome starts over.
    """
    if outcome is None:
        return None
    if streak and streak.get("tool") == tool_name and streak.get("outcome") == outcome:
        return {**streak, "count": streak.get("count", 0) + 1}
    return {"tool": tool_name, "outcome": outcome, "count": 1}
