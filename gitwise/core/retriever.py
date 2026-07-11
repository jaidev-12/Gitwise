"""Hybrid retrieval: ChromaDB vector search + BM25 keyword search, fused with RRF.

Pure vector similarity misses exact-match cases that matter a lot for code
(function names, error strings, config keys). BM25 catches those. Reciprocal
Rank Fusion combines the two rankings without needing to normalize incomparable
similarity scores.
"""
from functools import lru_cache

from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from gitwise.config import BM25_TOP_K, RRF_K, VECTOR_TOP_K
from gitwise.core.indexer import _get_client, _get_embedding_fn


@lru_cache(maxsize=8)
def _load_bm25_retriever(collection_name: str) -> BM25Retriever:
    """Build (and cache) a BM25 retriever from every chunk in a collection.

    Cached per collection_name for the process lifetime of the CLI — repos
    don't change mid-session, so re-fetching every query would be wasted work.
    """
    client = _get_client()
    collection = client.get_collection(collection_name, embedding_function=_get_embedding_fn())
    data = collection.get(include=["documents", "metadatas"])

    docs = [
        Document(page_content=text, metadata=meta)
        for text, meta in zip(data["documents"], data["metadatas"])
    ]
    retriever = BM25Retriever.from_documents(docs)
    retriever.k = BM25_TOP_K
    return retriever


def _vector_search(collection_name: str, question: str, k: int) -> list[dict]:
    client = _get_client()
    collection = client.get_collection(collection_name, embedding_function=_get_embedding_fn())
    results = collection.query(query_texts=[question], n_results=k)

    hits = []
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    for doc, meta in zip(docs, metas):
        hits.append({"text": doc, "file_path": meta.get("file_path", "?")})
    return hits


def _bm25_search(collection_name: str, question: str) -> list[dict]:
    retriever = _load_bm25_retriever(collection_name)
    docs = retriever.invoke(question)
    return [{"text": d.page_content, "file_path": d.metadata.get("file_path", "?")} for d in docs]


def _rrf_key(hit: dict) -> str:
    """A stable identity for a chunk, used to merge duplicate hits across rankings."""
    return f"{hit['file_path']}::{hash(hit['text'])}"


def hybrid_query(collection_name: str, question: str, n_results: int = 6) -> list[dict]:
    """Retrieve top chunks using vector + keyword search fused via RRF.

    Falls back to vector-only results if BM25 indexing fails for any reason
    (e.g. an empty collection), so this is a safe drop-in replacement for the
    old `query_index`.
    """
    vector_hits = _vector_search(collection_name, question, VECTOR_TOP_K)

    try:
        bm25_hits = _bm25_search(collection_name, question)
    except Exception:
        bm25_hits = []

    if not bm25_hits:
        return vector_hits[:n_results]

    scores: dict[str, float] = {}
    chunk_by_key: dict[str, dict] = {}

    for rank, hit in enumerate(vector_hits):
        key = _rrf_key(hit)
        chunk_by_key[key] = hit
        scores[key] = scores.get(key, 0.0) + 1.0 / (RRF_K + rank + 1)

    for rank, hit in enumerate(bm25_hits):
        key = _rrf_key(hit)
        chunk_by_key[key] = hit
        scores[key] = scores.get(key, 0.0) + 1.0 / (RRF_K + rank + 1)

    ranked_keys = sorted(scores, key=lambda k: scores[k], reverse=True)
    return [chunk_by_key[k] for k in ranked_keys[:n_results]]
