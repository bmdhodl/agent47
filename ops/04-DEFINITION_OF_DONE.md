# Definition of Done

## Every PR

- [ ] `make check` passes (pytest + ruff lint). Coverage >= 80%. If `make` is unavailable, run the equivalent direct commands.
- [ ] New functionality has tests.
- [ ] No new hard dependencies in core SDK. Integration deps guarded by `try/except ImportError`.
- [ ] `make structural` passes (10 Golden Principles).
- [ ] `make security` passes (bandit scan).
- [ ] Test runs are clean - no persistent pytest config warnings.
- [ ] No hardcoded absolute paths.
- [ ] If `__init__.py` exports changed, it was intentional.
- [ ] If the change ships user-visible behavior or release prep, docs and roadmap were reviewed for drift.

## Cutting a release

- [ ] `make release-guard` passes (version markers, changelog section, and generated PyPI README are aligned).
- [ ] If `HttpSink`, tracing, or the hosted-ingest contract changed, run `sdk/tests/integration_dashboard.py` with a real API key and keep proof of a trace-id-scoped `/api/v1/traces?trace_id=...` lookup from this release candidate.
- [ ] `sdk/pyproject.toml` version matches the intended tag.
- [ ] `CHANGELOG.md` has an entry for the version being shipped.
- [ ] `sdk/PYPI_README.md` is regenerated from `README.md` + `CHANGELOG.md` and matches the release tag.
- [ ] GitHub Releases has an entry for the tag, not just a git tag.
- [ ] PyPI version matches the Git tag after publish.
- [ ] Release notes link to the correct docs, repo, and package name.

## Adding a new guard

- [ ] Inherits `BaseGuard`.
- [ ] `check()` raises an exception (never returns bool).
- [ ] Has `auto_check(event_name, event_data)` for Tracer integration.
- [ ] Thread-safe: `self._lock = threading.Lock()` on mutable state.
- [ ] Exported from `__init__.py`, added to `__all__`.
- [ ] Added to `THREAD_SAFE_CLASSES` in `test_architecture.py`.

## Adding a new sink

- [ ] Inherits `TraceSink`.
- [ ] Implements `emit(event: Dict[str, Any]) -> None`.
- [ ] Optional deps guarded with `try/except ImportError`.
- [ ] Exported from `sinks/__init__.py` and `agentguard/__init__.py`.

## Adding a new integration

- [ ] Third-party imports guarded with `try/except ImportError`.
- [ ] Imports core modules only (never the reverse).
- [ ] Optional dep added to `pyproject.toml [project.optional-dependencies]`.
