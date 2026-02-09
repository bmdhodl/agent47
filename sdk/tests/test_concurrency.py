"""Thread safety tests for guards and sinks."""
import os
import tempfile
import threading
import time
import unittest

from agentguard.guards import (
    BudgetExceeded,
    BudgetGuard,
    LoopDetected,
    LoopGuard,
    RateLimitGuard,
)
from agentguard.tracing import JsonlFileSink


class TestBudgetGuardThreadSafety(unittest.TestCase):
    """Verify BudgetGuard.consume() is thread-safe."""

    def test_concurrent_consume_tokens(self):
        guard = BudgetGuard(max_tokens=100_000)
        barrier = threading.Barrier(10)

        def consume():
            barrier.wait()
            for _ in range(100):
                guard.consume(tokens=10)

        threads = [threading.Thread(target=consume) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 10 threads * 100 iterations * 10 tokens = 10,000
        self.assertEqual(guard.state.tokens_used, 10_000)

    def test_concurrent_consume_cost(self):
        guard = BudgetGuard(max_cost_usd=1000.0)
        barrier = threading.Barrier(10)

        def consume():
            barrier.wait()
            for _ in range(100):
                guard.consume(cost_usd=0.01)

        threads = [threading.Thread(target=consume) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 10 * 100 * 0.01 = 10.00
        self.assertAlmostEqual(guard.state.cost_used, 10.0, places=2)

    def test_concurrent_consume_with_budget_exceeded(self):
        guard = BudgetGuard(max_tokens=500)
        exceeded_count = 0
        lock = threading.Lock()

        def consume():
            nonlocal exceeded_count
            for _ in range(100):
                try:
                    guard.consume(tokens=1)
                except BudgetExceeded:
                    with lock:
                        exceeded_count += 1

        threads = [threading.Thread(target=consume) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Total attempts: 1000, max: 500 → some should exceed
        self.assertGreater(exceeded_count, 0)
        # Total consumed should equal 500 (the excess) + exceeded count
        self.assertGreaterEqual(guard.state.tokens_used, 500)

    def test_concurrent_reset(self):
        guard = BudgetGuard(max_tokens=100_000)

        def consume_and_reset():
            for _ in range(50):
                guard.consume(tokens=1)
            guard.reset()

        threads = [threading.Thread(target=consume_and_reset) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # After all resets, state should be clean
        # (or partially consumed if a consume happened after a reset)
        # The key assertion: no crash, no exception


class TestRateLimitGuardThreadSafety(unittest.TestCase):
    """Verify RateLimitGuard.check() is thread-safe."""

    def test_concurrent_check(self):
        guard = RateLimitGuard(max_calls_per_minute=500)
        success_count = 0
        exceeded_count = 0
        lock = threading.Lock()
        barrier = threading.Barrier(10)

        def check():
            nonlocal success_count, exceeded_count
            barrier.wait()
            for _ in range(100):
                try:
                    guard.check()
                    with lock:
                        success_count += 1
                except BudgetExceeded:
                    with lock:
                        exceeded_count += 1

        threads = [threading.Thread(target=check) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Total attempts: 1000, max: 500
        self.assertEqual(success_count + exceeded_count, 1000)
        self.assertEqual(success_count, 500)
        self.assertEqual(exceeded_count, 500)

    def test_concurrent_reset(self):
        guard = RateLimitGuard(max_calls_per_minute=100)

        def check_and_reset():
            for _ in range(20):
                try:
                    guard.check()
                except BudgetExceeded:
                    pass
            guard.reset()

        threads = [threading.Thread(target=check_and_reset) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # No crash — that's the key assertion


class TestJsonlFileSinkThreadSafety(unittest.TestCase):
    """Verify JsonlFileSink writes correctly under concurrent access."""

    def test_concurrent_writes(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            sink = JsonlFileSink(path)
            barrier = threading.Barrier(10)

            def emit_events():
                barrier.wait()
                for i in range(100):
                    sink.emit({"thread": threading.current_thread().name, "i": i})

            threads = [threading.Thread(target=emit_events) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            # Read back and verify
            import json

            with open(path, "r") as f:
                lines = [l.strip() for l in f if l.strip()]

            # 10 threads * 100 events = 1000 lines
            self.assertEqual(len(lines), 1000)

            # Every line should be valid JSON
            for line in lines:
                json.loads(line)
        finally:
            os.unlink(path)


class TestLoopGuardThreadSafety(unittest.TestCase):
    """LoopGuard doesn't use a lock, but should not crash under threads."""

    def test_concurrent_checks_no_crash(self):
        guard = LoopGuard(max_repeats=5, window=20)
        barrier = threading.Barrier(5)

        def check_various():
            barrier.wait()
            for i in range(50):
                try:
                    guard.check(f"tool_{i % 10}", {"i": i})
                except LoopDetected:
                    pass

        threads = [threading.Thread(target=check_various) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # No crash


if __name__ == "__main__":
    unittest.main()
