"""Gantt-style trace viewer — self-contained HTML served via stdlib."""
from __future__ import annotations

import argparse
import os
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

_HTML = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>AgentGuard Trace Viewer</title>
    <style>
      :root {
        --bg:#0f1115; --ink:#f1f5f9; --muted:#9aa4b2; --card:#171a21;
        --accent:#4ade80; --blue:#60a5fa; --purple:#a78bfa;
        --green:#4ade80; --red:#f87171; --yellow:#fbbf24;
        --border:#252a34;
      }
      * { box-sizing: border-box; }
      body { margin:0; font-family:'IBM Plex Sans',system-ui,sans-serif; background:var(--bg); color:var(--ink); }
      header { padding:16px 20px; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:12px; }
      h1 { margin:0; font-size:20px; font-weight:600; }
      .badge { font-size:11px; background:#222833; padding:2px 8px; border-radius:10px; color:var(--muted); }
      .wrap { padding:20px; }
      .stats { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:10px; margin-bottom:20px; }
      .card { background:var(--card); padding:10px 14px; border-radius:8px; border:1px solid var(--border); }
      .card .label { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.5px; }
      .card .val { font-size:20px; font-weight:600; margin-top:2px; }
      .card .val.green { color:var(--green); }

      /* Gantt timeline */
      .gantt { position:relative; margin-top:12px; }
      .gantt-row { display:flex; align-items:center; height:28px; border-bottom:1px solid #1a1e27; cursor:pointer; }
      .gantt-row:hover { background:#1a1e27; }
      .gantt-label { width:220px; min-width:220px; padding:0 8px; font-size:12px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
      .gantt-track { flex:1; position:relative; height:100%; }
      .gantt-bar { position:absolute; height:16px; top:6px; border-radius:3px; min-width:2px; transition: opacity .15s; }
      .gantt-bar:hover { opacity:.85; }
      .gantt-bar.reasoning { background:var(--blue); }
      .gantt-bar.tool { background:var(--green); }
      .gantt-bar.llm { background:var(--purple); }
      .gantt-bar.guard { background:var(--yellow); }
      .gantt-bar.error { background:var(--red); }
      .gantt-bar.default { background:#64748b; }

      /* Detail panel */
      .detail { display:none; background:var(--card); border:1px solid var(--border); border-radius:8px; padding:16px; margin:12px 0; font-size:13px; }
      .detail.open { display:block; }
      .detail pre { background:#0f1115; padding:10px; border-radius:6px; overflow-x:auto; font-size:12px; color:var(--muted); }
      .detail .dhead { font-weight:600; margin-bottom:8px; color:var(--accent); }

      /* Legend */
      .legend { display:flex; gap:16px; margin-bottom:14px; flex-wrap:wrap; }
      .legend-item { display:flex; align-items:center; gap:5px; font-size:12px; color:var(--muted); }
      .legend-dot { width:10px; height:10px; border-radius:2px; }
    </style>
  </head>
  <body>
    <header>
      <h1>AgentGuard Trace Viewer</h1>
      <span class="badge">Gantt Timeline</span>
    </header>
    <div class="wrap">
      <div class="stats" id="stats"></div>
      <div class="legend">
        <div class="legend-item"><div class="legend-dot" style="background:var(--blue)"></div>Reasoning</div>
        <div class="legend-item"><div class="legend-dot" style="background:var(--green)"></div>Tool</div>
        <div class="legend-item"><div class="legend-dot" style="background:var(--purple)"></div>LLM</div>
        <div class="legend-item"><div class="legend-dot" style="background:var(--yellow)"></div>Guard</div>
        <div class="legend-item"><div class="legend-dot" style="background:var(--red)"></div>Error</div>
      </div>
      <div class="gantt" id="gantt"></div>
      <div class="detail" id="detail"></div>
    </div>
    <script>
      async function load() {
        const res = await fetch('/trace');
        const text = await res.text();
        const lines = text.split('\\n').filter(Boolean);
        const events = lines.map(l => JSON.parse(l));

        if (!events.length) { document.getElementById('gantt').innerHTML = '<p style="color:var(--muted)">No events found.</p>'; return; }

        // Stats
        const totalEvents = events.length;
        const spans = events.filter(e => e.kind === 'span');
        const spanStarts = spans.filter(e => e.phase === 'start');
        const spanEnds = spans.filter(e => e.phase === 'end');
        const evts = events.filter(e => e.kind === 'event');
        const reasoning = evts.filter(e => e.name === 'reasoning.step').length;
        const toolResults = evts.filter(e => e.name === 'tool.result').length;
        const llmResults = evts.filter(e => e.name === 'llm.result').length;
        const loops = evts.filter(e => e.name === 'guard.loop_detected').length;
        const errors = events.filter(e => e.error != null).length;

        let totalMs = 0;
        spanEnds.forEach(e => { if (e.duration_ms && e.duration_ms > totalMs) totalMs = e.duration_ms; });

        const totalTokens = events.reduce((acc, e) => {
          const d = e.data || {};
          const u = d.token_usage || d.usage || {};
          return acc + (u.total_tokens || 0);
        }, 0);

        const statsEl = document.getElementById('stats');
        const cards = [
          ['Events', totalEvents, ''],
          ['Spans', spanStarts.length, ''],
          ['Run time', totalMs > 0 ? totalMs.toFixed(1) + ' ms' : '-', ''],
          ['Reasoning', reasoning, ''],
          ['Tool calls', toolResults, ''],
          ['LLM calls', llmResults, ''],
          ['Loop hits', loops, loops > 0 ? 'color:var(--red)' : ''],
          ['Errors', errors, errors > 0 ? 'color:var(--red)' : ''],
          ['Tokens', totalTokens || '-', ''],
        ];
        statsEl.innerHTML = cards.map(([k,v,s]) =>
          `<div class="card"><div class="label">${k}</div><div class="val" style="${s}">${v}</div></div>`
        ).join('');

        // Build timeline rows
        // Each event gets a row. Position = ts relative to min ts. Width = duration_ms or a small dot.
        const minTs = Math.min(...events.map(e => e.ts));
        const maxTs = Math.max(...events.map(e => e.ts));
        const maxDur = Math.max(...spanEnds.map(e => e.duration_ms || 0), 1);
        const timeRange = Math.max((maxTs - minTs) * 1000, maxDur, 1); // in ms

        // Build span pairs: match start/end by span_id
        const spanMap = {};
        spans.forEach(e => {
          if (!spanMap[e.span_id]) spanMap[e.span_id] = {};
          if (e.phase === 'start') spanMap[e.span_id].start = e;
          if (e.phase === 'end') spanMap[e.span_id].end = e;
        });

        // Build display rows: spans (paired) + standalone events
        const rows = [];

        // Add span rows
        Object.values(spanMap).forEach(pair => {
          const s = pair.start || pair.end;
          const dur = pair.end ? (pair.end.duration_ms || 0) : 0;
          const startMs = (s.ts - minTs) * 1000;
          rows.push({
            name: s.name,
            startMs,
            durMs: dur,
            type: classifyName(s.name),
            event: s,
            endEvent: pair.end,
            depth: s.parent_id ? 1 : 0,
          });
        });

        // Add standalone events (not span start/end)
        evts.forEach(e => {
          const startMs = (e.ts - minTs) * 1000;
          rows.push({
            name: e.name,
            startMs,
            durMs: 0,
            type: classifyName(e.name),
            event: e,
            endEvent: null,
            depth: 1,
          });
        });

        // Sort by startMs
        rows.sort((a, b) => a.startMs - b.startMs || a.depth - b.depth);

        const ganttEl = document.getElementById('gantt');
        ganttEl.innerHTML = rows.map((r, i) => {
          const left = (r.startMs / timeRange * 100).toFixed(4);
          const width = r.durMs > 0 ? Math.max(r.durMs / timeRange * 100, 0.3).toFixed(4) : '0.3';
          const indent = r.depth > 0 ? '&nbsp;&nbsp;' : '';
          return `<div class="gantt-row" data-idx="${i}">
            <div class="gantt-label" title="${esc(r.name)}">${indent}${esc(r.name)}</div>
            <div class="gantt-track">
              <div class="gantt-bar ${r.type}" style="left:${left}%;width:${width}%" title="${esc(r.name)} ${r.durMs > 0 ? r.durMs.toFixed(1)+'ms' : 'event'}"></div>
            </div>
          </div>`;
        }).join('');

        // Click to expand detail
        const detailEl = document.getElementById('detail');
        ganttEl.addEventListener('click', e => {
          const row = e.target.closest('.gantt-row');
          if (!row) return;
          const idx = parseInt(row.dataset.idx);
          const r = rows[idx];
          const ev = r.endEvent || r.event;
          detailEl.className = 'detail open';
          detailEl.innerHTML = `
            <div class="dhead">${esc(r.name)}</div>
            <p><strong>Kind:</strong> ${esc(ev.kind||'')} &nbsp; <strong>Phase:</strong> ${esc(ev.phase||'')}
            ${r.durMs > 0 ? '&nbsp; <strong>Duration:</strong> ' + r.durMs.toFixed(3) + ' ms' : ''}
            ${ev.error ? '&nbsp; <strong style="color:var(--red)">Error:</strong> ' + esc(ev.error.message||'') : ''}
            </p>
            <p><strong>trace_id:</strong> ${esc(ev.trace_id||'')}<br><strong>span_id:</strong> ${esc(ev.span_id||'')}${ev.parent_id ? '<br><strong>parent_id:</strong> '+esc(ev.parent_id) : ''}</p>
            <pre>${esc(JSON.stringify(ev.data || {}, null, 2))}</pre>
          `;
        });
      }

      function esc(s) {
        const d = document.createElement('div');
        d.appendChild(document.createTextNode(s));
        return d.innerHTML;
      }

      function classifyName(name) {
        if (name.startsWith('reasoning')) return 'reasoning';
        if (name.startsWith('tool')) return 'tool';
        if (name.startsWith('llm')) return 'llm';
        if (name.startsWith('guard')) return 'guard';
        if (name.includes('error')) return 'error';
        return 'default';
      }

      load();
    </script>
  </body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    trace_path: Optional[str] = None

    def do_GET(self) -> None:
        if self.path == "/":
            self._send(200, _HTML, content_type="text/html")
            return
        if self.path == "/trace":
            if not self.trace_path or not os.path.exists(self.trace_path):
                self._send(404, "trace not found")
                return
            with open(self.trace_path, encoding="utf-8") as f:
                data = f.read()
            self._send(200, data, content_type="text/plain")
            return
        self._send(404, "not found")

    def log_message(self, format: str, *args) -> None:
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
