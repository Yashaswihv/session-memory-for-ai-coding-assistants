import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Callable, List, Tuple

Span = Tuple[int, int]


@dataclass
class RedactionPattern:
    label: str
    finder: Callable[[str], List[Span]]

    @classmethod
    def from_regex(cls, label: str, regex: "re.Pattern") -> "RedactionPattern":
        return cls(label, lambda text: [(m.start(), m.end()) for m in regex.finditer(text)])


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


_HIGH_ENTROPY_TOKEN_RE = re.compile(r"[A-Za-z0-9+/_-]{24,}")
HIGH_ENTROPY_THRESHOLD_BITS_PER_CHAR = 4.3


def _find_high_entropy_strings(text: str) -> List[Span]:
    """
    Flags long tokens whose character distribution looks close to uniformly
    random (Shannon entropy above threshold) — a heuristic for unlabeled
    secrets that don't match a known key/token format. This is deliberately
    imperfect: hex hashes, commit ids, and other benign identifiers can
    have entropy in the same range as a real secret. The paper is explicit
    that pattern-based redaction has both false negatives and false
    positives and the review step exists precisely because of that — this
    is not meant to be a guarantee, just a heuristic backstop.
    """
    matches = []
    for m in _HIGH_ENTROPY_TOKEN_RE.finditer(text):
        if _shannon_entropy(m.group(0)) >= HIGH_ENTROPY_THRESHOLD_BITS_PER_CHAR:
            matches.append((m.start(), m.end()))
    return matches


DEFAULT_PATTERNS: List[RedactionPattern] = [
    RedactionPattern.from_regex(
        "api_key",
        re.compile(r"\b(?:sk|pk|api|key)[-_][A-Za-z0-9]{16,}\b", re.IGNORECASE),
    ),
    RedactionPattern.from_regex(
        "bearer_token",
        re.compile(r"\bBearer\s+[A-Za-z0-9\-_.]{16,}"),
    ),
    RedactionPattern.from_regex(
        "email",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
    RedactionPattern.from_regex(
        "internal_hostname",
        re.compile(r"\b[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*\.(?:internal|corp|local)\b", re.IGNORECASE),
    ),
    RedactionPattern("high_entropy_string", _find_high_entropy_strings),
]
