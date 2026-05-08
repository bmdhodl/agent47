"""Tests for the typed-contracts public schemas (agentguard.schemas)."""
from __future__ import annotations

import pytest

import agentguard
from agentguard import SUPPORTED_PROFILES, InitConfig, ProfileDefaults, RepoConfig


class TestSchemaExports:
    def test_schemas_importable_from_package_root(self) -> None:
        # The four typed contracts must be reachable via the top-level import.
        assert agentguard.InitConfig is InitConfig
        assert agentguard.RepoConfig is RepoConfig
        assert agentguard.ProfileDefaults is ProfileDefaults
        assert agentguard.SUPPORTED_PROFILES == SUPPORTED_PROFILES

    def test_supported_profiles_matches_runtime(self) -> None:
        # Schema constant must stay in sync with profiles.py.
        from agentguard.profiles import _PROFILE_DEFAULTS

        assert set(SUPPORTED_PROFILES) == set(_PROFILE_DEFAULTS.keys())


class TestInitConfig:
    def test_defaults_validate(self) -> None:
        InitConfig().validate()  # should not raise

    def test_valid_full_config(self) -> None:
        cfg = InitConfig(
            api_key="ag_abc",
            budget_usd=5.0,
            service="my-agent",
            profile="coding-agent",
            warn_pct=0.5,
            loop_max=3,
            retry_max=2,
        )
        cfg.validate()

    def test_warn_pct_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="warn_pct"):
            InitConfig(warn_pct=1.5).validate()

    def test_local_only_with_api_key_rejected(self) -> None:
        with pytest.raises(ValueError, match="local_only"):
            InitConfig(api_key="ag_x", local_only=True).validate()

    def test_api_key_with_newline_rejected(self) -> None:
        with pytest.raises(ValueError, match="newline"):
            InitConfig(api_key="ag_x\nInjected: header").validate()

    def test_negative_budget_rejected(self) -> None:
        with pytest.raises(ValueError, match="budget_usd"):
            InitConfig(budget_usd=-1.0).validate()

    def test_unknown_profile_rejected(self) -> None:
        with pytest.raises(ValueError, match="Unknown AgentGuard profile"):
            InitConfig(profile="not-a-real-profile").validate()

    def test_zero_loop_max_rejected(self) -> None:
        with pytest.raises(ValueError, match="loop_max"):
            InitConfig(loop_max=0).validate()

    def test_negative_retry_max_rejected(self) -> None:
        with pytest.raises(ValueError, match="retry_max"):
            InitConfig(retry_max=-1).validate()

    def test_empty_string_service_rejected(self) -> None:
        with pytest.raises(ValueError, match="service"):
            InitConfig(service="   ").validate()

    def test_to_dict_roundtrips_through_init_signature(self) -> None:
        # The dict produced by to_dict() must be acceptable kwargs for init.
        # We verify by introspection rather than calling init (no global state mutation).
        import inspect

        from agentguard.setup import init

        cfg = InitConfig(budget_usd=1.0, profile="default", auto_patch=False)
        sig = inspect.signature(init)
        accepted = set(sig.parameters.keys())
        for key in cfg.to_dict():
            assert key in accepted, f"InitConfig field {key!r} not accepted by init()"


class TestRepoConfig:
    def test_defaults_validate(self) -> None:
        RepoConfig().validate()

    def test_valid_full_config(self) -> None:
        RepoConfig(
            service="svc",
            trace_file="traces.jsonl",
            budget_usd=10.0,
            profile="deployed-agent",
            warn_pct=0.5,
            loop_max=2,
            retry_max=1,
        ).validate()

    def test_to_dict_omits_unset_fields(self) -> None:
        cfg = RepoConfig(service="svc", budget_usd=2.5)
        assert cfg.to_dict() == {"service": "svc", "budget_usd": 2.5}

    def test_negative_budget_rejected(self) -> None:
        with pytest.raises(ValueError, match="budget_usd"):
            RepoConfig(budget_usd=-0.01).validate()

    def test_unknown_profile_rejected(self) -> None:
        with pytest.raises(ValueError, match="Unknown AgentGuard profile"):
            RepoConfig(profile="bogus").validate()

    def test_warn_pct_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="warn_pct"):
            RepoConfig(warn_pct=2.0).validate()


class TestProfileDefaults:
    def test_valid(self) -> None:
        ProfileDefaults(loop_max=5, warn_pct=0.8, retry_max=None).validate()
        ProfileDefaults(loop_max=2, warn_pct=0.5, retry_max=1).validate()

    def test_zero_loop_max_rejected(self) -> None:
        with pytest.raises(ValueError, match="loop_max"):
            ProfileDefaults(loop_max=0, warn_pct=0.8).validate()

    def test_warn_pct_out_of_range_rejected(self) -> None:
        with pytest.raises(ValueError, match="warn_pct"):
            ProfileDefaults(loop_max=3, warn_pct=-0.1).validate()

    def test_negative_retry_max_rejected(self) -> None:
        with pytest.raises(ValueError, match="retry_max"):
            ProfileDefaults(loop_max=3, warn_pct=0.8, retry_max=-1).validate()

    def test_matches_runtime_profile_defaults(self) -> None:
        # Every built-in profile dict must be representable as a ProfileDefaults
        # instance that validates cleanly.
        from agentguard.profiles import get_profile_defaults

        for name in SUPPORTED_PROFILES:
            d = get_profile_defaults(name)
            schema = ProfileDefaults(
                loop_max=d["loop_max"],
                warn_pct=d["warn_pct"],
                retry_max=d.get("retry_max"),
            )
            schema.validate()
