from typing import List, Optional, Tuple

from session_memory.indexing.chunker import Chunk
from session_memory.indexing.embedder import embed_texts
from session_memory.registry.registry import Registry
from session_memory.retrieval.rrf import reciprocal_rank_fusion
from session_memory.retrieval.searcher import CANDIDATE_MULTIPLIER, collect_rankings


def search_all_workspaces(
    query: str,
    top_k: int = 5,
    date_after: Optional[float] = None,
    workspaces: Optional[List[str]] = None,
) -> List[Tuple[str, Chunk, float]]:
    """
    Fans out across every registered workspace (or the id/name/tag subset
    named in `workspaces`) and merges everything into one global top-K via
    a single RRF pass, each result labeled with its source workspace name.
    Default (workspaces=None) is every registered workspace — the agreed
    default for search_all_workspaces with no filter.
    """
    registry = Registry()
    entries = registry.list_workspaces()
    if workspaces:
        wanted = set(workspaces)
        entries = [
            e for e in entries
            if e.id in wanted or e.name in wanted or wanted.intersection(e.tags)
        ]

    memory_dir_to_name = {e.memory_dir: e.name for e in entries}
    if not memory_dir_to_name:
        return []

    candidate_k = top_k * CANDIDATE_MULTIPLIER
    query_embedding = embed_texts([query])[0]
    ranked_lists, chunk_lookup, source_dir = collect_rankings(
        list(memory_dir_to_name.keys()), query_embedding, query, candidate_k
    )
    fused = reciprocal_rank_fusion(ranked_lists)

    results: List[Tuple[str, Chunk, float]] = []
    for key, score in fused:
        chunk = chunk_lookup[key]
        if date_after is not None and chunk.timestamp < date_after:
            continue
        workspace_name = memory_dir_to_name[source_dir[key]]
        results.append((workspace_name, chunk, score))
        if len(results) >= top_k:
            break
    return results
