import os
import pickle
from typing import List

from session_memory.capture.transcript_reader import Turn
from session_memory.indexing.bm25_index import Bm25Index
from session_memory.indexing.chunker import Chunk, chunk_turns
from session_memory.indexing.embedder import embed_texts
from session_memory.indexing.faiss_index import FaissIndex
from session_memory.store.removed_turns import RemovedTurns


class SessionIndex:
    """
    Owns one session's paired index files —
    conversation_log_<commit>_<session>.{faiss,bm25.pkl,chunks.pkl} — and
    keeps them in sync as new turns are captured. This is what the
    session-end hook calls right after LogWriter, giving "incremental index
    maintenance" (paper section 3.4): new chunks are embedded and appended
    to FAISS, and the BM25 index is rebuilt from the full accumulated chunk
    set (BM25 is corpus-level; a partial append would leave its IDF weights
    stale).

    Tracks its own "how many turns already indexed" progress from the
    persisted chunk list rather than trusting a pre-sliced turn list from
    the caller, so it stays independently resumable even if a prior run
    was interrupted after LogWriter advanced its own cursor but before
    indexing finished.
    """

    def __init__(self, memory_dir: str, commit_hash: str, session_id: str):
        base = os.path.join(memory_dir, f"conversation_log_{commit_hash}_{session_id}")
        self.memory_dir = memory_dir
        self.session_id = session_id
        self.faiss_path = base + ".faiss"
        self.bm25_path = base + ".bm25.pkl"
        self.chunks_path = base + ".chunks.pkl"

        self.chunks: List[Chunk] = self._load_chunks()
        self.faiss_index = FaissIndex(self.faiss_path)

    def _load_chunks(self) -> List[Chunk]:
        if not os.path.exists(self.chunks_path):
            return []
        try:
            with open(self.chunks_path, "rb") as f:
                return pickle.load(f)
        except (pickle.PickleError, OSError, EOFError):
            return []

    def _turns_already_indexed(self) -> int:
        """How many leading turns (by turn_index) are already reflected in
        the persisted chunks. Deliberately independent of LogWriter's own
        SessionState: if the hook process is killed between LogWriter
        advancing its cursor and this class finishing its write (observed
        in practice -- claude -p's SessionEnd hook can time out mid-index),
        LogWriter's bookkeeping would otherwise say "nothing new" forever
        and the index would never catch up. Tracking progress from what's
        actually on disk here means a retry can always detect and repair
        the gap regardless of what LogWriter thinks happened."""
        if not self.chunks:
            return 0
        return max(c.turn_index for c in self.chunks) + 1

    def add_turns(self, all_turns: List[Turn]) -> List[Chunk]:
        """
        Chunks, embeds, and indexes whatever turns in `all_turns` aren't
        already reflected in the persisted chunk list. Callers should pass
        the FULL ordered turn list for this session each time (not a
        pre-sliced "new turns" subset) so this can independently determine
        what's missing.

        Turns recorded in `RemovedTurns` by `session-memory cleanup` are
        never (re-)indexed, even though "not reflected in the persisted
        chunk list" would otherwise include them — deriving progress purely
        from the chunks on disk cannot distinguish "developer deleted this"
        from "never indexed yet".
        """
        already_indexed = self._turns_already_indexed()
        removed = RemovedTurns(self.memory_dir).removed(self.session_id)
        new_turns = [
            turn for turn in all_turns[already_indexed:]
            if turn.turn_index not in removed
        ]
        new_chunks = chunk_turns(new_turns)
        if not new_chunks:
            return []

        os.makedirs(self.memory_dir, exist_ok=True)

        embeddings = embed_texts([c.text for c in new_chunks])
        self.faiss_index.add(embeddings)
        self.faiss_index.save()

        self.chunks.extend(new_chunks)
        with open(self.chunks_path, "wb") as f:
            pickle.dump(self.chunks, f)

        bm25 = Bm25Index.build([c.text for c in self.chunks])
        bm25.save(self.bm25_path)

        return new_chunks
