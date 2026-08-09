"""
Global wiring/unwiring of session-memory into Claude Code: slash commands,
SessionStart/SessionEnd hooks (~/.claude/settings.json), and MCP server
registration (`claude mcp add --scope user`). Every function here is
paired with an exact inverse so uninstall removes precisely what install
added, without touching anything else the user has configured.
"""
import os
import shutil
import subprocess

from session_memory.setup import paths
from session_memory.setup.jsonutil import load_json, save_json


def install_commands() -> None:
    os.makedirs(paths.CLAUDE_COMMANDS_DIR, exist_ok=True)
    src_dir = os.path.join(paths.ASSISTANTS_DIR, "claude-code", "commands")
    for name in paths.COMMAND_NAMES:
        shutil.copy(
            os.path.join(src_dir, f"{name}.md"),
            os.path.join(paths.CLAUDE_COMMANDS_DIR, f"{name}.md"),
        )


def uninstall_commands() -> None:
    for name in paths.COMMAND_NAMES:
        p = os.path.join(paths.CLAUDE_COMMANDS_DIR, f"{name}.md")
        if os.path.isfile(p):
            os.remove(p)


def _session_start_cmd() -> str:
    return f"python3 {paths.SESSION_START_WRAPPER}"


def _session_end_cmd() -> str:
    return f"python3 {paths.SESSION_END_WRAPPER}"


def _upsert_hook(hooks: dict, event_name: str, command: str) -> None:
    entries = hooks.setdefault(event_name, [])
    for entry in entries:
        for h in entry.get("hooks", []):
            if h.get("command") == command:
                return  # already wired, idempotent
    entries.append({"hooks": [{"type": "command", "command": command}]})


def _remove_hook(hooks: dict, event_name: str, command: str) -> None:
    entries = hooks.get(event_name)
    if not entries:
        return
    new_entries = []
    for entry in entries:
        remaining = [h for h in entry.get("hooks", []) if h.get("command") != command]
        if remaining:
            entry = dict(entry)
            entry["hooks"] = remaining
            new_entries.append(entry)
        # else: this entry only ever contained our handler -- drop it.
    hooks[event_name] = new_entries


def wire_hooks() -> None:
    data = load_json(paths.CLAUDE_SETTINGS_PATH)
    hooks = data.setdefault("hooks", {})
    _upsert_hook(hooks, "SessionStart", _session_start_cmd())
    _upsert_hook(hooks, "SessionEnd", _session_end_cmd())
    save_json(paths.CLAUDE_SETTINGS_PATH, data)


def unwire_hooks() -> None:
    if not os.path.isfile(paths.CLAUDE_SETTINGS_PATH):
        return
    data = load_json(paths.CLAUDE_SETTINGS_PATH)
    hooks = data.get("hooks", {})
    _remove_hook(hooks, "SessionStart", _session_start_cmd())
    _remove_hook(hooks, "SessionEnd", _session_end_cmd())
    save_json(paths.CLAUDE_SETTINGS_PATH, data)


def register_mcp(bin_path: str) -> None:
    # Remove first so re-running install is idempotent rather than erroring
    # on "already exists".
    subprocess.run(
        ["claude", "mcp", "remove", "session-memory", "--scope", "user"],
        capture_output=True, text=True,
    )
    subprocess.run(
        ["claude", "mcp", "add", "session-memory", "--scope", "user", "--", bin_path, "serve"],
        capture_output=True, text=True, check=True,
    )


def deregister_mcp() -> None:
    subprocess.run(
        ["claude", "mcp", "remove", "session-memory", "--scope", "user"],
        capture_output=True, text=True,
    )
