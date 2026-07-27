import os
from datetime import datetime, timezone
from typing import List, Optional

from session_memory.indexing.chunker import Chunk
from session_memory.retrieval.cross_searcher import search_all_workspaces as _search_all_workspaces
from session_memory.retrieval.searcher import search_workspace
from session_memory.store.workspace import resolve_workspace


def _parse_date_after(date_after: Optional[str]) -> Optional[float]:
    """Accepts an ISO-8601 timestamp (as the MCP tool's date_after argument
    would be passed) and converts it to the epoch float Chunk.timestamp
    uses internally."""
    if not date_after:
        return None
    try:
        return datetime.fromisoformat(date_after.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _format_result(chunk: Chunk, score: float, workspace: Optional[str] = None) -> dict:
    ts_iso = (
        datetime.fromtimestamp(chunk.timestamp, tz=timezone.utc).isoformat()
        if chunk.timestamp
        else None
    )
    result = {
        "text": chunk.text,
        "session_id": chunk.session_id,
        "turn_index": chunk.turn_index,
        "commit_hash": chunk.commit_hash,
        "timestamp": ts_iso,
        "score": round(score, 4),
    }
    if workspace is not None:
        result["workspace"] = workspace
    return result


def handle_search_conversation_log(
    query: str,
    top_k: int = 5,
    date_after: Optional[str] = None,
    cwd: Optional[str] = None,
) -> List[dict]:
    """
    Searches the calling repo's own `.conversation-memory/`. `cwd` defaults
    to this server process's own working directory; an assistant that
    tracks its own session cwd should pass it explicitly, since a stdio MCP
    server process's cwd doesn't necessarily follow the assistant around if
    the developer `cd`s elsewhere mid-session.
    """
    workspace = resolve_workspace(cwd or os.getcwd())
    if workspace is None:
        return []
    results = search_workspace(
        workspace.memory_dir, query, top_k=top_k, date_after=_parse_date_after(date_after)
    )
    return [_format_result(chunk, score) for chunk, score in results]


def handle_search_all_workspaces(
    query: str,
    top_k: int = 5,
    date_after: Optional[str] = None,
    workspaces: Optional[List[str]] = None,
) -> List[dict]:
    """Searches every registered workspace (or the id/name/tag subset in
    `workspaces`), labeling each result with its source workspace name."""
    results = _search_all_workspaces(
        query, top_k=top_k, date_after=_parse_date_after(date_after), workspaces=workspaces
    )
    return [_format_result(chunk, score, workspace=name) for name, chunk, score in results]
