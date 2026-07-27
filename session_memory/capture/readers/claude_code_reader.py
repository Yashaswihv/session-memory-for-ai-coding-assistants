import json
import os
from typing import List, Optional

from session_memory.capture.transcript_reader import TranscriptReader, Turn, parse_iso_timestamp


def _text_from_blocks(blocks) -> str:
    """Concatenates the text of `text`-type content blocks; ignores
    tool_use/tool_result/thinking/image blocks."""
    if not isinstance(blocks, list):
        return ""
    parts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    return "\n".join(p for p in parts if p).strip()


def _block_types(blocks) -> set:
    if not isinstance(blocks, list):
        return set()
    return {b.get("type") for b in blocks if isinstance(b, dict)}


class ClaudeCodeReader(TranscriptReader):
    """
    Reader implementation for Claude Code's JSONL transcript format
    (~/.claude/projects/<slug>/<session-id>.jsonl).

    Each line is a JSON object. Only lines with top-level `type` in
    ("user", "assistant") AND a `message` key are conversational turns;
    other line types (mode, permission-mode, system, file-history-snapshot,
    attachment, last-prompt, summary, ...) are session bookkeeping and are
    skipped. The real payload is nested: `message.role` / `message.content`,
    where `content` is a list of blocks (text, tool_use, tool_result,
    thinking, image) rather than a flat string.

    A "user" event whose content includes a `tool_result` block is a tool
    result being fed back to the model, not developer input, and is treated
    as connective tissue rather than a turn boundary. `isApiErrorMessage`
    lines and `isSidechain` (subagent) turns are excluded from the primary
    developer-assistant thread.
    """

    def parse_transcript(self, file_path: str, session_id: str, commit_hash: str) -> List[Turn]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Transcript file not found: {file_path}")

        events = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

        def is_real_user_turn(event: dict) -> bool:
            if event.get("type") != "user" or "message" not in event:
                return False
            if event.get("isSidechain") or event.get("isApiErrorMessage"):
                return False
            blocks = event["message"].get("content")
            types = _block_types(blocks)
            return "text" in types and "tool_result" not in types

        def is_real_assistant_event(event: dict) -> bool:
            if event.get("type") != "assistant" or "message" not in event:
                return False
            return not (event.get("isSidechain") or event.get("isApiErrorMessage"))

        turns: List[Turn] = []
        turn_index = 0
        i = 0
        n = len(events)

        while i < n:
            if not is_real_user_turn(events[i]):
                i += 1
                continue

            # A single logical developer message can be split across several
            # "user"-typed lines with bookkeeping lines (attachment, system,
            # ...) physically in between (observed with multi-image messages:
            # one line carries the text, a later one carries only
            # per-attachment placeholder blocks). Collect every real user
            # turn up to the first real assistant reply, rather than
            # requiring strict adjacency.
            dev_parts = []
            j = i
            while j < n and not is_real_assistant_event(events[j]):
                if is_real_user_turn(events[j]):
                    text = _text_from_blocks(events[j]["message"].get("content"))
                    if text:
                        dev_parts.append(text)
                j += 1
            developer_text = "\n".join(dev_parts).strip()

            # From the first assistant reply, extend forward through
            # interleaved assistant/tool_result events until the next real
            # user turn; take the LAST text-bearing assistant message as the
            # canonical response.
            k = j
            last_text_event: Optional[dict] = None
            while k < n and not is_real_user_turn(events[k]):
                candidate = events[k]
                if is_real_assistant_event(candidate):
                    text = _text_from_blocks(candidate["message"].get("content"))
                    if text:
                        last_text_event = candidate
                k += 1

            if last_text_event is not None and developer_text:
                turns.append(
                    Turn(
                        developer_text=developer_text,
                        assistant_text=_text_from_blocks(last_text_event["message"].get("content")),
                        timestamp=parse_iso_timestamp(last_text_event.get("timestamp")),
                        commit_hash=commit_hash,
                        session_id=session_id,
                        turn_index=turn_index,
                    )
                )
                turn_index += 1

            i = k

        return turns
