import os
from typing import List, Tuple

import numpy as np

from session_memory.indexing.embedder import EMBEDDING_DIM


class FaissIndex:
    """
    Thin wrapper over a flat FAISS inner-product index (equivalent to
    cosine similarity, since embeddings are L2-normalized). New vectors can
    be appended incrementally without rebuilding — unlike BM25, dense
    vector indexes don't need corpus-wide recomputation on each addition.
    """

    def __init__(self, index_path: str):
        self.index_path = index_path
        self.index = self._load_or_create()

    def _load_or_create(self):
        import faiss

        if os.path.exists(self.index_path):
            return faiss.read_index(self.index_path)
        return faiss.IndexFlatIP(EMBEDDING_DIM)

    @classmethod
    def create_empty(cls, index_path: str) -> "FaissIndex":
        """Builds a fresh, empty index at `index_path` without attempting
        to load whatever (possibly corrupt) file is already there — used
        when a rebuild is required rather than a normal load."""
        import faiss

        instance = cls.__new__(cls)
        instance.index_path = index_path
        instance.index = faiss.IndexFlatIP(EMBEDDING_DIM)
        return instance

    def add(self, embeddings: np.ndarray) -> None:
        if embeddings.shape[0] == 0:
            return
        self.index.add(embeddings)

    def save(self) -> None:
        import faiss

        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)

    def search(self, query_embedding: np.ndarray, top_k: int) -> Tuple[List[int], List[float]]:
        """Returns (chunk positions, scores) ranked by descending similarity."""
        if self.index.ntotal == 0:
            return [], []
        k = min(top_k, self.index.ntotal)
        scores, indices = self.index.search(query_embedding.reshape(1, -1), k)
        return indices[0].tolist(), scores[0].tolist()

    @property
    def ntotal(self) -> int:
        return self.index.ntotal
