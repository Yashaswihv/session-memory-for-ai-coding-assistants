import os

import click

from session_memory.hooks.project_instructions import replace_dynamic_block
from session_memory.retrieval.searcher import search_workspace
from session_memory.store.workspace import MEMORY_DIR_NAME, resolve_workspace


@click.command(name="prime")
@click.option("--path", default=".", show_default=True, help="The worktree's own directory.")
@click.option("--top-k", default=5, show_default=True, help="How many parent-repo turns to seed with.")
def cmd_prime(path: str, top_k: int):
    """
    Worktree context inheritance: if `path` is a linked git worktree whose
    parent repo has initialized conversation memory, seeds a focused
    AGENTS.md in the worktree with relevant turns from the parent's
    history — retrieved using the worktree's branch name as the query —
    so a new worktree session starts with the parent's accumulated
    reasoning, not just its code (paper section 3.4).
    """
    worktree_dir = os.path.realpath(path)
    workspace = resolve_workspace(worktree_dir)
    if workspace is None or not workspace.is_worktree:
        click.echo("Not a linked worktree with an initialized parent repo -- nothing to prime.")
        return

    # `workspace.memory_dir` for a worktree points at the *new*
    # `.conversation-memory/worktrees/<branch>/` subdirectory used for
    # capturing this worktree's own future sessions -- empty at prime time.
    # What we want to search here is the parent repo's own accumulated
    # history, which lives directly at `workspace.root/.conversation-memory/`.
    parent_memory_dir = os.path.join(workspace.root, MEMORY_DIR_NAME)
    query = f"branch {workspace.worktree_name}"
    results = search_workspace(parent_memory_dir, query, top_k=top_k)
    if not results:
        click.echo(f"No prior context found in the parent repo for branch '{workspace.worktree_name}'.")
        return

    lines = [f"### Primed context inherited from parent repo (branch: {workspace.worktree_name})", ""]
    for chunk, _score in results:
        lines.append(f"- {chunk.text.strip()}")
        lines.append("")

    # replace_dynamic_block writes into `worktree_dir` specifically (not
    # workspace.root, which points at the *parent* repo for a worktree) --
    # the primed instruction file belongs in the worktree itself.
    replace_dynamic_block(worktree_dir, "\n".join(lines))
    click.echo(f"Primed {os.path.join(worktree_dir, 'AGENTS.md')} with {len(results)} turn(s) from the parent repo.")
