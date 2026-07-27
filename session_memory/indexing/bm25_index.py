import pickle
import re
from typing import List, Optional, Tuple

_TOKEN_RE = re.compile(r"[a-zA-Z0-9_\-\.]+")


def _tokenize(text: str) -> List[str]:
    """
    Preserves snake_case identifiers and dotted paths as single tokens
    (e.g. "payment_service_v2_retry_budget", "log_writer.py"), rather than
    the whitespace splitting BM25 implementations default to — this is the
    tokenizer the paper's hybrid retrieval relies on for exact-identifier
    recall (section 3.4).
    """
    return _TOKEN_RE.findall(text.lower())


class Bm25Index:
    """
    Wraps rank_bm25's BM25Okapi. BM25 is a corpus-level model — its IDF
    weights depend on the whole corpus, so unlike the FAISS index this is
    always rebuilt from every chunk on each update rather than appended to
    (paper section 3.4).
    """

    def __init__(self, bm25):
        self._bm25 = bm25

    @classmethod
    def build(cls, texts: List[str]) -> "Bm25Index":
        if not texts:
            return cls(None)
        from rank_bm25 import BM25Okapi

        tokenized = [_tokenize(t) for t in texts]
        return cls(BM25Okapi(tokenized))

    def save(self, path: str) -> None:
        with open(path, "wb") as f:
            pickle.dump(self._bm25, f)

    @classmethod
    def load(cls, path: str) -> "Bm25Index":
        with open(path, "rb") as f:
            bm25 = pickle.load(f)
        return cls(bm25)

    def search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        """Returns (chunk position, score) pairs ranked by descending BM25 score."""
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda pair: pair[1], reverse=True)
        return ranked[:top_k]
