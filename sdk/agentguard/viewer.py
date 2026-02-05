from __future__ import annotations

import argparse
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional


_HTML = """<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <title>AgentGuard Trace Viewer</title>
    <style>
      :root { --bg:#0f1115; --ink:#f1f5f9; --muted:#9aa4b2; --card:#171a21; --accent:#4ade80; }
      body { margin:0; font-family: 'IBM Plex Sans', system-ui, sans-serif; background:var(--bg); color:var(--ink); }
      header { padding:20px; border-bottom:1px solid #252a34; }
      h1 { margin:0; font-size:22px; }
      .wrap { padding:20px; }
      .stats { display:grid; grid-template-columns: repeat(auto-fit, minmax(180px,1fr)); gap:12px; }
      .card { background:var(--card); padding:12px; border-radius:10px; border:1px solid #222833; }
      .label { color:var(--muted); font-size:12px; }
      table { width:100%; border-collapse: collapse; margin-top:16px; }
      th, td { text-align:left; padding:8px; border-bottom:1px solid #222833; font-size:13px; }
      code { color: var(--accent); }
    </style>
  </head>
  <body>
    <header>
      <h1>AgentGuard Trace Viewer</h1>
      <div class=\"label\">Loaded from local JSONL trace</div>
    </header>
    <div class=\"wrap\">
      <div class=\"stats\" id=\"stats\"></div>
      <table>
        <thead>
          <tr>
            <th>ts</th>
            <th>kind</th>
            <th>name</th>
            <th>trace_id</th>
            <th>span_id</th>
          </tr>
        </thead>
        <tbody id=\"rows\"></tbody>
      </table>
    </div>
    <script>
      async function load() {
        const res = await fetch('/trace');
        const text = await res.text();
        const lines = text.split('\n').filter(Boolean);
        const events = lines.map(l => JSON.parse(l));

        const stats = {
          total: events.length,
          spans: events.filter(e => e.kind === 'span').length,
          events: events.filter(e => e.kind === 'event').length,
          reasoning: events.filter(e => e.name === 'reasoning.step').length,
          loops: events.filter(e => e.name === 'guard.loop_detected').length,
        };

        const statsEl = document.getElementById('stats');
        statsEl.innerHTML = [
          ['Total events', stats.total],
          ['Spans', stats.spans],
          ['Events', stats.events],
          ['Reasoning steps', stats.reasoning],
          ['Loop hits', stats.loops],
        ].map(([k,v]) => `
          <div class=\"card\"><div class=\"label\">${k}</div><div><code>${v}</code></div></div>
        `).join('');

        const rows = document.getElementById('rows');
        rows.innerHTML = events.map(e => `
          <tr>
            <td>${new Date(e.ts * 1000).toISOString()}</td>
            <td>${e.kind}</td>
            <td>${e.name}</td>
            <td>${e.trace_id}</td>
            <td>${e.span_id}</td>
          </tr>
        `).join('');
      }
      load();
    </script>
  </body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    trace_path: Optional[str] = None

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/":
            self._send(200, _HTML, content_type="text/html")
            return
        if self.path == "/trace":
            if not self.trace_path or not os.path.exists(self.trace_path):
                self._send(404, "trace not found")
                return
            with open(self.trace_path, "r", encoding="utf-8") as f:
                data = f.read()
            self._send(200, data, content_type="text/plain")
            return
        self._send(404, "not found")

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def _send(self, status: int, body: str, content_type: str = "text/plain") -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def serve(trace_path: str, port: int = 8080, open_browser: bool = True) -> None:
    handler = _Handler
    handler.trace_path = trace_path

    server = HTTPServer(("127.0.0.1", port), handler)

    if open_browser:
        threading.Timer(0.4, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()

    print(f"Viewer running at http://127.0.0.1:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(prog="agentguard-view")
    parser.add_argument("path", help="Path to JSONL trace")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--no-open", action="store_true")
    args = parser.parse_args()

    serve(args.path, port=args.port, open_browser=not args.no_open)


if __name__ == "__main__":
    main()
