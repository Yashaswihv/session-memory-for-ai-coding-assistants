import os
from typing import Optional

import click

from session_memory.capture.discovery import discover_transcripts
from session_memory.cli.cmd_init import init_workspace
from session_memory.hooks.session_end import run_session_end


@click.command(name="backfill")
@click.option("--path", default=".", show_default=True, help="Workspace directory to backfill.")
@click.option(
    "--assistant",
    default=None,
    type=click.Choice(["claude-code", "agy"]),
    help="Limit discovery to one assistant. Default: search both.",
)
def cmd_backfill(path: str, assistant: Optional[str]):
    """
    Finds every transcript this machine has on disk for a workspace and
    captures + indexes each one that hasn't been captured yet, using the
    conversation_log_<commit>_<session> naming convention.

    Ensures the workspace is initialized first (safe to run standalone --
    this is what the /initialize-conversation-memory command uses).

    Note: for Claude Code this recovers full history (every past session
    is kept as its own file). For agy this can only recover the most
    recently used session in this directory -- agy itself only persists a
    workspace -> last-session mapping, not a full history index.
    """
    root = os.path.realpath(path)
    entry = init_workspace(root)

    transcripts = discover_transcripts(root, assistant)
    if not transcripts:
        click.echo(f"No transcripts found on disk for '{entry.name}' ({root}).")
        return

    total_new_turns = 0
    for session_id, transcript_path, assistant_name in transcripts:
        new_turns = run_session_end(root, session_id, transcript_path, assistant=assistant_name)
        total_new_turns += len(new_turns)
        click.echo(f"  [{assistant_name}] session {session_id}: {len(new_turns)} new turn(s) captured")

    click.echo(
        f"Backfill complete for '{entry.name}': {len(transcripts)} session(s) processed, "
        f"{total_new_turns} new turn(s) captured across all sessions."
    )
