"""Persistent conversation memory, backed by a local SQLite file.

Each chat thread (identified by thread_id) gets its full message history
checkpointed after every turn. Because it's a real file on disk, memory
survives process restarts — closing and reopening `gitwise chat --repo X`
picks the conversation back up.
"""
from langgraph.checkpoint.sqlite import SqliteSaver

from gitwise.config import MEMORY_DB_PATH

_saver_cm = None
_saver = None


def get_checkpointer() -> SqliteSaver:
    """Returns a process-wide SqliteSaver, creating the DB file on first use."""
    global _saver_cm, _saver
    if _saver is None:
        MEMORY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _saver_cm = SqliteSaver.from_conn_string(str(MEMORY_DB_PATH))
        _saver = _saver_cm.__enter__()
    return _saver


def thread_id_for(repo: str, session: str = "default") -> str:
    """Deterministic thread id so the same --repo resumes the same conversation."""
    return f"{repo}::{session}"
