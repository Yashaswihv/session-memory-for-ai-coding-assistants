"""
Global wiring/unwiring of session-memory into agy: skills, the Stop hook
(~/.gemini/config/hooks.json), skill registration
(~/.gemini/config/skills.json), and MCP server registration
(~/.gemini/config/mcp_config.json). Every function here is paired with an
exact inverse so uninstall removes precisely what install added.
"""
import os
import shutil

from session_memory.setup import paths
from session_memory.setup.jsonutil import load_json, save_json


def install_skills() -> None:
    os.makedirs(paths.AGY_SKILLS_DIR, exist_ok=True)
    src_dir = os.path.join(paths.ASSISTANTS_DIR, "agy", "skills")
    for name in paths.COMMAND_NAMES:
        dst = os.path.join(paths.AGY_SKILLS_DIR, name)
        if os.path.isdir(dst):
            shutil.rmtree(dst)
        shutil.copytree(os.path.join(src_dir, name), dst)


def uninstall_skills() -> None:
    if os.path.isdir(paths.AGY_SKILLS_DIR):
        shutil.rmtree(paths.AGY_SKILLS_DIR, ignore_errors=True)


def wire_skills_json() -> None:
    os.makedirs(paths.AGY_CONFIG_DIR, exist_ok=True)
    data = load_json(paths.AGY_SKILLS_JSON)
    entries = data.setdefault("entries", [])
    if not any(e.get("path") == paths.AGY_SKILLS_DIR for e in entries):
        entries.append({"path": paths.AGY_SKILLS_DIR})
    save_json(paths.AGY_SKILLS_JSON, data)


def unwire_skills_json() -> None:
    if not os.path.isfile(paths.AGY_SKILLS_JSON):
        return
    data = load_json(paths.AGY_SKILLS_JSON)
    entries = data.get("entries", [])
    data["entries"] = [e for e in entries if e.get("path") != paths.AGY_SKILLS_DIR]
    save_json(paths.AGY_SKILLS_JSON, data)


def wire_hooks_json() -> None:
    os.makedirs(paths.AGY_CONFIG_DIR, exist_ok=True)
    data = load_json(paths.AGY_HOOKS_JSON)
    data[paths.AGY_HOOK_NAME] = {
        "Stop": [{"type": "command", "command": f"python3 {paths.STOP_WRAPPER}"}],
    }
    save_json(paths.AGY_HOOKS_JSON, data)


def unwire_hooks_json() -> None:
    if not os.path.isfile(paths.AGY_HOOKS_JSON):
        return
    data = load_json(paths.AGY_HOOKS_JSON)
    data.pop(paths.AGY_HOOK_NAME, None)
    save_json(paths.AGY_HOOKS_JSON, data)


def wire_mcp_config(bin_path: str) -> None:
    os.makedirs(paths.AGY_CONFIG_DIR, exist_ok=True)
    data = load_json(paths.AGY_MCP_CONFIG_JSON)
    servers = data.setdefault("mcpServers", {})
    servers["session-memory"] = {"command": bin_path, "args": ["serve"]}
    save_json(paths.AGY_MCP_CONFIG_JSON, data)


def unwire_mcp_config() -> None:
    if not os.path.isfile(paths.AGY_MCP_CONFIG_JSON):
        return
    data = load_json(paths.AGY_MCP_CONFIG_JSON)
    data.get("mcpServers", {}).pop("session-memory", None)
    save_json(paths.AGY_MCP_CONFIG_JSON, data)
