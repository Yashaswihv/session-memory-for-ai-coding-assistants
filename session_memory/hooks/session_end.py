from datetime import datetime, timezone
from typing import List, Optional

from session_memory.capture.reader_factory import ReaderFactory
from session_memory.capture.transcript_reader import Turn
from session_memory.indexing.session_index import SessionIndex
from session_memory.registry.registry import Registry
from session_memory.store.log_writer import LogWriter
from session_memory.store.workspace import resolve_workspace


def run_session_end(
    cwd: str,
    session_id: str,
    transcript_path: str,
    assistant: Optional[str] = None,
) -> List[Turn]:
    """
    Session-end lifecycle hook: reads the on-disk transcript (bypassing
    whatever in-memory truncation the assistant applies), extracts clean
    turn pairs, appends only the new ones to this session's log, indexes
    them incrementally (FAISS + BM25), and records the session in the
    global registry.

    `assistant` should be supplied by whatever wires this hook into a given
    CLI's lifecycle (each assistant knows its own name); if omitted, the
    reader is auto-detected from the transcript's own schema.

    Returns the newly-written turns — empty if the workspace hasn't opted
    in (no `.conversation-memory/` reachable) or there was nothing new to
    write (re-entrant: safe to call more than once for the same session).
    """
    workspace = resolve_workspace(cwd)
    if workspace is None:
        return []

    reader = (
        ReaderFactory.get_reader(assistant)
        if assistant
        else ReaderFactory.detect_and_get_reader(transcript_path)
    )
    turns = reader.parse_transcript(
        transcript_path, session_id=session_id, commit_hash=workspace.commit_hash
    )

    writer = LogWriter(workspace.memory_dir, workspace.commit_hash, session_id)
    new_turns = writer.append_new_turns(turns)

    # SessionIndex tracks its own "already indexed" progress independently
    # of LogWriter's cursor (see SessionIndex._turns_already_indexed), so
    # the full turn list is passed every time rather than just the
    # newly-written slice. This lets indexing self-heal if a prior
    # invocation wrote the log but was killed before indexing finished --
    # a real failure mode observed with hook execution timeouts.
    index = SessionIndex(workspace.memory_dir, workspace.commit_hash, session_id)
    index.add_turns(turns)

    registry = Registry()
    entry = registry.get_by_path(workspace.root)
    if entry is not None:
        registry.record_session(
            entry.id,
            assistant or "unknown",
            datetime.now(timezone.utc).isoformat(),
        )

    return new_turns
