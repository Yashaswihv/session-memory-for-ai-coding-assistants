import click

from session_memory import __version__
from session_memory.cli.cmd_cleanup import cmd_cleanup
from session_memory.cli.cmd_deregister import cmd_deregister
from session_memory.cli.cmd_distill import cmd_distill
from session_memory.cli.cmd_init import cmd_init
from session_memory.cli.cmd_list import cmd_list
from session_memory.cli.cmd_prime import cmd_prime
from session_memory.cli.cmd_sanitize import cmd_sanitize
from session_memory.hooks.session_end import run_session_end
from session_memory.hooks.session_start import run_session_start


@click.group()
@click.version_option(version=__version__)
def cli():
    """session-memory: local-first conversation memory for AI coding assistants."""


cli.add_command(cmd_init)
cli.add_command(cmd_sanitize)
cli.add_command(cmd_distill)
cli.add_command(cmd_cleanup)
cli.add_command(cmd_prime)
cli.add_command(cmd_list)
cli.add_command(cmd_deregister)


@cli.group(name="hook")
def hook_group():
    """Lifecycle hook entry points, for wiring into an assistant's own hook config."""


@hook_group.command(name="session-start")
@click.option("--cwd", default=".", show_default=True, help="The session's working directory.")
def hook_session_start(cwd: str):
    """Injects the retrieval pointer into AGENTS.md/CLAUDE.md, if this workspace has opted in."""
    workspace = run_session_start(cwd)
    if workspace is None:
        click.echo("No .conversation-memory/ reachable from this directory — skipping.")
        return
    click.echo(f"Session-start: workspace root = {workspace.root}")


@hook_group.command(name="session-end")
@click.option("--cwd", default=".", show_default=True, help="The session's working directory.")
@click.option("--session-id", required=True, help="Unique id for this session.")
@click.option("--transcript-path", required=True, help="Path to the on-disk session transcript.")
@click.option("--assistant", default=None, help="Assistant name (e.g. agy, claude-code). Auto-detected if omitted.")
def hook_session_end(cwd: str, session_id: str, transcript_path: str, assistant: str):
    """Reads the on-disk transcript, extracts new turns, and appends them to this session's log."""
    new_turns = run_session_end(cwd, session_id, transcript_path, assistant=assistant)
    click.echo(f"Session-end: {len(new_turns)} new turn(s) captured.")


@cli.command(name="serve")
def cmd_serve():
    """Runs the MCP server (stdio transport) exposing search_conversation_log
    and search_all_workspaces. Point an assistant's MCP config at
    `session-memory serve`."""
    from session_memory.mcp_server.server import main as run_server

    run_server()


if __name__ == "__main__":
    cli()
