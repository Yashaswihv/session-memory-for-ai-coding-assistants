import os
from typing import List

from session_memory.registry.registry import Registry
from session_memory.registry.workspace_entry import WorkspaceEntry


def find_stale_entries(registry: Registry) -> List[WorkspaceEntry]:
    """Registered workspaces whose `path` no longer exists on disk."""
    return [w for w in registry.list_workspaces() if not os.path.isdir(w.path)]


def clean_stale_entries(registry: Registry) -> List[WorkspaceEntry]:
    """Removes and returns the workspace entries whose path no longer exists."""
    stale = find_stale_entries(registry)
    for w in stale:
        registry.deregister(w.id)
    return stale
