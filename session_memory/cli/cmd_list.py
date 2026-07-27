import click

from session_memory.registry.registry import Registry
from session_memory.registry.resolver import clean_stale_entries


@click.command(name="list")
@click.option(
    "--clean", is_flag=True,
    help="Also remove registered workspaces whose path no longer exists on disk.",
)
def cmd_list(clean: bool):
    """Lists every workspace registered on this machine."""
    registry = Registry()

    if clean:
        removed = clean_stale_entries(registry)
        for w in removed:
            click.echo(f"Removed stale entry: {w.name} ({w.path})")
        if removed:
            click.echo()

    workspaces = registry.list_workspaces()
    if not workspaces:
        click.echo("No registered workspaces.")
        return

    click.echo(f"Registered workspaces ({len(workspaces)}):\n")
    for w in workspaces:
        click.echo(f"* {w.name}  {w.path}")
        last = w.last_session_at or "never"
        assistants = ", ".join(w.assistants_used) or "none"
        tags = ", ".join(w.tags) or "none"
        click.echo(f"  id={w.id}  last session: {last}  assistants: {assistants}  tags: {tags}")
        click.echo()
