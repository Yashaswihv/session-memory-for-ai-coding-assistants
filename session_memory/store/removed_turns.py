import json
import os
from typing import Iterable, Set


class RemovedTurns:
    """
    Sidecar `.removed_turns.json` inside a `.conversation-memory/` directory,
    storing {session_id: [turn_index, ...]} for turns a developer removed via
    `session-memory cleanup`.

    `SessionIndex` decides what to index from what's currently on disk (so a
    hook that was killed after the log write but before indexing can catch
    up), which means a removed turn looks exactly like a turn that was never
    indexed yet — and gets re-added by the next capture. The session-end hook
    fires per turn (Claude Code/agy both wire it to their per-turn Stop
    event), so "the next capture" is usually seconds away. Recording removed
    turns here is what makes the removal durable across later captures.
    """

    STATE_FILENAME = ".removed_turns.json"

    def __init__(self, memory_dir: str):
        self.memory_dir = memory_dir
        self.path = os.path.join(memory_dir, self.STATE_FILENAME)
        self._data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
        return {
            session_id: {int(index) for index in indices}
            for session_id, indices in data.items()
        }

    def removed(self, session_id: str) -> Set[int]:
        return set(self._data.get(session_id, set()))

    def record_removed(self, session_id: str, turn_indices: Iterable[int]) -> None:
        indices = {int(index) for index in turn_indices}
        if not indices:
            return
        self._data.setdefault(session_id, set()).update(indices)
        self._save()

    def _save(self) -> None:
        os.makedirs(self.memory_dir, exist_ok=True)
        payload = {session_id: sorted(indices) for session_id, indices in self._data.items()}
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
