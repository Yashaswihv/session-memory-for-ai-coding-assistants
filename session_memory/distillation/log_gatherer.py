import os
from typing import Optional

from session_memory.retrieval.searcher import find_raw_session_bases


def gather_session_logs(memory_dir: str, since: Optional[float] = None) -> str:
    """
    Concatenates every raw session's markdown log under `memory_dir`
    (including worktree subdirectories) into one text blob, for an
    assistant to read and distill into AGENTS.md's `<!-- DYNAMIC -->`
    section. `since` (an epoch timestamp) restricts to logs modified after
    that time, so a repeat distillation pass can focus on what's
    accumulated since the last one rather than always re-reading
    everything.
    """
    bases = find_raw_session_bases(memory_dir)
    parts = []
    for base in sorted(bases):
        md_path = base + ".md"
        if not os.path.exists(md_path):
            continue
        if since is not None and os.path.getmtime(md_path) < since:
            continue
        with open(md_path, "r", encoding="utf-8") as f:
            parts.append(f.read())
    return "\n\n".join(parts)
