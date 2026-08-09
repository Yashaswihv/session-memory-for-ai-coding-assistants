import click

from session_memory.setup import installer


@click.group(name="setup")
def cmd_setup():
    """Global installation plumbing -- driven by setup.sh / uninstall.sh,
    not normally invoked by hand."""


@cmd_setup.command(name="install")
@click.option(
    "--bin-path", required=True,
    help="Absolute path to the installed session-memory binary (inside its dedicated venv).",
)
def cmd_setup_install(bin_path: str):
    """Wires slash commands/skills, lifecycle hooks, and MCP registration
    into both Claude Code and agy's global config."""
    installer.install(bin_path)


@cmd_setup.command(name="uninstall")
@click.option(
    "--purge-data", is_flag=True,
    help="Also delete every registered workspace's .conversation-memory/ and the global registry.",
)
def cmd_setup_uninstall(purge_data: bool):
    """Removes everything `setup install` wired into Claude Code and agy's
    global config."""
    installer.uninstall(purge_data=purge_data)
