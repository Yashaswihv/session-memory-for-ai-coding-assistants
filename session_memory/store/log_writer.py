import os
from datetime import datetime, timezone
from typing import List

from session_memory.capture.transcript_reader import Turn
from session_memory.store.session_state import SessionState


class LogWriter:
    """
    Appends new turns to the per-session, append-only markdown log
    `conversation_log_<commit_hash>_<session_id>.md` inside a workspace's
    `.conversation-memory/` directory (paper section 3.3). Re-entrancy is
    handled via `SessionState`: only turns beyond what's already been
    written for this session_id are appended.
    """

    def __init__(self, memory_dir: str, commit_hash: str, session_id: str):
        self.memory_dir = memory_dir
        self.commit_hash = commit_hash
        self.session_id = session_id
        self.log_path = os.path.join(
            memory_dir, f"conversation_log_{commit_hash}_{session_id}.md"
        )
        self.state = SessionState(memory_dir)

    def append_new_turns(self, turns: List[Turn]) -> List[Turn]:
        """
        Given the full ordered list of turns extracted so far for this
        session, appends only the ones not yet written and returns that new
        slice (so the indexing layer can embed just the new chunks).
        """
        already_written = self.state.turns_written(self.session_id)
        new_turns = turns[already_written:]
        if not new_turns:
            return []

        os.makedirs(self.memory_dir, exist_ok=True)
        is_new_file = not os.path.exists(self.log_path)
        with open(self.log_path, "a", encoding="utf-8") as f:
            if is_new_file:
                f.write(
                    f"# Conversation Log — commit {self.commit_hash}, session {self.session_id}\n\n"
                )
            for turn in new_turns:
                f.write(self._format_turn(turn))

        self.state.mark_written(self.session_id, len(turns))
        return new_turns

    @staticmethod
    def _format_turn(turn: Turn) -> str:
        if turn.timestamp:
            ts = datetime.fromtimestamp(turn.timestamp, tz=timezone.utc).isoformat()
        else:
            ts = "unknown"
        return (
            f"## Turn {turn.turn_index} — {ts}\n\n"
            f"**Developer:**\n{turn.developer_text}\n\n"
            f"**Assistant:**\n{turn.assistant_text}\n\n"
            "---\n\n"
        )
