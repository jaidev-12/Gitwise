"""Shared state passed between nodes in the chat graph."""
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ChatState(TypedDict):
    # Full conversation history. `add_messages` appends rather than overwrites,
    # and the SqliteSaver checkpoints this after every node run.
    messages: Annotated[list[BaseMessage], add_messages]

    repo: str                    # which Chroma collection / repo this thread is about
    standalone_question: str     # this turn's question, rewritten to be self-contained
    retrieved_chunks: list[dict] # hybrid retrieval hits for this turn
