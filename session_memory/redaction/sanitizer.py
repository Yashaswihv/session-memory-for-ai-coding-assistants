from collections import Counter
from typing import List, Optional, Tuple

from session_memory.redaction.patterns import DEFAULT_PATTERNS, RedactionPattern


def sanitize_text(
    text: str, extra_patterns: Optional[List[RedactionPattern]] = None
) -> Tuple[str, Counter]:
    """
    Applies redaction patterns to `text`, replacing each match with
    `[REDACTED:<label>]`. Returns (sanitized_text, {label: count}) — the
    count is reported, the matched substring never is (paper section 3.3:
    "reports what it matched... never echoing the secret").
    """
    patterns = list(DEFAULT_PATTERNS) + list(extra_patterns or [])

    all_matches: List[Tuple[int, int, str]] = []
    for pattern in patterns:
        for start, end in pattern.finder(text):
            all_matches.append((start, end, pattern.label))

    if not all_matches:
        return text, Counter()

    # Resolve overlaps: earliest start first, and the longest match at a
    # given position wins (so e.g. a bearer-token match isn't split by a
    # high-entropy-string match landing on the same token).
    all_matches.sort(key=lambda m: (m[0], -(m[1] - m[0])))
    selected: List[Tuple[int, int, str]] = []
    last_end = -1
    for start, end, label in all_matches:
        if start >= last_end:
            selected.append((start, end, label))
            last_end = end

    counts: Counter = Counter()
    pieces = []
    cursor = 0
    for start, end, label in selected:
        pieces.append(text[cursor:start])
        pieces.append(f"[REDACTED:{label}]")
        counts[label] += 1
        cursor = end
    pieces.append(text[cursor:])
    return "".join(pieces), counts
