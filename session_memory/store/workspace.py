import os
import subprocess
from dataclasses import dataclass
from typing import Optional, Tuple

MEMORY_DIR_NAME = ".conversation-memory"
NO_GIT_SENTINEL = "no-git"


@dataclass
class Workspace:
    root: str
    memory_dir: str
    commit_hash: str
    is_worktree: bool = False
    worktree_name: Optional[str] = None


def get_commit_hash(repo_root: str) -> str:
    """
    Returns the HEAD commit hash for repo_root, or NO_GIT_SENTINEL if
    repo_root isn't a git repository, has no commits yet, or git isn't
    available. The framework must behave the same whether or not the
    target directory uses git — this is the only place commit identity
    is resolved, so every caller gets the same fallback for free.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return NO_GIT_SENTINEL


def _find_upwards(start: str, name: str) -> Optional[str]:
    """
    Walks up from `start` looking for a directory containing a child entry
    named `name`. Returns that directory, or None if not found by the
    filesystem root.
    """
    current = os.path.realpath(start)
    while True:
        if os.path.exists(os.path.join(current, name)):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def _read_worktree_branch(admin_gitdir: str, fallback: str) -> str:
    """
    Reads the branch name for a linked worktree from its administrative
    `<main-repo>/.git/worktrees/<name>/HEAD` file (contents like
    "ref: refs/heads/feature-x"). Falls back to `fallback` (the admin
    directory name) on a detached HEAD or if the file can't be read — the
    paper routes worktree memory under `.conversation-memory/worktrees/<branch>/`,
    which is the checked-out branch, not necessarily the admin dir's name.
    """
    head_path = os.path.join(admin_gitdir, "HEAD")
    try:
        with open(head_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
    except OSError:
        return fallback
    prefix = "ref: refs/heads/"
    if content.startswith(prefix):
        return content[len(prefix):]
    return fallback


def _resolve_worktree_parent(worktree_root: str) -> Optional[Tuple[str, str]]:
    """
    If `worktree_root/.git` is a *file* (linked git worktree), resolves the
    main repository root and this worktree's checked-out branch name from
    its `gitdir:` pointer (e.g. "gitdir: /main-repo/.git/worktrees/feature-x").
    Returns (main_repo_root, branch_name), or None if this isn't a linked
    worktree.
    """
    git_path = os.path.join(worktree_root, ".git")
    if not os.path.isfile(git_path):
        return None
    try:
        with open(git_path, "r", encoding="utf-8") as f:
            line = f.readline().strip()
    except OSError:
        return None
    if not line.startswith("gitdir:"):
        return None

    gitdir = line.split(":", 1)[1].strip()
    gitdir = os.path.realpath(gitdir)
    marker = os.path.join(".git", "worktrees") + os.sep
    normalized = gitdir
    if not normalized.endswith(os.sep):
        normalized += os.sep
    idx = normalized.find(marker)
    if idx == -1:
        return None

    main_repo_root = normalized[:idx].rstrip(os.sep) or os.sep
    admin_dir_name = os.path.basename(normalized.rstrip(os.sep))
    branch_name = _read_worktree_branch(gitdir, fallback=admin_dir_name)
    return main_repo_root, branch_name


def resolve_workspace(start_path: str) -> Optional[Workspace]:
    """
    Resolves the effective workspace for a session starting at `start_path`.
    Returns None if this directory tree hasn't opted in (no
    `.conversation-memory/` reachable) — per the paper's per-workspace
    opt-in gate, callers should treat None as "exit silently, don't capture".

    Resolution order:
      1. If `start_path` sits inside a linked git worktree AND the main
         repo has an initialized `.conversation-memory/`, route to the
         parent's `.conversation-memory/worktrees/<name>/` (worktree
         context inheritance, paper section 3.4).
      2. Otherwise, walk up from `start_path` for a directory that directly
         contains `.conversation-memory/` — this works identically whether
         or not git is present anywhere in the chain, since the opt-in gate
         is the directory's existence, not any git state.
    """
    git_root = _find_upwards(start_path, ".git")
    if git_root is not None:
        worktree_info = _resolve_worktree_parent(git_root)
        if worktree_info is not None:
            main_repo_root, worktree_name = worktree_info
            if os.path.isdir(os.path.join(main_repo_root, MEMORY_DIR_NAME)):
                memory_dir = os.path.join(main_repo_root, MEMORY_DIR_NAME, "worktrees", worktree_name)
                return Workspace(
                    root=main_repo_root,
                    memory_dir=memory_dir,
                    commit_hash=get_commit_hash(git_root),
                    is_worktree=True,
                    worktree_name=worktree_name,
                )
            # Parent repo never opted in — fall through to standard resolution.

    root = _find_upwards(start_path, MEMORY_DIR_NAME)
    if root is None:
        return None
    return Workspace(
        root=root,
        memory_dir=os.path.join(root, MEMORY_DIR_NAME),
        commit_hash=get_commit_hash(root),
    )
