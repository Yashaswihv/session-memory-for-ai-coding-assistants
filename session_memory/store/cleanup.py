import glob
import os
import pickle
import re
from typing import List, Optional

from session_memory.indexing.bm25_index import Bm25Index
from session_memory.indexing.chunker import Chunk
from session_memory.indexing.embedder import embed_texts
from session_memory.indexing.faiss_index import FaissIndex
from session_memory.store.removed_turns import RemovedTurns

_TURN_BLOCK_RE = re.compile(r"## Turn (\d+) — .*?(?=\n## Turn \d+ — |\Z)", re.DOTALL)


def _find_session_base(memory_dir: str, session_id: str) -> Optional[str]:
    """Locates the raw session file base for `session_id` under
    `memory_dir`, including worktree subdirectories."""
    matches = glob.glob(
        os.path.join(memory_dir, "**", f"*_{session_id}.chunks.pkl"), recursive=True
    )
    matches = [m for m in matches if not m.endswith(".sanitized.chunks.pkl")]
    if not matches:
        return None
    return matches[0][: -len(".chunks.pkl")]


def _strip_turn_blocks_from_log(md_path: str, turn_indices: set) -> None:
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    def _strip(match: "re.Match") -> str:
        return "" if int(match.group(1)) in turn_indices else match.group(0)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(_TURN_BLOCK_RE.sub(_strip, content))


def remove_turns(memory_dir: str, session_id: str, turn_indices: List[int]) -> int:
    """
    Surgically removes the given turn indices from a session's log and
    index — for low-quality, sensitive, or superseded turns the developer
    wants gone from retrieval (the paper's cleanup mechanism; also the
    documented mitigation for stale/superseded turns, since automatic
    supersession detection isn't implemented). Rebuilds FAISS and BM25 from
    what remains and strips the matching "## Turn N — ..." block(s) from
    the raw markdown log. Returns the number of chunks actually removed.

    Re-running the session-end hook for this same session afterward won't
    resurrect the removed turn: `SessionState` keeps the markdown log
    shrunk (it tracks how many turns were extracted from the transcript,
    not how many currently exist in the log), and the removed indices are
    recorded in `RemovedTurns` so `SessionIndex` — which deliberately
    derives its progress from the persisted chunks rather than
    `SessionState` — knows not to re-index them on the next capture.
    """
    base = _find_session_base(memory_dir, session_id)
    if base is None:
        return 0

    chunks_path = base + ".chunks.pkl"
    if not os.path.exists(chunks_path):
        return 0
    with open(chunks_path, "rb") as f:
        chunks: List[Chunk] = pickle.load(f)

    turn_indices_set = set(turn_indices)
    present = {c.turn_index for c in chunks}
    removed_indices = present & turn_indices_set
    kept = [c for c in chunks if c.turn_index not in removed_indices]
    removed_count = len(chunks) - len(kept)
    if removed_count == 0:
        return 0

    with open(chunks_path, "wb") as f:
        pickle.dump(kept, f)

    RemovedTurns(memory_dir).record_removed(session_id, removed_indices)

    faiss_index = FaissIndex.create_empty(base + ".faiss")
    if kept:
        faiss_index.add(embed_texts([c.text for c in kept]))
    faiss_index.save()

    bm25_index = Bm25Index.build([c.text for c in kept])
    bm25_index.save(base + ".bm25.pkl")

    md_path = base + ".md"
    if os.path.exists(md_path):
        _strip_turn_blocks_from_log(md_path, turn_indices_set)

    return removed_count
