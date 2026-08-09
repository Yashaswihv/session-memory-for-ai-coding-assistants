#!/usr/bin/env python3
"""
Claude Code SessionEnd hook wrapper. Registered globally in
~/.claude/settings.json by `session-memory setup install` -- no-op in
any directory that hasn't opted in via `session-memory init`.

Claude Code sends the hook payload as snake_case JSON on stdin, with
`cwd`, `session_id`, and `transcript_path` fields.
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

    cwd = payload.get("cwd")
    session_id = payload.get("session_id")
    transcript_path = payload.get("transcript_path")
    if not (cwd and session_id and transcript_path):
        return

    try:
        subprocess.run(
            [
                SM_BIN, "hook", "session-end",
                "--cwd", cwd,
                "--session-id", session_id,
                "--transcript-path", transcript_path,
                "--assistant", "claude-code",
            ],
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        # Best-effort: never let a capture failure disrupt session end.
        pass


if __name__ == "__main__":
    main()
