"""Run the same real LangChain tool against either installed SDK version."""
import importlib.metadata
import json
import sys

if len(sys.argv) > 1:
    sys.path.insert(0, sys.argv[1])

from agentguard import BudgetExceeded, BudgetGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler
from langchain_core.tools import tool

executed = []

@tool
def search_docs(query: str) -> str:
    """Search a local sample. No network or model calls."""
    executed.append(query)
    return "Local sample result"

handler = AgentGuardCallbackHandler(budget_guard=BudgetGuard(max_calls=0))
try:
    search_docs.invoke({"query": "billing docs"}, config={"callbacks": [handler]})
    result = "Tool ran despite zero-call budget"
except BudgetExceeded:
    result = "BudgetExceeded: tool stopped before execution"

print(json.dumps({"version": importlib.metadata.version("agentguard47"),
                  "budget_calls": 0, "tool_executions": len(executed),
                  "result": result}, indent=2))
