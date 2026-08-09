#!/usr/bin/env python3
"""
Claude Code SessionStart hook wrapper. Registered globally in
~/.claude/settings.json by `session-memory setup install`, so it fires
for every project -- it's a no-op in any directory that hasn't been
`session-memory init`'d (see run_session_start).

Claude Code sends the hook payload as snake_case JSON on stdin.
"""
import json
import os
import subprocess
import sys

SM_BIN = os.environ.get("SESSION_MEMORY_BIN") or os.path.expanduser("~/.local/bin/session-memory")


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return

    cwd = payload.get("cwd", ".")
    try:
        subprocess.run([SM_BIN, "hook", "session-start", "--cwd", cwd], timeout=20)
    except (OSError, subprocess.SubprocessError):
        # Best-effort: never let a capture failure disrupt the session.
        pass


if __name__ == "__main__":
    main()
