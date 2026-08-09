"""
Top-level install()/uninstall() orchestration, called by `session-memory
setup install/uninstall` (in turn called by setup.sh / uninstall.sh).

Each individual wiring step is independent and best-effort: if one
assistant isn't present on this machine (e.g. no `claude` CLI, or agy was
never installed), that step is reported and skipped rather than aborting
the whole install/uninstall.
"""
import os
import shutil

from session_memory.registry.registry import Registry
from session_memory.setup import agy, claude_code, paths


def _step(label: str, fn) -> None:
    try:
        fn()
        print(f"  [ok] {label}")
    except Exception as e:
        print(f"  [skip] {label}: {e}")


def install(bin_path: str) -> None:
    print("Installing session-memory global integration...")

    os.makedirs(paths.HOOKS_DIR, exist_ok=True)
    for subdir, names in (
        ("claude-code/hooks", ["session_start_wrapper.py", "session_end_wrapper.py"]),
        ("agy/hooks", ["stop_wrapper.py"]),
    ):
        src_dir = os.path.join(paths.ASSISTANTS_DIR, subdir)
        for name in names:
            shutil.copy(os.path.join(src_dir, name), os.path.join(paths.HOOKS_DIR, name))
    print(f"  [ok] installed hook wrapper scripts to {paths.HOOKS_DIR}")

    os.makedirs(os.path.dirname(paths.BIN_LINK), exist_ok=True)
    if os.path.islink(paths.BIN_LINK) or os.path.exists(paths.BIN_LINK):
        os.remove(paths.BIN_LINK)
    os.symlink(bin_path, paths.BIN_LINK)
    print(f"  [ok] symlinked {paths.BIN_LINK} -> {bin_path}")

    if os.path.dirname(paths.BIN_LINK) not in os.environ.get("PATH", "").split(os.pathsep):
        print(
            f"  [warn] {os.path.dirname(paths.BIN_LINK)} is not on your PATH. "
            f'Add `export PATH="$HOME/.local/bin:$PATH"` to your shell profile so '
            f"`session-memory` resolves directly (the slash commands/skills fall back "
            f"to the full path in the meantime, so they'll still work)."
        )

    print("Claude Code:")
    _step("copy slash commands to ~/.claude/commands/", claude_code.install_commands)
    _step("wire SessionStart/SessionEnd hooks into ~/.claude/settings.json", claude_code.wire_hooks)
    _step("register MCP server (claude mcp add --scope user)", lambda: claude_code.register_mcp(paths.BIN_LINK))

    print("agy:")
    _step("copy skills to agy skills dir", agy.install_skills)
    _step("register skills in ~/.gemini/config/skills.json", agy.wire_skills_json)
    _step("wire Stop hook into ~/.gemini/config/hooks.json", agy.wire_hooks_json)
    _step("register MCP server in ~/.gemini/config/mcp_config.json", lambda: agy.wire_mcp_config(paths.BIN_LINK))

    print(
        "\nInstall complete. In any project directory, run "
        "/initialize-conversation-memory (Claude Code) or the equivalent skill "
        "(agy) to opt that workspace in."
    )


def uninstall(purge_data: bool = False) -> None:
    print("Removing session-memory global integration...")

    print("Claude Code:")
    _step("remove slash commands", claude_code.uninstall_commands)
    _step("unwire SessionStart/SessionEnd hooks", claude_code.unwire_hooks)
    _step("deregister MCP server", claude_code.deregister_mcp)

    print("agy:")
    _step("remove skills", agy.uninstall_skills)
    _step("unregister skills.json entry", agy.unwire_skills_json)
    _step("unwire Stop hook", agy.unwire_hooks_json)
    _step("unregister MCP server entry", agy.unwire_mcp_config)

    if os.path.islink(paths.BIN_LINK) or os.path.exists(paths.BIN_LINK):
        os.remove(paths.BIN_LINK)
        print(f"  [ok] removed {paths.BIN_LINK}")

    if purge_data:
        _purge_data()
    else:
        registry = Registry()
        workspaces = registry.list_workspaces()
        if workspaces:
            print(
                f"\n{len(workspaces)} workspace(s) still have conversation memory on disk "
                f"(left in place -- re-run with --purge-data to remove them too):"
            )
            for w in workspaces:
                print(f"  - {w.name}: {w.memory_dir}")

    print("\nUninstall complete.")


def _purge_data() -> None:
    registry = Registry()
    workspaces = registry.list_workspaces()
    print(f"\nPurging conversation memory data ({len(workspaces)} registered workspace(s))...")
    for w in workspaces:
        if not os.path.isdir(w.memory_dir):
            continue
        answer = input(f"  Delete conversation memory for '{w.name}' at {w.memory_dir}? [y/N] ").strip().lower()
        if answer == "y":
            shutil.rmtree(w.memory_dir, ignore_errors=True)
            print(f"    [ok] deleted {w.memory_dir}")
        else:
            print(f"    [skip] kept {w.memory_dir}")

    registry_path = registry.registry_path
    if os.path.isfile(registry_path):
        os.remove(registry_path)
        print(f"  [ok] deleted registry {registry_path}")
