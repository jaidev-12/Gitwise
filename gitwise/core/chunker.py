"""Walk a repo, pick relevant files, and split them into overlapping chunks."""
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from gitwise.config import (
    CHUNK_OVERLAP_CHARS,
    CHUNK_SIZE_CHARS,
    IGNORE_DIRS,
    MAX_FILE_SIZE_BYTES,
    MAX_FILES_TO_INDEX,
    SOURCE_EXTENSIONS,
)


@dataclass
class Chunk:
    text: str
    file_path: str  # relative path, used for citations
    chunk_index: int


def _iter_candidate_files(repo_path: Path) -> Iterator[Path]:
    count = 0
    for path in repo_path.rglob("*"):
        if count >= MAX_FILES_TO_INDEX:
            return
        if not path.is_file():
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue
        try:
            if path.stat().st_size > MAX_FILE_SIZE_BYTES:
                continue
        except OSError:
            continue
        count += 1
        yield path


def _split_text(text: str, size: int, overlap: int) -> list[str]:
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start = end - overlap
    return chunks


def chunk_repo(repo_path: Path) -> list[Chunk]:
    """Returns all chunks across all relevant files in the repo."""
    chunks: list[Chunk] = []
    for file_path in _iter_candidate_files(repo_path):
        try:
            text = file_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        if not text.strip():
            continue

        rel_path = str(file_path.relative_to(repo_path))
        pieces = _split_text(text, CHUNK_SIZE_CHARS, CHUNK_OVERLAP_CHARS)
        for i, piece in enumerate(pieces):
            chunks.append(Chunk(text=piece, file_path=rel_path, chunk_index=i))

    return chunks
