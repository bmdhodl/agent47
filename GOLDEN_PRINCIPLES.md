# Golden Principles

Mechanical rules enforced by structural tests in `sdk/tests/test_architecture.py`.
Violations fail CI. Each rule maps to the test that enforces it.

## 1. Zero Dependencies in Core

Core SDK modules use Python stdlib only. No `pip install` required.

- **Enforced by:** `test_core_modules_stdlib_only`
- **Allowed:** Optional deps (langchain, otel, crewai) in `integrations/` and `sinks/otel.py`, guarded by `try/except ImportError`.
- **Why:** The SDK is the acquisition funnel. Zero-dep means zero friction.

## 2. One-Way Import Direction

`integrations/` and `sinks/otel.py` may import from core modules.
Core modules must never import from `integrations/` or `sinks/otel.py`.

- **Enforced by:** `test_core_does_not_import_integrations`
- **Why:** Prevents circular deps and keeps the core self-contained.

## 3. Public API Through \_\_init\_\_.py

All user-facing classes and functions are exported from `sdk/agentguard/__init__.py` via `__all__`.
Users should never need to import from submodules.

- **Enforced by:** `test_all_list_complete` (in `test_exports.py`)
- **Why:** Stable import paths. Refactoring internals doesn't break users.

## 4. Guards Raise Exceptions

Guards signal violations by raising specific exceptions:
- `LoopDetected` (LoopGuard, FuzzyLoopGuard)
- `BudgetExceeded` (BudgetGuard)
- `TimeoutExceeded` (TimeoutGuard)

Never return booleans from `check()` or `auto_check()`.

- **Enforced by:** `test_guard_check_methods_raise_not_return`
- **Why:** Exception-based control flow is explicit, composable, and unambiguous.

## 5. TraceSink Interface

All sinks implement `emit(event: Dict[str, Any]) -> None`.
Subclass `TraceSink` and override `emit()`.

- **Enforced by:** `test_all_sinks_implement_emit`
- **Why:** Uniform interface enables pluggable backends.

## 6. Thread-Safe Mutable State

Any class with mutable instance state that may be shared across threads
must have a `_lock = threading.Lock()` attribute and use it for all mutations.

Known thread-safe classes: LoopGuard, FuzzyLoopGuard, BudgetGuard,
RateLimitGuard, JsonlFileSink, HttpSink, CostTracker.

- **Enforced by:** `test_thread_safe_classes_have_lock`
- **Why:** SDK users run agents concurrently. Data races are silent and deadly.

## 7. Module Size Limit

No single module exceeds 800 lines. Split large modules into focused submodules.

- **Enforced by:** `test_no_module_exceeds_line_limit`
- **Why:** Large files are hard for agents and humans to navigate and reason about.

## 8. Every Public Symbol Has a Docstring

All classes and functions in `__all__` must have a docstring.

- **Enforced by:** `test_all_public_exports_have_docstrings`
- **Why:** Docstrings are the primary documentation for both humans and agents.

## 9. No Hardcoded Absolute Paths

No `.py` file in the SDK may contain hardcoded absolute filesystem paths.

- **Enforced by:** `test_no_hardcoded_absolute_paths`
- **Why:** Hardcoded paths break portability.

## 10. Naming Conventions

- Public classes: PascalCase
- Public functions: snake_case
- Private attributes: _prefixed

- **Enforced by:** `test_public_naming_conventions`
- **Why:** Consistency for agent code generation. No guessing.
