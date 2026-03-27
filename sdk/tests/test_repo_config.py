from __future__ import annotations

import json
import os
import tempfile

import pytest

from agentguard.repo_config import find_repo_config, load_repo_config


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
