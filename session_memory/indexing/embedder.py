from typing import List

import numpy as np

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Encodes `texts` with all-MiniLM-L6-v2, L2-normalized so that inner
    product (used by the FAISS index) is equivalent to cosine similarity.
    """
    if not texts:
        return np.zeros((0, EMBEDDING_DIM), dtype="float32")
    model = _get_model()
    embeddings = model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings.astype("float32")
