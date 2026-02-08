"""
AgentGuard + LangChain RAG Pipeline with Runtime Guards

This example shows how to add loop detection and budget enforcement
to a LangChain RAG agent. If the agent enters a loop or exceeds
its cost budget, AgentGuard stops it immediately.

Requirements:
    pip install agentguard47[langchain] langchain langchain-openai chromadb

Usage:
    export OPENAI_API_KEY=sk-...
    python langchain_rag_with_guards.py
"""

import os

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.tools.retriever import create_retriever_tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from agentguard import Tracer, LoopGuard, BudgetGuard, JsonlFileSink
from agentguard.integrations.langchain import AgentGuardCallbackHandler

# --- 1. Set up AgentGuard ---

tracer = Tracer(
    sink=JsonlFileSink("traces.jsonl"),
    service="rag-agent",
)
loop_guard = LoopGuard(max_repeats=3, window=6)
budget_guard = BudgetGuard(max_cost_usd=2.00, max_calls=50)

handler = AgentGuardCallbackHandler(
    tracer=tracer,
    loop_guard=loop_guard,
    budget_guard=budget_guard,
)

# --- 2. Build a simple RAG pipeline ---

# Sample documents (replace with your own data)
docs = [
    Document(page_content="AgentGuard is a zero-dependency Python SDK for AI agent observability."),
    Document(page_content="LoopGuard detects repeated tool calls and stops runaway agents."),
    Document(page_content="BudgetGuard enforces cost limits per agent run."),
    Document(page_content="The dashboard shows Gantt timelines, alerts, and usage metrics."),
]

embeddings = OpenAIEmbeddings()
vectorstore = Chroma.from_documents(docs, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

retriever_tool = create_retriever_tool(
    retriever,
    name="search_docs",
    description="Search the documentation for information about AgentGuard.",
)

# --- 3. Create the agent ---

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Use the search_docs tool to answer questions."),
    MessagesPlaceholder("chat_history", optional=True),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),
])

agent = create_openai_tools_agent(llm, [retriever_tool], prompt)
executor = AgentExecutor(agent=agent, tools=[retriever_tool], verbose=True)

# --- 4. Run with AgentGuard watching ---

if __name__ == "__main__":
    try:
        result = executor.invoke(
            {"input": "What does AgentGuard do and how does it detect loops?"},
            config={"callbacks": [handler]},
        )
        print("\nAnswer:", result["output"])
    except Exception as e:
        print(f"\nAgent stopped: {e}")

    # Check what happened
    print(f"\nBudget used: ${budget_guard.state.cost_used:.4f}")
    print(f"API calls: {budget_guard.state.calls_used}")
    print("Traces saved to traces.jsonl")
