"""fastapi_budget_middleware.py — AgentGuard as FastAPI middleware.

Shows how to integrate AgentGuard into a web app: each request gets its own
trace, and a shared BudgetGuard enforces a global spend limit across all
requests.

Setup:
  pip install agentguard47 fastapi uvicorn

Run:
  python fastapi_budget_middleware.py
  # Then: curl http://localhost:8000/ask?q=hello
"""
from __future__ import annotations

import os
import time
from contextlib import asynccontextmanager

from agentguard import (
    BudgetGuard,
    BudgetExceeded,
    JsonlFileSink,
    LoopGuard,
    Tracer,
)

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    print("Install dependencies: pip install fastapi uvicorn")
    raise SystemExit(1)


# --- AgentGuard setup ---

here = os.path.dirname(os.path.abspath(__file__))
tracer = Tracer(
    sink=JsonlFileSink(os.path.join(here, "fastapi_traces.jsonl")),
    service="fastapi-agent",
)
budget = BudgetGuard(max_cost_usd=5.00, max_calls=1000)
loop_guard = LoopGuard(max_repeats=5)


# --- Fake agent (replace with real LLM call) ---

def fake_agent(question: str) -> str:
    """Simulate an agent that 'costs' a small amount per call."""
    budget.consume(calls=1, cost_usd=0.002)
    loop_guard.check(tool_name="agent", tool_args={"q": question})
    return f"Answer to: {question}"


# --- FastAPI app ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    # Flush traces on shutdown
    sink = getattr(tracer, "_sink", None)
    if hasattr(sink, "shutdown"):
        sink.shutdown()

app = FastAPI(title="AgentGuard Demo API", lifespan=lifespan)


@app.middleware("http")
async def agentguard_middleware(request: Request, call_next):
    """Wrap each request in an AgentGuard trace."""
    path = request.url.path
    with tracer.trace(f"http.{request.method} {path}") as ctx:
        ctx.event("request.start", data={
            "method": request.method,
            "path": path,
            "query": str(request.query_params),
        })
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except BudgetExceeded as e:
            ctx.event("guard.budget_exceeded", data={"error": str(e)})
            return JSONResponse(
                status_code=429,
                content={"error": "Budget exceeded"},
            )

        elapsed_ms = (time.perf_counter() - start) * 1000
        ctx.event("request.end", data={
            "status": response.status_code,
            "elapsed_ms": round(elapsed_ms, 1),
        })
    return response


@app.get("/ask")
async def ask(q: str = "What is AgentGuard?"):
    """Endpoint that runs a traced agent."""
    try:
        answer = fake_agent(q)
    except BudgetExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    return {"question": q, "answer": answer}


@app.get("/budget")
async def budget_status():
    """Check remaining budget."""
    return {
        "calls_used": budget.state.calls_used,
        "cost_used_usd": round(budget.state.cost_used, 4),
        "max_calls": budget.max_calls,
        "max_cost_usd": budget.max_cost_usd,
    }


if __name__ == "__main__":
    print("[agentguard] Budget: $5.00, 1000 calls max")
    print("[agentguard] Traces → fastapi_traces.jsonl")
    print("[agentguard] Try: curl http://localhost:8000/ask?q=hello")
    print("[agentguard]      curl http://localhost:8000/budget")
    uvicorn.run(app, host="0.0.0.0", port=8000)
