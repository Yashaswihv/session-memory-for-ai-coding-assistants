#!/usr/bin/env python3
"""
Claude Code SessionEnd + Stop hook wrapper. Registered globally in
~/.claude/settings.json by `session-memory setup install` for both
events -- no-op in any directory that hasn't opted in via
`session-memory init`. Wiring the same script to both events gives live
per-turn capture (Stop fires each time the main agent finishes
responding) while also catching up at true session close; running it
twice for the same turn is harmless since capture is re-entrant and only
appends what's new.

Claude Code sends the hook payload as snake_case JSON on stdin, with
`cwd`, `session_id`, and `transcript_path` fields, for both events.
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
