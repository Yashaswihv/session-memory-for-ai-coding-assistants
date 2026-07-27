from typing import Dict, List, Tuple, TypeVar

T = TypeVar("T")

RRF_K = 60


def reciprocal_rank_fusion(ranked_lists: List[List[T]], k: int = RRF_K) -> List[Tuple[T, float]]:
    """
    Merges multiple ranked lists of the same item type via Reciprocal Rank
    Fusion: score(d) = sum over lists of 1/(k + rank(d)), where rank is
    1-based (paper section 3.4). Returns (item, score) pairs sorted by
    descending score. An item absent from a list simply contributes 0 for
    that list.
    """
    scores: Dict[T, float] = {}
    for ranked_list in ranked_lists:
        for rank, item in enumerate(ranked_list, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda pair: pair[1], reverse=True)
