"""Architectural invariant tests — mechanical enforcement of SDK golden principles.

These tests enforce the structural rules defined in GOLDEN_PRINCIPLES.md.
Each assertion message includes remediation instructions so agents and
developers can self-correct on failure.

Run with: pytest sdk/tests/test_architecture.py -v
"""
import ast
import inspect
import re
import sys
from pathlib import Path

import pytest

import agentguard
from agentguard.tracing import TraceSink

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SDK_ROOT = Path(__file__).parent.parent / "agentguard"

# Core modules — must use stdlib only (no third-party imports at module level)
CORE_MODULES = [
    "__init__.py",
    "atracing.py",
    "cli.py",
    "cost.py",
    "evaluation.py",
    "export.py",
    "guards.py",
    "instrument.py",
    "setup.py",
    "tracing.py",
    "sinks/http.py",
]

# Integration modules — allowed to import third-party packages
INTEGRATION_MODULES = [
    "sinks/__init__.py",
    "sinks/otel.py",
    "integrations/__init__.py",
    "integrations/langchain.py",
    "integrations/langgraph.py",
    "integrations/crewai.py",
]

# Known thread-safe classes (have mutable state, must have _lock)
THREAD_SAFE_CLASSES = [
    "LoopGuard",
    "FuzzyLoopGuard",
    "BudgetGuard",
    "RateLimitGuard",
    "JsonlFileSink",
    "HttpSink",
]

MAX_MODULE_LINES = 800

# Python stdlib module names — sys.stdlib_module_names requires 3.10+
if hasattr(sys, "stdlib_module_names"):
    _STDLIB = {m.split(".")[0] for m in sys.stdlib_module_names}
else:
    # Fallback for Python 3.9
    _STDLIB = {
        "abc", "aifc", "argparse", "array", "ast", "asynchat", "asyncio",
        "asyncore", "atexit", "audioop", "base64", "bdb", "binascii",
        "binhex", "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb",
        "chunk", "cmath", "cmd", "code", "codecs", "codeop", "collections",
        "colorsys", "compileall", "concurrent", "configparser", "contextlib",
        "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
        "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal",
        "difflib", "dis", "distutils", "doctest", "email", "encodings",
        "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput",
        "fnmatch", "formatter", "fractions", "ftplib", "functools", "gc",
        "getopt", "getpass", "gettext", "glob", "grp", "gzip", "hashlib",
        "heapq", "hmac", "html", "http", "idlelib", "imaplib", "imghdr",
        "imp", "importlib", "inspect", "io", "ipaddress", "itertools",
        "json", "keyword", "lib2to3", "linecache", "locale", "logging",
        "lzma", "mailbox", "mailcap", "marshal", "math", "mimetypes",
        "mmap", "modulefinder", "multiprocessing", "netrc", "nis", "nntplib",
        "numbers", "operator", "optparse", "os", "ossaudiodev", "parser",
        "pathlib", "pdb", "pickle", "pickletools", "pipes", "pkgutil",
        "platform", "plistlib", "poplib", "posix", "posixpath", "pprint",
        "profile", "pstats", "pty", "pwd", "py_compile", "pyclbr",
        "pydoc", "queue", "quopri", "random", "re", "readline", "reprlib",
        "resource", "rlcompleter", "runpy", "sched", "secrets", "select",
        "selectors", "shelve", "shlex", "shutil", "signal", "site",
        "smtpd", "smtplib", "sndhdr", "socket", "socketserver", "spwd",
        "sqlite3", "sre_compile", "sre_constants", "sre_parse", "ssl",
        "stat", "statistics", "string", "stringprep", "struct", "subprocess",
        "sunau", "symtable", "sys", "sysconfig", "syslog", "tabnanny",
        "tarfile", "telnetlib", "tempfile", "termios", "test", "textwrap",
        "threading", "time", "timeit", "tkinter", "token", "tokenize",
        "trace", "traceback", "tracemalloc", "tty", "turtle", "turtledemo",
        "types", "typing", "unicodedata", "unittest", "urllib", "uu",
        "uuid", "venv", "warnings", "wave", "weakref", "webbrowser",
        "winreg", "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc",
        "zipapp", "zipfile", "zipimport", "zlib",
        # Python internal / special
        "_thread", "__future__", "_collections_abc", "_typeshed",
        "typing_extensions",
    }

