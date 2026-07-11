"""The conversational RAG graph: rewrite -> retrieve -> generate.

Why a graph instead of the old one-shot `_ask_and_print` loop:
- `messages` accumulates across turns and is checkpointed to SQLite, so a
  follow-up like "what does that function call?" has real history to resolve
  against instead of being answered in a vacuum.
- Splitting rewrite/retrieve/generate into separate nodes makes each step
  independently testable and swappable (e.g. add a reranker node later
  without touching the others).
"""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from gitwise.config import MAX_HISTORY_MESSAGES
from gitwise.core.llm import SYSTEM_PROMPT, build_context_block, get_chat_llm
from gitwise.core.retriever import hybrid_query
from gitwise.graph.state import ChatState
from gitwise.memory.checkpointer import get_checkpointer

_REWRITE_PROMPT = (
    "Given the conversation so far and a follow-up question, rewrite the "
    "follow-up into a standalone question that makes sense without the chat "
    "history. If the follow-up is already standalone, return it unchanged. "
    "Only output the rewritten question, nothing else."
)


def _rewrite_question(state: ChatState) -> dict:
    history = state["messages"][:-1]  # everything except the new question
    latest = state["messages"][-1].content

    if not history:
        # First turn in the thread — nothing to disambiguate against.
        return {"standalone_question": latest}

    llm = get_chat_llm()
    windowed = history[-MAX_HISTORY_MESSAGES:]
    prompt = [SystemMessage(content=_REWRITE_PROMPT), *windowed, HumanMessage(content=latest)]
    rewritten = llm.invoke(prompt).content.strip()
    return {"standalone_question": rewritten or latest}


def _retrieve(state: ChatState) -> dict:
    hits = hybrid_query(state["repo"], state["standalone_question"], n_results=6)
    return {"retrieved_chunks": hits}


def _generate(state: ChatState) -> dict:
    llm = get_chat_llm()
    context = build_context_block(state["retrieved_chunks"])
    history = state["messages"][:-1][-MAX_HISTORY_MESSAGES:]
    latest_question = state["messages"][-1].content

    user_turn = f"Context:\n{context}\n\nQuestion:\n{latest_question}"
    prompt = [SystemMessage(content=SYSTEM_PROMPT), *history, HumanMessage(content=user_turn)]

    response = llm.invoke(prompt)
    return {"messages": [AIMessage(content=response.content)]}


def build_chat_graph():
    """Compile the graph once with a persistent SQLite checkpointer attached."""
    graph = StateGraph(ChatState)
    graph.add_node("rewrite", _rewrite_question)
    graph.add_node("retrieve", _retrieve)
    graph.add_node("generate", _generate)

    graph.set_entry_point("rewrite")
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile(checkpointer=get_checkpointer())
