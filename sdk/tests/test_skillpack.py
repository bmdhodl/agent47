import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from agentguard.cli import _skillpack
from agentguard.skillpack import TARGET_CHOICES, run_skillpack


class TestSkillpack(unittest.TestCase):
    def test_all_targets_json_is_parseable(self) -> None:
        buf = io.StringIO()

        result = run_skillpack(json_output=True, stream=buf)

        self.assertEqual(result, 0)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["target"], "all")
        self.assertEqual(
            payload["targets"],
            ["codex", "claude-code", "copilot", "cursor"],
        )
        self.assertEqual(payload["files"][0]["path"], ".agentguard.json")

    def test_target_specific_text_mentions_expected_path(self) -> None:
        buf = io.StringIO()

        result = run_skillpack(target="claude-code", stream=buf)

        self.assertEqual(result, 0)
        output = buf.getvalue()
        self.assertIn("Target: claude-code", output)
        self.assertIn("Suggested path: CLAUDE.md", output)
        self.assertIn("agentguard quickstart --framework raw --write", output)

    def test_invalid_target_returns_error(self) -> None:
        buf = io.StringIO()

        result = run_skillpack(target="unknown", json_output=True, stream=buf)

        self.assertEqual(result, 1)
        payload = json.loads(buf.getvalue())
        self.assertEqual(payload["status"], "error")
        self.assertIn("Unknown target", payload["error"])

    def test_write_creates_default_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            os.chdir(tmp)
            try:
                buf = io.StringIO()
                result = run_skillpack(write_files=True, stream=buf)

                self.assertEqual(result, 0)
                self.assertTrue(os.path.exists("agentguard_skillpack/.agentguard.json"))
                self.assertTrue(os.path.exists("agentguard_skillpack/AGENTS.md"))
                self.assertTrue(os.path.exists("agentguard_skillpack/CLAUDE.md"))
                self.assertTrue(os.path.exists("agentguard_skillpack/.github/copilot-instructions.md"))
                self.assertTrue(os.path.exists("agentguard_skillpack/.cursor/rules/agentguard.mdc"))
                with open(
                    "agentguard_skillpack/.agentguard.json",
                    encoding="utf-8",
                ) as handle:
                    config = json.load(handle)
                self.assertEqual(config["profile"], "coding-agent")
                self.assertIn("Wrote files:", buf.getvalue())
            finally:
                os.chdir(cwd)

    def test_write_refuses_to_overwrite_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = os.path.join(tmp, "skillpack", "AGENTS.md")
            os.makedirs(os.path.dirname(destination), exist_ok=True)
            with open(destination, "w", encoding="utf-8") as handle:
                handle.write("keep me\n")

            buf = io.StringIO()
            result = run_skillpack(
                target="codex",
                write_files=True,
                output_dir=os.path.join(tmp, "skillpack"),
                stream=buf,
            )

            self.assertEqual(result, 1)
            self.assertIn("Refusing to overwrite existing file", buf.getvalue())
            with open(destination, encoding="utf-8") as handle:
                self.assertIn("keep me", handle.read())

    def test_cli_skillpack_can_write_target_specific_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destination = os.path.join(tmp, "pack")
            buf = io.StringIO()

            with redirect_stdout(buf), self.assertRaises(SystemExit) as ctx:
                _skillpack(
                    target="copilot",
                    write_files=True,
                    output_dir=destination,
                )

            self.assertEqual(ctx.exception.code, 0)
            self.assertTrue(os.path.exists(os.path.join(destination, ".agentguard.json")))
            self.assertTrue(
                os.path.exists(os.path.join(destination, ".github", "copilot-instructions.md"))
            )
            self.assertIn("Output dir:", buf.getvalue())

    def test_target_choices_stay_stable(self) -> None:
        self.assertEqual(
            TARGET_CHOICES,
            ("all", "codex", "claude-code", "copilot", "cursor"),
        )


if __name__ == "__main__":
    unittest.main()
