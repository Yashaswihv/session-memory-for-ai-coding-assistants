import click

from session_memory.registry.registry import Registry


@click.command(name="deregister")
@click.argument("workspace_id")
def cmd_deregister(workspace_id: str):
    """Removes a workspace from the registry (does not delete its
    .conversation-memory/ files -- only stops it from appearing in
    `list` or being searched by search_all_workspaces)."""
    registry = Registry()
    if registry.deregister(workspace_id):
        click.echo(f"Deregistered workspace {workspace_id}.")
    else:
        click.echo(f"No registered workspace with id {workspace_id}.")
