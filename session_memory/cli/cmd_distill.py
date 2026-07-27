import os
import sys

import click

from session_memory.distillation.distiller import apply_distillation, dump_logs_for_distillation
from session_memory.store.workspace import resolve_workspace


@click.group(name="distill")
def cmd_distill():
    """
    LLM-assisted distillation of accumulated session logs into AGENTS.md's
    <!-- DYNAMIC --> section (paper section 3.4, Strategy A). This
    framework is local-first and doesn't call an LLM itself: `dump` hands
    the accumulated logs to whatever is doing the summarizing — typically
    the AI assistant itself, via a skill or slash command, using its own
    already-running model — and `write` persists the result. The developer
    triggers this at deliberate checkpoints, preserving human judgment
    about what's worth distilling.
    """


@cmd_distill.command(name="dump")
@click.option("--path", default=".", show_default=True, help="Workspace directory.")
def cmd_distill_dump(path: str):
    """Prints every accumulated raw session log to stdout, for an assistant
    to read and summarize."""
    root = os.path.realpath(path)
    workspace = resolve_workspace(root)
    if workspace is None:
        click.echo("No .conversation-memory/ reachable from this directory.", err=True)
        raise SystemExit(1)
    logs = dump_logs_for_distillation(workspace.memory_dir)
    if not logs:
        click.echo("No accumulated session logs found.", err=True)
        raise SystemExit(1)
    click.echo(logs)


@cmd_distill.command(name="write")
@click.option("--path", default=".", show_default=True, help="Workspace directory.")
@click.option(
    "--file", "file_path", default=None,
    help="Read distilled content from this file instead of stdin.",
)
def cmd_distill_write(path: str, file_path: str):
    """Replaces AGENTS.md's <!-- DYNAMIC --> section with distilled content
    read from --file or stdin."""
    root = os.path.realpath(path)
    workspace = resolve_workspace(root)
    if workspace is None:
        click.echo("No .conversation-memory/ reachable from this directory.", err=True)
        raise SystemExit(1)

    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = sys.stdin.read()

    if not content.strip():
        click.echo("No content provided to distill.", err=True)
        raise SystemExit(1)

    apply_distillation(workspace.root, content)
    click.echo(f"Updated AGENTS.md's <!-- DYNAMIC --> section in {workspace.root}")
