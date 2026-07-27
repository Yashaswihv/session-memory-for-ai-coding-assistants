import os
import re
from dataclasses import dataclass
from typing import List, Optional

from session_memory.capture.transcript_reader import Turn

# A turn's combined text longer than this is split into overlapping windows
# rather than truncated, so content near the end of a long turn stays
# reachable from a query (paper section 3.4, "Turn chunking").
TURN_SPLIT_THRESHOLD = 2000
WINDOW_SIZE = 2000
WINDOW_OVERLAP = 200

_DIFF_FENCE_RE = re.compile(r"```diff\n.*?```", re.DOTALL)
_UNIFIED_DIFF_HUNK_RE = re.compile(
    r"--- .+\n\+\+\+ .+\n(?:@@.*@@\n(?:[-+ ].*\n?)*)+", re.MULTILINE
)


@dataclass
class Chunk:
    text: str
    session_id: str
    turn_index: int
    chunk_index: int
    timestamp: float
    commit_hash: str

    @property
    def chunk_id(self) -> str:
        return f"{self.session_id}:{self.turn_index}:{self.chunk_index}"


def _extract_diff_filename(diff_text: str) -> Optional[str]:
    match = re.search(r"^\+\+\+ b?/?(.+)$", diff_text, re.MULTILINE)
    if match:
        return os.path.basename(match.group(1).strip())
    return None


def _strip_diff_blocks(text: str) -> str:
    """
    Replaces fenced ```diff``` blocks and unified-diff hunks with a
    single-line label (e.g. "[code change: log_writer.py]"), preserving the
    filename signal without polluting embeddings with +/- diff lines.
    """
    def _label(match: "re.Match") -> str:
        filename = _extract_diff_filename(match.group(0))
        return f"[code change: {filename}]" if filename else "[code change]"

    text = _DIFF_FENCE_RE.sub(_label, text)
    text = _UNIFIED_DIFF_HUNK_RE.sub(_label, text)
    return text


def _split_into_windows(text: str) -> List[str]:
    if len(text) <= TURN_SPLIT_THRESHOLD:
        return [text]
    windows = []
    stride = WINDOW_SIZE - WINDOW_OVERLAP
    start = 0
    while start < len(text):
        windows.append(text[start:start + WINDOW_SIZE])
        if start + WINDOW_SIZE >= len(text):
            break
        start += stride
    return windows


def chunk_turn(turn: Turn) -> List[Chunk]:
    combined = f"Developer: {turn.developer_text}\n\nAssistant: {_strip_diff_blocks(turn.assistant_text)}"
    windows = _split_into_windows(combined)
    return [
        Chunk(
            text=window,
            session_id=turn.session_id,
            turn_index=turn.turn_index,
            chunk_index=i,
            timestamp=turn.timestamp,
            commit_hash=turn.commit_hash,
        )
        for i, window in enumerate(windows)
    ]


def chunk_turns(turns: List[Turn]) -> List[Chunk]:
    chunks: List[Chunk] = []
    for turn in turns:
        chunks.extend(chunk_turn(turn))
    return chunks
