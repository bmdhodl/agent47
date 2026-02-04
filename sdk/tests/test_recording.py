import os
import tempfile
import unittest

from agentguard.recording import Recorder, Replayer


class TestRecording(unittest.TestCase):
    def test_replay_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "replay.jsonl")
            recorder = Recorder(path)
            recorder.record_call("llm", {"prompt": "hi"}, {"text": "hello"})

            replayer = Replayer(path)
            result = replayer.replay_call("llm", {"prompt": "hi"})
            self.assertEqual(result["text"], "hello")

            with self.assertRaises(KeyError):
                replayer.replay_call("llm", {"prompt": "missing"})


if __name__ == "__main__":
    unittest.main()
