import json
import os


class SessionState:
    """
    Sidecar `.session_state.json` inside a `.conversation-memory/` directory,
    storing {session_id: turns_written} so the session-end hook can be
    safely re-entrant (paper section 3.2: slice turns[N:] and append only
    new turns, regardless of how many times the hook fires for a session).
    """

    STATE_FILENAME = ".session_state.json"

    def __init__(self, memory_dir: str):
        self.memory_dir = memory_dir
        self.path = os.path.join(memory_dir, self.STATE_FILENAME)
        self._data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def turns_written(self, session_id: str) -> int:
        return self._data.get(session_id, 0)

    def mark_written(self, session_id: str, count: int) -> None:
        self._data[session_id] = count
        self._save()

    def _save(self) -> None:
        os.makedirs(self.memory_dir, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)
