"""Tests for v1.1.0 guard improvements: BaseGuard, auto_check, context managers."""
import time
import unittest

from agentguard.guards import (
    BaseGuard,
    BudgetGuard,
    FuzzyLoopGuard,
    LoopDetected,
    LoopGuard,
    RateLimitGuard,
    TimeoutExceeded,
    TimeoutGuard,
)


class TestBaseGuard(unittest.TestCase):
    """Test BaseGuard abstract class."""

    def test_auto_check_is_noop(self):
        guard = BaseGuard()
        # Should not raise
        guard.auto_check("tool.search", {"q": "test"})
        guard.auto_check("tool.search")

    def test_reset_is_noop(self):
        guard = BaseGuard()
        guard.reset()

    def test_subclass_can_override(self):
        class CountingGuard(BaseGuard):
            def __init__(self):
                self.count = 0

            def auto_check(self, event_name, event_data=None):
                self.count += 1

            def reset(self):
                self.count = 0

        guard = CountingGuard()
        guard.auto_check("tool.search")
        guard.auto_check("tool.search")
        self.assertEqual(guard.count, 2)
        guard.reset()
        self.assertEqual(guard.count, 0)

    def test_isinstance_checks(self):
        self.assertIsInstance(LoopGuard(), BaseGuard)
        self.assertIsInstance(BudgetGuard(max_calls=10), BaseGuard)
        self.assertIsInstance(TimeoutGuard(max_seconds=10), BaseGuard)
        self.assertIsInstance(FuzzyLoopGuard(), BaseGuard)
        self.assertIsInstance(RateLimitGuard(max_calls_per_minute=10), BaseGuard)


class TestLoopGuardAutoCheck(unittest.TestCase):
    """Test LoopGuard.auto_check delegates to check()."""

    def test_auto_check_triggers_loop_detection(self):
        guard = LoopGuard(max_repeats=2)
        guard.auto_check("tool.search", {"q": "test"})
        with self.assertRaises(LoopDetected):
            guard.auto_check("tool.search", {"q": "test"})

    def test_auto_check_different_names_ok(self):
        guard = LoopGuard(max_repeats=2)
        guard.auto_check("tool.search", {"q": "a"})
        guard.auto_check("tool.read", {"q": "b"})
        guard.auto_check("tool.search", {"q": "a"})
        # No exception — not consecutive


class TestFuzzyLoopGuardAutoCheck(unittest.TestCase):
    def test_auto_check_triggers_fuzzy_detection(self):
        guard = FuzzyLoopGuard(max_tool_repeats=3)
        guard.auto_check("tool.search", {"q": "a"})
        guard.auto_check("tool.search", {"q": "b"})
        with self.assertRaises(LoopDetected):
            guard.auto_check("tool.search", {"q": "c"})


class TestTimeoutGuardAutoCheck(unittest.TestCase):
    def test_auto_check_before_start_is_noop(self):
        guard = TimeoutGuard(max_seconds=10)
        # Should not raise since timer hasn't started
        guard.auto_check("tool.search")

    def test_auto_check_after_start(self):
        guard = TimeoutGuard(max_seconds=10)
        guard.start()
        # Should not raise — well within limit
        guard.auto_check("tool.search")


class TestRateLimitGuardAutoCheck(unittest.TestCase):
    def test_auto_check_delegates(self):
        guard = RateLimitGuard(max_calls_per_minute=2)
        guard.auto_check("tool.a")
        guard.auto_check("tool.b")
        from agentguard.guards import BudgetExceeded
        with self.assertRaises(BudgetExceeded):
            guard.auto_check("tool.c")


class TestTimeoutGuardContextManager(unittest.TestCase):
    """Test TimeoutGuard as a context manager."""

    def test_context_manager_starts_timer(self):
        guard = TimeoutGuard(max_seconds=10)
        with guard:
            # Timer should be started, check should not raise
            guard.check()
        # Exited successfully

    def test_context_manager_raises_on_timeout(self):
        guard = TimeoutGuard(max_seconds=0.01)
        with self.assertRaises(TimeoutExceeded):
            with guard:
                time.sleep(0.05)
        # The __exit__ should have raised TimeoutExceeded

    def test_context_manager_no_check_if_exception(self):
        """If user code raises, __exit__ should NOT also check timeout."""
        guard = TimeoutGuard(max_seconds=0.01)
        with self.assertRaises(ValueError):
            with guard:
                time.sleep(0.05)
                raise ValueError("user error")
        # ValueError propagated, not TimeoutExceeded

    def test_context_manager_manual_check_inside(self):
        guard = TimeoutGuard(max_seconds=0.01)
        with self.assertRaises(TimeoutExceeded):
            with guard:
                time.sleep(0.05)
                guard.check()  # Manual check inside context

    def test_context_manager_returns_self(self):
        guard = TimeoutGuard(max_seconds=10)
        with guard as g:
            self.assertIs(g, guard)


class TestTracerAutoCheckDispatch(unittest.TestCase):
    """Test Tracer dispatches auto_check to guards."""

    def test_auto_check_called_on_events(self):
        from agentguard.tracing import Tracer

        class RecordingGuard(BaseGuard):
            def __init__(self):
                self.calls = []

            def auto_check(self, event_name, event_data=None):
                self.calls.append((event_name, event_data))

        guard = RecordingGuard()
        tracer = Tracer(guards=[guard])
        with tracer.trace("test") as ctx:
            ctx.event("tool.search", data={"q": "test"})
            ctx.event("tool.read")

        self.assertEqual(len(guard.calls), 2)
        self.assertEqual(guard.calls[0], ("tool.search", {"q": "test"}))
        self.assertEqual(guard.calls[1], ("tool.read", None))

    def test_backward_compat_check_dispatch(self):
        """Guards without auto_check but with check() still work."""
        from agentguard.tracing import Tracer

        class OldStyleGuard:
            def __init__(self):
                self.calls = []

            def check(self, name, data=None):
                self.calls.append(name)

        guard = OldStyleGuard()
        tracer = Tracer(guards=[guard])
        with tracer.trace("test") as ctx:
            ctx.event("tool.search")

        self.assertEqual(guard.calls, ["tool.search"])

    def test_backward_compat_no_args_check(self):
        """Guards with check() that takes no args still work."""
        from agentguard.tracing import Tracer

        class NoArgsGuard:
            def __init__(self):
                self.called = False

            def check(self):
                self.called = True

        guard = NoArgsGuard()
        tracer = Tracer(guards=[guard])
        with tracer.trace("test") as ctx:
            ctx.event("tool.search")

        self.assertTrue(guard.called)


if __name__ == "__main__":
    unittest.main()
