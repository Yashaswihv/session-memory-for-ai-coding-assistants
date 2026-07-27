from collections import Counter
from typing import Iterable


def merge_counts(counts_list: Iterable[Counter]) -> Counter:
    total: Counter = Counter()
    for counts in counts_list:
        total.update(counts)
    return total


def format_report(counts: Counter, session_count: int) -> str:
    """Human-readable report for the developer to review before sharing —
    labels and counts only, never the matched text itself."""
    if not counts:
        return f"No redaction matches across {session_count} session file(s)."
    lines = [f"Redaction report across {session_count} session file(s):"]
    for label, count in sorted(counts.items()):
        lines.append(f"  {label}: {count} match(es)")
    lines.append("Review the matches above before sharing the sanitized files.")
    return "\n".join(lines)
