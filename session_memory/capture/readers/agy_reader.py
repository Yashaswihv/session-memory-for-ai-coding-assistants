import json
import os
import re
from typing import List, Optional

from session_memory.capture.transcript_reader import TranscriptReader, Turn, parse_iso_timestamp

_USER_REQUEST_RE = re.compile(r"<USER_REQUEST>(.*?)</USER_REQUEST>", re.DOTALL)


def _extract_developer_text(raw_content: str) -> str:
    """
    Real USER_INPUT events wrap the actual developer message in
    <USER_REQUEST>...</USER_REQUEST>, followed by sibling tags such as
    <ADDITIONAL_METADATA> and <USER_SETTINGS_CHANGE> that are session
    bookkeeping, not developer input. Pull out just the request body;
    fall back to the raw content if the tag isn't present.
    """
    match = _USER_REQUEST_RE.search(raw_content)
    return match.group(1).strip() if match else raw_content.strip()


class AgyReader(TranscriptReader):
    """
    Reader implementation for the Antigravity CLI (agy) JSONL transcript format.
    Each line is a JSON object with at least a `type` and `created_at` field.
    Relevant types:
      - USER_INPUT: developer turn; `content` holds the wrapped request text.
      - PLANNER_RESPONSE: an assistant step. Not every PLANNER_RESPONSE carries
        `content` — many are tool-call-only (`thinking` + `tool_calls`, no
        final text). Other event types (CODE_ACTION, RUN_COMMAND, VIEW_FILE,
        LIST_DIRECTORY, SEARCH_WEB, ...) represent tool activity interleaved
        between planner steps.
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

        turns: List[Turn] = []
        turn_index = 0
        i = 0
        n = len(events)

        while i < n:
            if events[i].get("type") != "USER_INPUT":
                i += 1
                continue

            # Collect developer text from every USER_INPUT up to the first
            # PLANNER_RESPONSE, tolerating other event types (CHECKPOINT,
            # SYSTEM_MESSAGE, ...) in between rather than requiring strict
            # adjacency between USER_INPUT lines (mirrors the equivalent
            # merge in the Claude Code reader).
            dev_parts = []
            j = i
            while j < n and events[j].get("type") != "PLANNER_RESPONSE":
                if events[j].get("type") == "USER_INPUT":
                    text = _extract_developer_text(events[j].get("content", ""))
                    if text:
                        dev_parts.append(text)
                j += 1
            developer_text = "\n".join(dev_parts).strip()

            # From the first PLANNER_RESPONSE, extend the window forward
            # through every event until the next USER_INPUT, and select the
            # LAST text-bearing PLANNER_RESPONSE in that window as the
            # canonical assistant reply. Intermediate tool-call-only
            # PLANNER_RESPONSEs and tool-activity events (CODE_ACTION,
            # RUN_COMMAND, VIEW_FILE, ...) are skipped.
            k = j
            last_text_event: Optional[dict] = None
            while k < n and events[k].get("type") != "USER_INPUT":
                candidate = events[k]
                if candidate.get("type") == "PLANNER_RESPONSE" and candidate.get("content"):
                    last_text_event = candidate
                k += 1

            if last_text_event is not None and developer_text:
                turns.append(
                    Turn(
                        developer_text=developer_text,
                        assistant_text=last_text_event["content"].strip(),
                        timestamp=parse_iso_timestamp(last_text_event.get("created_at")),
                        commit_hash=commit_hash,
                        session_id=session_id,
                        turn_index=turn_index,
                    )
                )
                turn_index += 1

            i = k  # resume scanning at the next USER_INPUT (or end of file)

        return turns
