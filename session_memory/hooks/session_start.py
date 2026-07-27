from typing import Optional

from session_memory.hooks.project_instructions import ensure_project_instructions
from session_memory.store.workspace import Workspace, resolve_workspace


def run_session_start(cwd: str) -> Optional[Workspace]:
    """
    Session-start lifecycle hook. Per-workspace opt-in gate: if
    `.conversation-memory/` isn't reachable from `cwd` (directly, or via a
    worktree's initialized parent), this is a no-op that returns None —
    capture only happens in directories the developer explicitly
    initialized via `session-memory init`.
    """
    workspace = resolve_workspace(cwd)
    if workspace is None:
        return None
    ensure_project_instructions(workspace.root)
    return workspace
