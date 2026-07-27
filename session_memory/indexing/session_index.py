import os
import pickle
from typing import List

from session_memory.capture.transcript_reader import Turn
from session_memory.indexing.bm25_index import Bm25Index
from session_memory.indexing.chunker import Chunk, chunk_turns
from session_memory.indexing.embedder import embed_texts
from session_memory.indexing.faiss_index import FaissIndex


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
    """

    def __init__(self, memory_dir: str, commit_hash: str, session_id: str):
        base = os.path.join(memory_dir, f"conversation_log_{commit_hash}_{session_id}")
        self.memory_dir = memory_dir
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

    def add_turns(self, new_turns: List[Turn]) -> List[Chunk]:
        """Chunks, embeds, and indexes `new_turns` (already-new turns from
        LogWriter — this does not itself deduplicate against prior calls)."""
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
