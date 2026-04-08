import importlib.util
import json
import pathlib
import subprocess
import sys
import unittest

_SCRIPT_PATH = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "sdk_preflight.py"
_SPEC = importlib.util.spec_from_file_location("sdk_preflight", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
sdk_preflight = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = sdk_preflight
_SPEC.loader.exec_module(sdk_preflight)


class TestBuildPlan(unittest.TestCase):
    def test_sdk_code_change_adds_targeted_checks(self):
        steps = sdk_preflight.build_plan(
            [
                "sdk/agentguard/instrument.py",
                "sdk/agentguard/usage.py",
            ]
        )

        labels = [step.label for step in steps]
        self.assertEqual(labels, ["ruff", "targeted-pytest", "structural", "security"])

        targeted = next(step for step in steps if step.label == "targeted-pytest")
        self.assertIn("sdk/tests/test_instrument.py", targeted.command)
        self.assertIn("sdk/tests/test_instrument_patch.py", targeted.command)
        self.assertIn("sdk/tests/test_langchain_integration.py", targeted.command)
        self.assertIn("sdk/tests/test_savings.py", targeted.command)

    def test_readme_sync_inputs_add_sync_checks(self):
        steps = sdk_preflight.build_plan(["README.md", "sdk/PYPI_README.md"])

        labels = [step.label for step in steps]
        self.assertEqual(labels, ["pypi-readme-sync", "pypi-readme-test"])

    def test_changed_test_file_runs_directly(self):
        steps = sdk_preflight.build_plan(["sdk/tests/test_quickstart.py"])

        labels = [step.label for step in steps]
        self.assertEqual(labels, ["ruff", "targeted-pytest"])
        targeted = next(step for step in steps if step.label == "targeted-pytest")
        self.assertEqual(
            targeted.command,
            [sys.executable, "-m", "pytest", "sdk/tests/test_quickstart.py", "-v"],
        )

    def test_preflight_script_change_runs_its_own_tests(self):
        steps = sdk_preflight.build_plan(["scripts/sdk_preflight.py"])

        labels = [step.label for step in steps]
        self.assertEqual(labels, ["ruff", "targeted-pytest"])
        targeted = next(step for step in steps if step.label == "targeted-pytest")
        self.assertEqual(
            targeted.command,
            [sys.executable, "-m", "pytest", "sdk/tests/test_sdk_preflight.py", "-v"],
        )

    def test_conftest_change_runs_hosted_ingest_regressions(self):
        steps = sdk_preflight.build_plan(["sdk/tests/conftest.py"])

        labels = [step.label for step in steps]
        self.assertEqual(labels, ["ruff", "import-check", "targeted-pytest"])
        targeted = next(step for step in steps if step.label == "targeted-pytest")
        self.assertEqual(
            targeted.command,
            [
                sys.executable,
                "-m",
                "pytest",
                "sdk/tests/test_e2e_pipeline.py",
                "sdk/tests/test_hosted_ingest_contract.py",
                "sdk/tests/test_integration_cost_guardrail.py",
                "-v",
            ],
        )

    def test_integration_dashboard_script_change_runs_helper_tests(self):
        steps = sdk_preflight.build_plan(["sdk/tests/integration_dashboard.py"])

        labels = [step.label for step in steps]
        self.assertEqual(labels, ["ruff", "import-check", "targeted-pytest"])
        targeted = next(step for step in steps if step.label == "targeted-pytest")
        self.assertEqual(
            targeted.command,
            [
                sys.executable,
                "-m",
                "pytest",
                "sdk/tests/test_integration_dashboard_script.py",
                "-v",
            ],
        )

    def test_non_test_sdk_script_change_gets_import_check(self):
        steps = sdk_preflight.build_plan(["sdk/tests/e2e_v110.py"])

        labels = [step.label for step in steps]
        self.assertEqual(labels, ["ruff", "import-check"])
        import_check = next(step for step in steps if step.label == "import-check")
        self.assertEqual(
            import_check.command,
            [
                sys.executable,
                "-c",
                sdk_preflight.IMPORT_CHECK_SNIPPET,
                "sdk/tests/e2e_v110.py",
            ],
        )

    def test_mcp_server_change_runs_mcp_test_step(self):
        steps = sdk_preflight.build_plan(["mcp-server/src/tools.ts"])

        labels = [step.label for step in steps]
        self.assertEqual(labels, ["mcp-test"])
        self.assertEqual(
            steps[0].command,
            ["npm", "--prefix", "mcp-server", "test"],
        )


class TestPlanCli(unittest.TestCase):
    def test_plan_output_is_json(self):
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPT_PATH),
                "--plan",
                "--changed-file",
                "sdk/agentguard/reporting.py",
            ],
            capture_output=True,
            check=True,
            text=True,
        )

        payload = json.loads(result.stdout)
        labels = [step["label"] for step in payload]
        self.assertEqual(labels, ["ruff", "targeted-pytest", "structural", "security"])
