"""Build and query a per-repo ChromaDB collection."""
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from gitwise.config import EMBEDDING_MODEL, VECTOR_DB_DIR
from gitwise.core.chunker import Chunk, chunk_repo


def _get_client() -> chromadb.ClientAPI:
    VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(VECTOR_DB_DIR))


def _get_embedding_fn():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )


def build_index(repo_local_path: Path, collection_name: str) -> int:
    """Chunk the repo and (re)build its ChromaDB collection.

    Returns the number of chunks indexed.
    """
    client = _get_client()

    # Fresh start each time we (re)index this repo
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(
        name=collection_name,
        embedding_function=_get_embedding_fn(),
    )

    chunks: list[Chunk] = chunk_repo(repo_local_path)
    if not chunks:
        return 0

    # Chroma wants string ids, batch to keep things sane on huge repos
    batch_size = 200
    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        collection.add(
            ids=[f"{c.file_path}::{c.chunk_index}::{i}" for i, c in enumerate(batch, start)],
            documents=[c.text for c in batch],
            metadatas=[{"file_path": c.file_path, "chunk_index": c.chunk_index} for c in batch],
        )

    return len(chunks)


def collection_exists(collection_name: str) -> bool:
    client = _get_client()
    try:
        client.get_collection(collection_name, embedding_function=_get_embedding_fn())
        return True
    except Exception:
        return False


def query_index(collection_name: str, question: str, n_results: int = 6) -> list[dict]:
    """Returns top matching chunks as dicts with text + metadata."""
    client = _get_client()
    collection = client.get_collection(collection_name, embedding_function=_get_embedding_fn())

    results = collection.query(query_texts=[question], n_results=n_results)

    hits = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for doc, meta in zip(docs, metas):
        hits.append({"text": doc, "file_path": meta.get("file_path", "?")})
    return hits
