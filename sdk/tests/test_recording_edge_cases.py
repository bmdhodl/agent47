"""Edge case tests for recording.py: Recorder and Replayer."""
import json
import os
import tempfile
import unittest

from agentguard.recording import Recorder, Replayer


class TestRecorderEdgeCases(unittest.TestCase):
    def test_record_with_metadata(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            recorder = Recorder(path)
            recorder.record_call("llm", {"prompt": "hi"}, {"text": "hello"}, meta={"env": "test"})

            with open(path, "r") as f:
                data = json.loads(f.readline())
            self.assertEqual(data["meta"]["env"], "test")
        finally:
            os.unlink(path)

    def test_record_multiple_calls(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            recorder = Recorder(path)
            recorder.record_call("llm", {"p": "1"}, {"r": "a"})
            recorder.record_call("llm", {"p": "2"}, {"r": "b"})
            recorder.record_call("search", {"q": "x"}, {"results": []})

            with open(path, "r") as f:
                lines = [l.strip() for l in f if l.strip()]
            self.assertEqual(len(lines), 3)
        finally:
            os.unlink(path)

    def test_record_repr(self):
        recorder = Recorder("test.jsonl")
        self.assertIn("test.jsonl", repr(recorder))


class TestReplayerEdgeCases(unittest.TestCase):
    def test_replay_missing_file(self):
        replayer = Replayer("/tmp/nonexistent_file_12345.jsonl")
        # Should have no entries, not crash
        with self.assertRaises(KeyError):
            replayer.replay_call("llm", {"prompt": "hi"})

    def test_replay_corrupt_lines(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('this is not json\n')
            f.write('{"name": "llm", "request": {"p": "1"}, "response": {"r": "a"}}\n')
            f.write('another bad line\n')
            path = f.name

        try:
            replayer = Replayer(path)
            result = replayer.replay_call("llm", {"p": "1"})
            self.assertEqual(result, {"r": "a"})
        finally:
            os.unlink(path)

    def test_replay_empty_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            replayer = Replayer(path)
            with self.assertRaises(KeyError):
                replayer.replay_call("llm", {"prompt": "hi"})
        finally:
            os.unlink(path)

    def test_replay_missing_fields(self):
        """Lines with missing name/request/response should be skipped."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            # Missing response
            f.write('{"name": "llm", "request": {"p": "1"}}\n')
            # Missing request
            f.write('{"name": "llm", "response": {"r": "a"}}\n')
            # Missing name
            f.write('{"request": {"p": "1"}, "response": {"r": "a"}}\n')
            # Valid
            f.write('{"name": "search", "request": {"q": "x"}, "response": {"results": []}}\n')
            path = f.name

        try:
            replayer = Replayer(path)
            # Only the valid entry should be loaded
            result = replayer.replay_call("search", {"q": "x"})
            self.assertEqual(result, {"results": []})
            # Others should raise
            with self.assertRaises(KeyError):
                replayer.replay_call("llm", {"p": "1"})
        finally:
            os.unlink(path)

    def test_replay_duplicate_keys_last_wins(self):
        """When multiple entries have the same key, last one wins."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            f.write('{"name": "llm", "request": {"p": "1"}, "response": {"r": "first"}}\n')
            f.write('{"name": "llm", "request": {"p": "1"}, "response": {"r": "second"}}\n')
            path = f.name

        try:
            replayer = Replayer(path)
            result = replayer.replay_call("llm", {"p": "1"})
            self.assertEqual(result, {"r": "second"})
        finally:
            os.unlink(path)

    def test_replay_repr(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name
        try:
            replayer = Replayer(path)
            self.assertIn(path, repr(replayer))
        finally:
            os.unlink(path)

    def test_roundtrip_with_complex_data(self):
        """Record and replay with nested dicts, lists, and special chars."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            recorder = Recorder(path)
            request = {"prompt": "Hello\nWorld", "params": {"temp": 0.7, "top_p": 0.9}}
            response = {"text": "Hi!", "tokens": [1, 2, 3], "meta": {"model": "gpt-4"}}
            recorder.record_call("llm", request, response)

            replayer = Replayer(path)
            result = replayer.replay_call("llm", request)
            self.assertEqual(result, response)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
