import json
import os
import tempfile
import unittest

from agentguard.savings import normalize_usage, summarize_savings


def _write_trace(events):
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        for event in events:
            f.write(json.dumps(event) + "\n")
    return path


class TestNormalizeUsage(unittest.TestCase):
    def test_normalizes_openai_usage_with_cache_details(self):
        normalized = normalize_usage(
            {
                "prompt_tokens": 1000,
                "completion_tokens": 200,
                "total_tokens": 1200,
                "prompt_tokens_details": {"cached_tokens": 800},
                "completion_tokens_details": {"reasoning_tokens": 50},
            },
            provider="openai",
        )

        self.assertEqual(
            normalized,
            {
                "input_tokens": 1000,
                "output_tokens": 200,
                "total_tokens": 1200,
                "prompt_tokens": 1000,
                "completion_tokens": 200,
                "cached_input_tokens": 800,
                "reasoning_tokens": 50,
            },
        )

    def test_normalizes_anthropic_usage_with_cache_fields(self):
        normalized = normalize_usage(
            {
                "input_tokens": 300,
                "output_tokens": 40,
                "cache_read_input_tokens": 200,
                "cache_creation_input_tokens": 100,
            },
            provider="anthropic",
        )

        self.assertEqual(
            normalized,
            {
                "input_tokens": 300,
                "output_tokens": 40,
                "total_tokens": 640,
                "cached_input_tokens": 200,
                "cache_read_input_tokens": 200,
                "cache_write_input_tokens": 100,
                "cache_creation_input_tokens": 100,
            },
        )

    def test_returns_none_for_missing_usage_shape(self):
        self.assertIsNone(normalize_usage({"foo": "bar"}))


class TestSummarizeSavings(unittest.TestCase):
    def test_reports_exact_openai_cache_savings(self):
        savings = summarize_savings(
            [
                {
                    "name": "llm.result",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {
                        "model": "gpt-4o",
                        "provider": "openai",
                        "usage": {
                            "prompt_tokens": 1000,
                            "completion_tokens": 200,
                            "total_tokens": 1200,
                            "prompt_tokens_details": {"cached_tokens": 800},
                        },
                    },
                }
            ]
        )

        self.assertEqual(savings["exact_tokens_saved"], 800)
        self.assertEqual(savings["estimated_tokens_saved"], 0)
        self.assertAlmostEqual(savings["exact_usd_saved"], 0.0010, places=4)
        self.assertAlmostEqual(savings["estimated_usd_saved"], 0.0, places=4)
        self.assertEqual(
            savings["reasons"],
            [
                {
                    "kind": "provider_prompt_cache_hit",
                    "confidence": "exact",
                    "occurrences": 1,
                    "tokens_saved": 800,
                    "usd_saved": 0.001,
                }
            ],
        )

    def test_reports_exact_anthropic_cache_savings(self):
        savings = summarize_savings(
            [
                {
                    "name": "llm.result",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {
                        "model": "claude-sonnet-4-20250514",
                        "provider": "anthropic",
                        "usage": {
                            "input_tokens": 300,
                            "output_tokens": 40,
                            "cache_read_input_tokens": 100,
                        },
                    },
                }
            ]
        )

        self.assertEqual(savings["exact_tokens_saved"], 100)
        self.assertAlmostEqual(savings["exact_usd_saved"], 0.0003, places=4)

    def test_reports_estimated_loop_savings_once_per_trace(self):
        savings = summarize_savings(
            [
                {
                    "name": "llm.result",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {
                        "model": "gpt-4o",
                        "provider": "openai",
                        "usage": {
                            "prompt_tokens": 1000,
                            "completion_tokens": 500,
                            "total_tokens": 1500,
                        },
                    },
                },
                {
                    "name": "guard.loop_detected",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {"message": "Loop detected"},
                },
                {
                    "name": "guard.budget_exceeded",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {"message": "Budget exceeded"},
                },
            ]
        )

        self.assertEqual(savings["exact_tokens_saved"], 0)
        self.assertEqual(savings["estimated_tokens_saved"], 1500)
        self.assertAlmostEqual(savings["estimated_usd_saved"], 0.0075, places=4)
        self.assertEqual(
            savings["reasons"],
            [
                {
                    "kind": "loop_prevented",
                    "confidence": "estimated",
                    "occurrences": 1,
                    "tokens_saved": 1500,
                    "usd_saved": 0.0075,
                }
            ],
        )

    def test_reports_estimated_retry_savings_from_nested_cost(self):
        savings = summarize_savings(
            [
                {
                    "name": "llm.end",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {
                        "model": "gpt-4o",
                        "provider": "openai",
                        "token_usage": {
                            "prompt_tokens": 1000,
                            "completion_tokens": 500,
                            "total_tokens": 1500,
                        },
                        "cost_usd": 0.0075,
                    },
                },
                {
                    "name": "guard.retry_limit_exceeded",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {"message": "Retry limit exceeded"},
                },
            ]
        )

        self.assertEqual(savings["estimated_tokens_saved"], 1500)
        self.assertAlmostEqual(savings["estimated_usd_saved"], 0.0075, places=4)
        self.assertEqual(savings["reasons"][0]["kind"], "retry_storm_stopped")

    def test_ignores_malformed_usage_fields(self):
        savings = summarize_savings(
            [
                {
                    "name": "llm.result",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {
                        "model": "gpt-4o",
                        "provider": "openai",
                        "usage": {"prompt_tokens": "1000"},
                    },
                }
            ]
        )

        self.assertEqual(
            savings,
            {
                "exact_tokens_saved": 0,
                "estimated_tokens_saved": 0,
                "exact_usd_saved": 0.0,
                "estimated_usd_saved": 0.0,
                "reasons": [],
            },
        )

    def test_accepts_trace_file_path(self):
        path = _write_trace(
            [
                {
                    "name": "llm.result",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {
                        "model": "gpt-4o",
                        "provider": "openai",
                        "usage": {
                            "prompt_tokens": 1000,
                            "completion_tokens": 500,
                            "total_tokens": 1500,
                        },
                    },
                },
                {
                    "name": "guard.budget_exceeded",
                    "kind": "event",
                    "phase": "emit",
                    "trace_id": "t1",
                    "data": {"message": "Budget exceeded"},
                },
            ]
        )
        try:
            savings = summarize_savings(path)
            self.assertEqual(savings["estimated_tokens_saved"], 1500)
            self.assertAlmostEqual(savings["estimated_usd_saved"], 0.0075, places=4)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
