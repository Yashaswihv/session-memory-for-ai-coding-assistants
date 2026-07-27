import os
import pickle
from typing import List, Tuple

from session_memory.indexing.bm25_index import Bm25Index
from session_memory.indexing.chunker import Chunk
from session_memory.indexing.embedder import embed_texts
from session_memory.indexing.faiss_index import FaissIndex


def _load_chunks(chunks_path: str) -> List[Chunk]:
    if not os.path.exists(chunks_path):
        return []
    try:
        with open(chunks_path, "rb") as f:
            return pickle.load(f)
    except (pickle.PickleError, OSError, EOFError):
        return []


def _load_or_rebuild_faiss(faiss_path: str, chunks: List[Chunk]) -> FaissIndex:
    try:
        index = FaissIndex(faiss_path)
        if index.ntotal == len(chunks):
            return index
    except Exception:
        pass
    rebuilt = FaissIndex.create_empty(faiss_path)
    rebuilt.add(embed_texts([c.text for c in chunks]))
    rebuilt.save()
    return rebuilt


def _load_or_rebuild_bm25(bm25_path: str, chunks: List[Chunk]) -> Bm25Index:
    if os.path.exists(bm25_path):
        try:
            return Bm25Index.load(bm25_path)
        except Exception:
            pass
    rebuilt = Bm25Index.build([c.text for c in chunks])
    rebuilt.save(bm25_path)
    return rebuilt


def load_or_rebuild_indexes(
    chunks_path: str, faiss_path: str, bm25_path: str
) -> Tuple[List[Chunk], FaissIndex, Bm25Index]:
    """
    Loads a session's chunk/FAISS/BM25 triple, transparently rebuilding
    whichever index fails to load or has drifted out of sync with the
    chunk list (e.g. a binary index built with a different FAISS/library
    version on a teammate's machine) — the portable chunk list is the
    source of truth (paper section 4.1, "version-resilient sharing").
    Returns ([], ..., ...) with empty indexes if there's no chunk data at
    all for this session.
    """
    chunks = _load_chunks(chunks_path)
    if not chunks:
        return [], FaissIndex.create_empty(faiss_path), Bm25Index(None)

    faiss_index = _load_or_rebuild_faiss(faiss_path, chunks)
    bm25_index = _load_or_rebuild_bm25(bm25_path, chunks)
    return chunks, faiss_index, bm25_index
