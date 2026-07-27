import json
import os
from typing import List, Optional

from session_memory.registry.workspace_entry import WorkspaceEntry

DEFAULT_REGISTRY_DIR = os.path.expanduser("~/.config/session-memory")
DEFAULT_REGISTRY_PATH = os.path.join(DEFAULT_REGISTRY_DIR, "registry.json")


class Registry:
    """
    Machine-local, cross-repo registry of every workspace that has run
    `session-memory init`, at ~/.config/session-memory/registry.json (XDG).
    It lives outside any repo so cross-workspace search
    (search_all_workspaces) can fan out over every registered
    `.conversation-memory/` store without per-repo configuration.
    """

    def __init__(self, registry_path: str = DEFAULT_REGISTRY_PATH):
        self.registry_path = registry_path
        self._workspaces: List[WorkspaceEntry] = self._load()

    def _load(self) -> List[WorkspaceEntry]:
        if not os.path.exists(self.registry_path):
            return []
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return []
        return [WorkspaceEntry.from_dict(w) for w in data.get("workspaces", [])]

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        payload = {
            "version": "1.0",
            "workspaces": [w.to_dict() for w in self._workspaces],
        }
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def list_workspaces(self) -> List[WorkspaceEntry]:
        return list(self._workspaces)

    def get_by_path(self, path: str) -> Optional[WorkspaceEntry]:
        norm = os.path.realpath(path)
        for w in self._workspaces:
            if os.path.realpath(w.path) == norm:
                return w
        return None

    def get_by_id(self, workspace_id: str) -> Optional[WorkspaceEntry]:
        for w in self._workspaces:
            if w.id == workspace_id:
                return w
        return None

    def register(self, entry: WorkspaceEntry) -> WorkspaceEntry:
        """
        Registers a newly-initialized workspace. Tags are set at init time
        (per the agreed default) and re-running init on an already
        registered path refreshes its mutable fields rather than duplicating
        the entry.
        """
        existing = self.get_by_path(entry.path)
        if existing is not None:
            existing.name = entry.name
            existing.tags = entry.tags
            existing.memory_dir = entry.memory_dir
            existing.git_remote = entry.git_remote
            self.save()
            return existing
        self._workspaces.append(entry)
        self.save()
        return entry

    def record_session(self, workspace_id: str, assistant_name: str, timestamp_iso: str) -> None:
        w = self.get_by_id(workspace_id)
        if w is None:
            return
        w.last_session_at = timestamp_iso
        if assistant_name not in w.assistants_used:
            w.assistants_used.append(assistant_name)
        self.save()

    def deregister(self, workspace_id: str) -> bool:
        before = len(self._workspaces)
        self._workspaces = [w for w in self._workspaces if w.id != workspace_id]
        if len(self._workspaces) != before:
            self.save()
            return True
        return False
