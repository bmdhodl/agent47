"""Local stand-in for POST /v1/responses: the model asks for search_docs every turn.

Used to run examples/openai_agents_sdk_budget.py offline. Usage is 40k input and
10k output tokens per call, about $0.012 on gpt-4o-mini.
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

COUNT = {"n": 0}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        COUNT["n"] += 1
        body = {
            "id": f"resp_{COUNT['n']}", "object": "response", "created_at": 0,
            "status": "completed", "model": "gpt-4o-mini",
            "output": [{"type": "function_call", "id": f"fc_{COUNT['n']}",
                        "call_id": f"call_{COUNT['n']}", "name": "search_docs",
                        "arguments": "{\"query\": \"LoopGuard\"}", "status": "completed"}],
            "parallel_tool_calls": True, "tool_choice": "auto", "tools": [],
            "usage": {"input_tokens": 40000, "input_tokens_details": {"cached_tokens": 0},
                      "output_tokens": 10000, "output_tokens_details": {"reasoning_tokens": 0},
                      "total_tokens": 50000},
        }
        data = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        print("model call", COUNT["n"], file=sys.stderr, flush=True)

    def log_message(self, *args):
        pass


HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
