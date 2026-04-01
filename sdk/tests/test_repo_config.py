from __future__ import annotations

import json
import os
import tempfile

import pytest

from agentguard.repo_config import find_repo_config, load_repo_config, load_repo_config_safely


def test_find_repo_config_walks_upward() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, ".agentguard.json")
        nested_dir = os.path.join(tmpdir, "src", "agent")
        os.makedirs(nested_dir, exist_ok=True)
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump({"service": "repo-agent"}, handle)

        found = find_repo_config(nested_dir)

        assert found == config_path


def test_load_repo_config_resolves_relative_trace_path() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, ".agentguard.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "service": "repo-agent",
                    "trace_file": ".agentguard/traces.jsonl",
                    "budget_usd": 3.25,
                    "profile": "coding-agent",
                    "retry_max": 4,
                },
                handle,
            )

        path, config = load_repo_config(tmpdir)

        assert path == config_path
        assert config["service"] == "repo-agent"
        assert config["trace_file"] == os.path.join(
            tmpdir,
            ".agentguard",
            "traces.jsonl",
        )
        assert config["budget_usd"] == 3.25
        assert config["profile"] == "coding-agent"
        assert config["retry_max"] == 4


def test_load_repo_config_ignores_unknown_keys() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, ".agentguard.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "service": "repo-agent",
                    "api_key": "ag_not_allowed",
                    "dashboard_url": "https://example.com",
                },
                handle,
            )

        _, config = load_repo_config(tmpdir)

        assert config == {"service": "repo-agent"}


def test_load_repo_config_rejects_invalid_service() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, ".agentguard.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump({"service": ""}, handle)

        with pytest.raises(ValueError, match="service"):
            load_repo_config(tmpdir)


def test_load_repo_config_rejects_invalid_top_level_shape() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, ".agentguard.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(["not", "an", "object"], handle)

        with pytest.raises(ValueError, match="JSON object"):
            load_repo_config(tmpdir)


def test_load_repo_config_includes_path_in_json_errors() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, ".agentguard.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            handle.write("{invalid json")

        with pytest.raises(ValueError, match=config_path.replace("\\", r"\\").replace(".", r"\.")):
            load_repo_config(tmpdir)


def test_load_repo_config_rejects_invalid_profile() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, ".agentguard.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump({"profile": "spaceship"}, handle)

        with pytest.raises(ValueError, match="Unknown AgentGuard profile"):
            load_repo_config(tmpdir)


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"budget_usd": True}, "budget_usd"),
        ({"warn_pct": False}, "warn_pct"),
        ({"loop_max": True}, "loop_max"),
        ({"retry_max": False}, "retry_max"),
    ],
)
def test_load_repo_config_rejects_boolean_numerics(
    payload: dict[str, object],
    message: str,
) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, ".agentguard.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

        with pytest.raises(ValueError, match=message):
            load_repo_config(tmpdir)


def test_load_repo_config_safely_returns_error_string() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, ".agentguard.json")
        with open(config_path, "w", encoding="utf-8") as handle:
            handle.write("{bad json")

        path, config, error = load_repo_config_safely(tmpdir)

        assert path == config_path
        assert config == {}
        assert error is not None
