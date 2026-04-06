import importlib.util
import pathlib
import sys
import unittest

_SCRIPT_PATH = pathlib.Path(__file__).resolve().parent / "integration_dashboard.py"
_SPEC = importlib.util.spec_from_file_location("integration_dashboard", _SCRIPT_PATH)
assert _SPEC is not None and _SPEC.loader is not None
integration_dashboard = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = integration_dashboard
_SPEC.loader.exec_module(integration_dashboard)


class TestIntegrationDashboardHelpers(unittest.TestCase):
    def test_build_traces_url_without_trace_id(self):
        self.assertEqual(
            integration_dashboard._build_traces_url("https://app.agentguard47.com"),
            "https://app.agentguard47.com/api/v1/traces",
        )

    def test_build_traces_url_with_trace_id(self):
        self.assertEqual(
            integration_dashboard._build_traces_url(
                "https://app.agentguard47.com",
                trace_id="trace_123",
            ),
            "https://app.agentguard47.com/api/v1/traces?trace_id=trace_123",
        )

    def test_build_traces_url_with_service(self):
        self.assertEqual(
            integration_dashboard._build_traces_url(
                "https://app.agentguard47.com",
                service="svc_123",
            ),
            "https://app.agentguard47.com/api/v1/traces?service=svc_123",
        )

    def test_build_traces_url_with_trace_id_and_service(self):
        self.assertEqual(
            integration_dashboard._build_traces_url(
                "https://app.agentguard47.com",
                trace_id="trace_123",
                service="svc_123",
            ),
            "https://app.agentguard47.com/api/v1/traces?trace_id=trace_123&service=svc_123",
        )

    def test_build_traces_url_strips_trailing_slash(self):
        self.assertEqual(
            integration_dashboard._build_traces_url(
                "https://app.agentguard47.com/",
                service="svc_123",
            ),
            "https://app.agentguard47.com/api/v1/traces?service=svc_123",
        )

    def test_build_traces_url_encodes_query_values(self):
        self.assertEqual(
            integration_dashboard._build_traces_url(
                "https://app.agentguard47.com",
                trace_id="trace/123",
                service="svc name",
            ),
            "https://app.agentguard47.com/api/v1/traces?trace_id=trace%2F123&service=svc+name",
        )

    def test_extract_traces_prefers_traces_key(self):
        payload = {"traces": [{"trace_id": "abc"}], "data": [{"trace_id": "wrong"}]}
        self.assertEqual(integration_dashboard._extract_traces(payload), payload["traces"])

    def test_extract_traces_falls_back_to_data(self):
        payload = {"data": [{"trace_id": "abc"}]}
        self.assertEqual(integration_dashboard._extract_traces(payload), payload["data"])

    def test_extract_traces_returns_empty_list_for_unexpected_payload(self):
        self.assertEqual(integration_dashboard._extract_traces({"ok": True}), [])

    def test_find_trace_returns_matching_trace(self):
        traces = [{"trace_id": "a"}, {"trace_id": "b"}]
        self.assertEqual(
            integration_dashboard._find_trace(traces, "b"),
            {"trace_id": "b"},
        )

    def test_find_trace_returns_none_when_missing(self):
        self.assertIsNone(integration_dashboard._find_trace([{"trace_id": "a"}], "missing"))
