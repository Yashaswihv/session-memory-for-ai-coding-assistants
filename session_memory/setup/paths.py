import os

import session_memory

PACKAGE_DIR = os.path.dirname(os.path.abspath(session_memory.__file__))
ASSISTANTS_DIR = os.path.join(PACKAGE_DIR, "assistants")

# Everything this framework puts on the system outside of a workspace's own
# .conversation-memory/ lives under here (plus the two symlink/config
# touchpoints below) -- keep this list in sync with uninstall.sh, which
# rm -rf's INSTALL_ROOT wholesale after the Python-side unwiring runs.
INSTALL_ROOT = os.path.expanduser("~/.local/share/session-memory")
HOOKS_DIR = os.path.join(INSTALL_ROOT, "hooks")
AGY_SKILLS_DIR = os.path.join(INSTALL_ROOT, "agy-skills")
BIN_LINK = os.path.expanduser("~/.local/bin/session-memory")

CLAUDE_COMMANDS_DIR = os.path.expanduser("~/.claude/commands")
CLAUDE_SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")

AGY_CONFIG_DIR = os.path.expanduser("~/.gemini/config")
AGY_HOOKS_JSON = os.path.join(AGY_CONFIG_DIR, "hooks.json")
AGY_MCP_CONFIG_JSON = os.path.join(AGY_CONFIG_DIR, "mcp_config.json")
AGY_SKILLS_JSON = os.path.join(AGY_CONFIG_DIR, "skills.json")
AGY_HOOK_NAME = "session-memory-capture"

# Shared between the Claude Code commands/ and agy skills/ asset trees --
# each name maps to <name>.md (Claude Code) and <name>/SKILL.md (agy).
COMMAND_NAMES = [
    "initialize-conversation-memory",
    "prime-conversation-memory",
    "distill-conversation-memory",
    "sanitize-conversation-memory",
    "cleanup-conversation-memory",
    "list-conversation-memory",
    "deregister-conversation-memory",
]

SESSION_START_WRAPPER = os.path.join(HOOKS_DIR, "session_start_wrapper.py")
SESSION_END_WRAPPER = os.path.join(HOOKS_DIR, "session_end_wrapper.py")
STOP_WRAPPER = os.path.join(HOOKS_DIR, "stop_wrapper.py")