ALLOWED_IMPORT_PREFIXES = _STDLIB | {"agentguard"}


def _is_inside_try_or_function(node: ast.AST, tree: ast.Module) -> bool:
    """Check if a node is inside a try/except block or function body."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            if child is node:
                if isinstance(parent, (ast.Try, ast.FunctionDef, ast.AsyncFunctionDef)):
                    return True
    # Walk more carefully with parent tracking
    return _walk_with_parents(tree, node)


def _walk_with_parents(tree: ast.Module, target: ast.AST) -> bool:
    """Walk AST tracking parents to check if target is inside try/function."""
    stack = [(tree, None)]
    while stack:
        current, parent = stack.pop()
        if current is target:
            # Walk up through ancestors
            ancestor = parent
            while ancestor is not None:
                if isinstance(ancestor, (ast.Try, ast.FunctionDef, ast.AsyncFunctionDef)):
                    return True
                # Need to find ancestor's parent — re-walk
                ancestor = _find_parent(tree, ancestor)
            return False
        for child in ast.iter_child_nodes(current):
            stack.append((child, current))
    return False


def _find_parent(tree: ast.Module, target: ast.AST) -> ast.AST:
    """Find the parent node of target in the AST."""
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            if child is target:
                return parent
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.structural
class TestArchitecturalInvariants:

    def test_core_modules_stdlib_only(self):
        """Core modules must not import third-party packages at module level.

        Golden Principle #1: Zero dependencies in core.
        """
        violations = []

        for rel_path in CORE_MODULES:
            filepath = SDK_ROOT / rel_path
            if not filepath.exists():
                continue
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        if top not in ALLOWED_IMPORT_PREFIXES:
                            if not _is_inside_try_or_function(node, tree):
                                violations.append(
                                    f"{rel_path}:{node.lineno} imports '{alias.name}'"
                                )
                elif isinstance(node, ast.ImportFrom):
                    # Skip relative imports (from . or from .foo)
                    if node.level > 0:
                        continue
                    if node.module:
                        top = node.module.split(".")[0]
                        if top not in ALLOWED_IMPORT_PREFIXES:
                            if not _is_inside_try_or_function(node, tree):
                                violations.append(
                                    f"{rel_path}:{node.lineno} imports from '{node.module}'"
                                )

        assert not violations, (
            "Core module stdlib-only rule violated:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: Move third-party imports inside try/except ImportError blocks "
            "or into integration modules (integrations/, sinks/otel.py)."
        )

    def test_core_does_not_import_integrations(self):
        """Core modules must not import from integrations/ or sinks/otel.py.

        Golden Principle #2: One-way import direction.
        """
        violations = []
        forbidden = {"agentguard.integrations", "agentguard.sinks.otel"}

        for rel_path in CORE_MODULES:
            filepath = SDK_ROOT / rel_path
            if not filepath.exists():
                continue
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=rel_path)

            for node in ast.walk(tree):
                module_name = ""
                if isinstance(node, ast.ImportFrom) and node.module:
                    module_name = node.module
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name

                for prefix in forbidden:
                    if module_name.startswith(prefix):
                        violations.append(
                            f"{rel_path}:{node.lineno} imports '{module_name}'"
                        )

        assert not violations, (
            "Core module imports from integrations (forbidden):\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: Core modules must never depend on integrations/ or sinks/otel.py. "
            "Dependency flows one way: integrations -> core."
        )

    def test_no_module_exceeds_line_limit(self):
        """No single SDK module should exceed 800 lines.

        Golden Principle #7: Module size limit.
        """
        violations = []

        for py_file in SDK_ROOT.rglob("*.py"):
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            if line_count > MAX_MODULE_LINES:
                rel = py_file.relative_to(SDK_ROOT)
                violations.append(f"{rel}: {line_count} lines (max: {MAX_MODULE_LINES})")

        assert not violations, (
            f"Files exceeding {MAX_MODULE_LINES} line limit:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: Split large modules into focused submodules."
        )

    def test_all_public_exports_have_docstrings(self):
        """Every class/function in __all__ must have a docstring.

        Golden Principle #8: Every public symbol has a docstring.
        """
        missing = []
        for name in agentguard.__all__:
            if name == "__version__":
                continue
            obj = getattr(agentguard, name)
            if inspect.isclass(obj) or inspect.isfunction(obj):
                if not obj.__doc__:
                    missing.append(name)

        assert not missing, (
            "Public API items missing docstrings:\n"
            + "\n".join(f"  - {name}" for name in missing)
            + "\n\nFix: Add a docstring to each listed class/function."
        )

    def test_public_naming_conventions(self):
        """Classes must be PascalCase, functions must be snake_case.

        Golden Principle #10: Naming conventions.
        """
        violations = []
        for name in agentguard.__all__:
            if name.startswith("_"):
                continue
            obj = getattr(agentguard, name)
            if inspect.isclass(obj):
                if not re.match(r"^[A-Z][a-zA-Z0-9]+$", name):
                    violations.append(f"Class '{name}' is not PascalCase")
            elif inspect.isfunction(obj):
                if not re.match(r"^[a-z][a-z0-9_]*$", name):
                    violations.append(f"Function '{name}' is not snake_case")

        assert not violations, (
            "Naming convention violations:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: Rename to follow PascalCase (classes) or snake_case (functions)."
        )

    def test_no_hardcoded_absolute_paths(self):
        """No Python file should contain hardcoded absolute filesystem paths.

        Golden Principle #9: No hardcoded absolute paths.
        """
        violations = []
        pattern = re.compile(r"""['"](/Users/|/home/|/var/|C:\\)""")

        for py_file in SDK_ROOT.rglob("*.py"):
            for i, line in enumerate(py_file.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line):
                    rel = py_file.relative_to(SDK_ROOT)
                    violations.append(f"{rel}:{i}: {line.strip()}")

        assert not violations, (
            "Hardcoded absolute paths found:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: Use relative paths or environment variables."
        )

    def test_thread_safe_classes_have_lock(self):
        """Classes with mutable shared state must have a _lock attribute.

        Golden Principle #6: Thread-safe mutable state requires Lock.
        """
        missing = []
        for class_name in THREAD_SAFE_CLASSES:
            cls = getattr(agentguard, class_name, None)
            if cls is None:
                continue
            source = inspect.getsource(cls)
            if "_lock" not in source:
                missing.append(class_name)

        assert not missing, (
            "Thread-safe classes missing _lock:\n"
            + "\n".join(f"  - {name}" for name in missing)
            + "\n\nFix: Add `self._lock = threading.Lock()` in __init__ and "
            "wrap all mutations with `with self._lock:`."
        )

    def test_guard_check_methods_raise_not_return(self):
        """Guard check() and auto_check() must raise exceptions, not return booleans.

        Golden Principle #4: Guards raise exceptions.
        """
        from agentguard import guards

        violations = []
        for name in dir(guards):
            cls = getattr(guards, name)
            if not inspect.isclass(cls):
                continue
            if not issubclass(cls, guards.BaseGuard) or cls is guards.BaseGuard:
                continue

            for method_name in ("check", "auto_check"):
                method = getattr(cls, method_name, None)
                if method is None:
                    continue
                # Skip inherited no-op from BaseGuard
                if method is getattr(guards.BaseGuard, method_name, None):
                    continue
                source = inspect.getsource(method)
                if "return True" in source or "return False" in source:
                    violations.append(
                        f"{name}.{method_name}() returns a boolean"
                    )

        assert not violations, (
            "Guards must raise exceptions, not return booleans:\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nFix: Replace `return True/False` with raising "
            "LoopDetected, BudgetExceeded, or TimeoutExceeded."
        )

    def test_all_sinks_implement_emit(self):
        """All TraceSink subclasses must implement emit().

        Golden Principle #5: TraceSink interface.
        """
        missing = []
        for cls in TraceSink.__subclasses__():
            if "emit" not in cls.__dict__:
                missing.append(cls.__name__)

        assert not missing, (
            "TraceSink subclasses missing emit():\n"
            + "\n".join(f"  - {name}" for name in missing)
            + "\n\nFix: Implement `def emit(self, event: Dict[str, Any]) -> None:` "
            "in each listed class."
        )
