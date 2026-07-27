import os
import subprocess
from datetime import datetime, timezone
from typing import Optional

import click

from session_memory.hooks.project_instructions import ensure_project_instructions
from session_memory.registry.registry import Registry
from session_memory.registry.workspace_entry import WorkspaceEntry, generate_workspace_id
from session_memory.store.workspace import MEMORY_DIR_NAME


def _get_git_remote(path: str) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


@click.command(name="init")
@click.option("--path", default=".", show_default=True, help="Workspace directory to initialize.")
@click.option("--name", default=None, help="Friendly name for this workspace (defaults to the directory name).")
@click.option("--tags", default="", help="Comma-separated tags for this workspace, set once at init time.")
def cmd_init(path: str, name: Optional[str], tags: str):
    """Initializes conversation memory for a workspace (works with or without git)."""
    root = os.path.realpath(path)
    memory_dir = os.path.join(root, MEMORY_DIR_NAME)
    os.makedirs(memory_dir, exist_ok=True)

    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    workspace_name = name or os.path.basename(root)

    entry = WorkspaceEntry(
        id=generate_workspace_id(root),
        name=workspace_name,
        path=root,
        memory_dir=memory_dir,
        initialized_at=datetime.now(timezone.utc).isoformat(),
        tags=tag_list,
        git_remote=_get_git_remote(root),
    )
    registry = Registry()
    registry.register(entry)

    ensure_project_instructions(root)

    click.echo(f"Initialized conversation memory for '{workspace_name}' at {memory_dir}")
    click.echo(f"Registered in ~/.config/session-memory/registry.json (id={entry.id}, tags={tag_list})")
