# Definition of Done

## Every PR

- [ ] `make check` passes (pytest + ruff lint). Coverage >= 80%.
- [ ] New functionality has tests.
- [ ] No new hard dependencies in core SDK. Integration deps guarded by `try/except ImportError`.
- [ ] `make structural` passes (10 Golden Principles).
- [ ] `make security` passes (bandit scan).
- [ ] No hardcoded absolute paths.
- [ ] If `__init__.py` exports changed, it was intentional.

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
