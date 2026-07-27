import glob
import os
from typing import Dict, List, Optional, Tuple

import numpy as np

from session_memory.indexing.chunker import Chunk
from session_memory.indexing.embedder import embed_texts
from session_memory.retrieval.fallback import load_or_rebuild_indexes
from session_memory.retrieval.rrf import reciprocal_rank_fusion

CANDIDATE_MULTIPLIER = 4


SANITIZED_CHUNKS_SUFFIX = ".sanitized.chunks.pkl"


def find_raw_session_bases(memory_dir: str) -> List[str]:
    """Every genuinely raw (non-sanitized) session base under `memory_dir`,
    including worktree subdirectories. Used by the sanitize command, which
    only ever operates on raw logs."""
    chunk_paths = glob.glob(os.path.join(memory_dir, "**", "*.chunks.pkl"), recursive=True)
    return sorted(
        p[: -len(".chunks.pkl")] for p in chunk_paths if not p.endswith(SANITIZED_CHUNKS_SUFFIX)
    )


def find_session_bases(memory_dir: str) -> List[str]:
    """
    One base path per session under `memory_dir` (including worktree
    subdirectories) for search purposes: the raw session base if present,
    otherwise its sanitized twin as a fallback. Once `sanitize` has run,
    both `conversation_log_X.chunks.pkl` and
    `conversation_log_X.sanitized.chunks.pkl` exist side by side on the
    author's own machine — treating them as two separate sessions would
    duplicate every search result. The paper is explicit that retrieval
    "uses a session's raw index when present... falls back to the
    sanitized index when only that exists... so both see a single,
    non-duplicated view" (section 3.4) — sanitized is a substitute for a
    missing raw log (a teammate's clone), never an addition to it.
    """
    chunk_paths = glob.glob(os.path.join(memory_dir, "**", "*.chunks.pkl"), recursive=True)
    raw_bases = set()
    sanitized_bases = set()
    for path in chunk_paths:
        if path.endswith(SANITIZED_CHUNKS_SUFFIX):
            sanitized_bases.add(path[: -len(SANITIZED_CHUNKS_SUFFIX)])
        else:
            raw_bases.add(path[: -len(".chunks.pkl")])

    bases = list(raw_bases)
    bases.extend(base + ".sanitized" for base in sanitized_bases - raw_bases)
    return sorted(bases)


def collect_rankings(
    memory_dirs: List[str], query_embedding: np.ndarray, query: str, candidate_k: int
) -> Tuple[List[List[str]], Dict[str, Chunk], Dict[str, str]]:
    """
    Globs every session's index triple under each of `memory_dirs` and
    searches each pair independently. Returns one ranked list PER SESSION
    PER RETRIEVAL METHOD — each session contributes its own dense ranking
    and its own sparse ranking as *separate* lists, never concatenated into
    one flat list. Concatenating would conflate "rank within this
    session's own search" with "position across all sessions combined",
    systematically penalizing every session searched after the first
    regardless of actual relevance. RRF is designed to merge exactly this
    kind of list-of-independent-rankings, which is what makes "no
    pre-aggregation needed... each developer's session files are searched
    as peers" (paper section 3.4) actually true.

    Keys are `<session base path>::<chunk_id>`, not the bare chunk_id:
    chunk_id (session_id:turn_index:chunk_index) is only unique within one
    session's own files, and session_ids are not guaranteed unique across
    workspaces — two independent repos could easily collide. The session's
    file path is always unique, so prefixing with it prevents chunks from
    different sessions/workspaces from silently overwriting each other in
    `chunk_lookup` during cross-workspace search.
    """
    ranked_lists: List[List[str]] = []
    chunk_lookup: Dict[str, Chunk] = {}
    source_dir: Dict[str, str] = {}

    for memory_dir in memory_dirs:
        for base in find_session_bases(memory_dir):
            chunks, faiss_index, bm25_index = load_or_rebuild_indexes(
                base + ".chunks.pkl", base + ".faiss", base + ".bm25.pkl"
            )
            if not chunks:
                continue

            def _key(position: int, _base=base) -> str:
                return f"{_base}::{chunks[position].chunk_id}"

            for position, chunk in enumerate(chunks):
                key = _key(position)
                chunk_lookup[key] = chunk
                source_dir[key] = memory_dir

            positions, _ = faiss_index.search(query_embedding, candidate_k)
            if positions:
                ranked_lists.append([_key(p) for p in positions])

            bm25_results = bm25_index.search(query, candidate_k)
            if bm25_results:
                ranked_lists.append([_key(p) for p, _ in bm25_results])

    return ranked_lists, chunk_lookup, source_dir


def search_workspace(
    memory_dir: str, query: str, top_k: int = 5, date_after: Optional[float] = None
) -> List[Tuple[Chunk, float]]:
    """
    Searches every session under a single workspace's
    `.conversation-memory/` (including worktree subdirectories) and merges
    results via RRF into one top-K (paper section 3.4).
    """
    candidate_k = top_k * CANDIDATE_MULTIPLIER
    query_embedding = embed_texts([query])[0]
    ranked_lists, chunk_lookup, _ = collect_rankings(
        [memory_dir], query_embedding, query, candidate_k
    )
    fused = reciprocal_rank_fusion(ranked_lists)

    results: List[Tuple[Chunk, float]] = []
    for key, score in fused:
        chunk = chunk_lookup[key]
        if date_after is not None and chunk.timestamp < date_after:
            continue
        results.append((chunk, score))
        if len(results) >= top_k:
            break
    return results
