import os
from typing import Tuple

import click

from session_memory.store.cleanup import remove_turns
from session_memory.store.workspace import resolve_workspace


@click.command(name="cleanup")
@click.option("--path", default=".", show_default=True, help="Workspace directory.")
@click.option("--session-id", required=True, help="Session to clean up.")
@click.option(
    "--turn", "turns", multiple=True, type=int, required=True,
    help="Turn index to remove (repeatable).",
)
def cmd_cleanup(path: str, session_id: str, turns: Tuple[int, ...]):
    """
    Surgically removes specific turns from a session's log and index --
    for low-quality, sensitive, or superseded turns the developer wants
    gone from retrieval.
    """
    root = os.path.realpath(path)
    workspace = resolve_workspace(root)
    if workspace is None:
        click.echo("No .conversation-memory/ reachable from this directory.")
        return

    removed = remove_turns(workspace.memory_dir, session_id, list(turns))
    if removed == 0:
        click.echo(f"Nothing removed (session '{session_id}' or the given turn(s) not found).")
    else:
        click.echo(f"Removed {removed} chunk(s) for {len(turns)} turn(s) from session '{session_id}'.")
