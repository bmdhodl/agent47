import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

_SCRIPTS_DIR = pathlib.Path(__file__).resolve().parents[2] / "scripts"
_SCRIPT_PATH = _SCRIPTS_DIR / "resolve_discussion_category.py"
_SPEC = importlib.util.spec_from_file_location("resolve_discussion_category", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
resolve_discussion_category = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = resolve_discussion_category
_SPEC.loader.exec_module(resolve_discussion_category)


class TestDiscussionCategoryResolution(unittest.TestCase):
    def test_extracts_matching_category_node_id(self):
        payload = [
            {"name": "General", "node_id": "DIC_general"},
            {"name": "Announcements", "node_id": "DIC_announcements"},
        ]

        self.assertEqual(
            resolve_discussion_category.extract_category_node_id(payload, "Announcements"),
            "DIC_announcements",
        )

    def test_rejects_github_error_object(self):
        payload = {
            "message": "Not Found",
            "documentation_url": "https://docs.github.com/rest",
            "status": "404",
        }

        self.assertIsNone(
            resolve_discussion_category.extract_category_node_id(payload, "Announcements")
        )

    def test_rejects_missing_or_blank_node_id(self):
        payload = [
            {"name": "Announcements", "node_id": ""},
            {"name": "Announcements"},
        ]

        self.assertIsNone(
            resolve_discussion_category.extract_category_node_id(payload, "Announcements")
        )

    def test_cli_prints_node_id_for_valid_category(self):
        result = subprocess.run(
            [sys.executable, str(_SCRIPT_PATH)],
            input=json.dumps([{"name": "Announcements", "node_id": "DIC_ok"}]),
            capture_output=True,
            check=True,
            text=True,
        )

        self.assertEqual(result.stdout.strip(), "DIC_ok")

    def test_cli_exits_nonzero_for_error_payload(self):
        result = subprocess.run(
            [sys.executable, str(_SCRIPT_PATH)],
            input=json.dumps({"message": "Not Found", "status": "404"}),
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
