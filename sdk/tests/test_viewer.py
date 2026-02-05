import json
import os
import tempfile
import threading
import unittest
from http.client import HTTPConnection

from agentguard.viewer import _Handler, serve, _HTML


class TestViewerHTML(unittest.TestCase):
    def test_html_contains_gantt_elements(self):
        self.assertIn("AgentGuard Trace Viewer", _HTML)
        self.assertIn("gantt", _HTML)
        self.assertIn("Gantt Timeline", _HTML)

    def test_html_contains_legend(self):
        self.assertIn("Reasoning", _HTML)
        self.assertIn("Tool", _HTML)
        self.assertIn("LLM", _HTML)
        self.assertIn("Guard", _HTML)
        self.assertIn("Error", _HTML)

    def test_html_has_stats_section(self):
        self.assertIn("id=\"stats\"", _HTML)

    def test_html_has_detail_panel(self):
        self.assertIn("id=\"detail\"", _HTML)


class TestViewerHandler(unittest.TestCase):
    def setUp(self):
        self.fd, self.path = tempfile.mkstemp(suffix=".jsonl")
        with os.fdopen(self.fd, "w") as f:
            f.write(json.dumps({"name": "test", "kind": "event"}) + "\n")

    def tearDown(self):
        os.unlink(self.path)

    def test_serve_starts_and_serves_html(self):
        """Start the viewer server, fetch /, verify HTML returned."""
        _Handler.trace_path = self.path
        from http.server import HTTPServer

        server = HTTPServer(("127.0.0.1", 0), _Handler)
        port = server.server_address[1]
        t = threading.Thread(target=server.handle_request, daemon=True)
        t.start()

        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/")
        resp = conn.getresponse()
        body = resp.read().decode()
        conn.close()

        self.assertEqual(resp.status, 200)
        self.assertIn("AgentGuard Trace Viewer", body)

    def test_serve_trace_endpoint(self):
        """Fetch /trace and verify JSONL is returned."""
        _Handler.trace_path = self.path
        from http.server import HTTPServer

        server = HTTPServer(("127.0.0.1", 0), _Handler)
        port = server.server_address[1]
        t = threading.Thread(target=server.handle_request, daemon=True)
        t.start()

        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/trace")
        resp = conn.getresponse()
        body = resp.read().decode()
        conn.close()

        self.assertEqual(resp.status, 200)
        data = json.loads(body.strip())
        self.assertEqual(data["name"], "test")

    def test_404_for_unknown_path(self):
        _Handler.trace_path = self.path
        from http.server import HTTPServer

        server = HTTPServer(("127.0.0.1", 0), _Handler)
        port = server.server_address[1]
        t = threading.Thread(target=server.handle_request, daemon=True)
        t.start()

        conn = HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/nope")
        resp = conn.getresponse()
        conn.close()

        self.assertEqual(resp.status, 404)


if __name__ == "__main__":
    unittest.main()
