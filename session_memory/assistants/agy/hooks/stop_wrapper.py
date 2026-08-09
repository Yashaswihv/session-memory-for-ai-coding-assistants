#!/usr/bin/env python3
"""
agy `Stop` lifecycle hook wrapper. agy has no SessionEnd-equivalent event,
but `Stop` fires whenever the agent's execution loop finishes (i.e. after
every turn, not just at conversation close) and its payload already
includes transcriptPath/workspacePaths/conversationId directly -- no
guessing needed, unlike Claude Code where the transcript path has to be
derived from cwd. Net effect: agy actually gets more granular automatic
capture than Claude Code (after every turn instead of only at session
end), for free. Registered globally in ~/.gemini/config/hooks.json by
`session-memory setup install` -- no-op in any directory that hasn't
opted in via `session-memory init`.

agy sends the hook payload as camelCase JSON on stdin (protojson
encoding) and requires a JSON object with a `decision` field on stdout.
"""
import json
import os
import subprocess
import sys

SM_BIN = os.environ.get("SESSION_MEMORY_BIN") or os.path.expanduser("~/.local/bin/session-memory")


def main():
    # Always allow the stop to proceed -- this hook only observes, never
    # blocks, and must never wedge the agent loop even if it errors.
    result = {"decision": "allow"}

    try:
        payload = json.load(sys.stdin)
        workspace_paths = payload.get("workspacePaths") or []
        cwd = workspace_paths[0] if workspace_paths else None
        session_id = payload.get("conversationId")
        transcript_path = payload.get("transcriptPath")

        if cwd and session_id and transcript_path:
            subprocess.run(
                [
                    SM_BIN, "hook", "session-end",
                    "--cwd", cwd,
                    "--session-id", session_id,
                    "--transcript-path", transcript_path,
                    "--assistant", "agy",
                ],
                timeout=60,
            )
    except (json.JSONDecodeError, OSError, subprocess.SubprocessError):
        # Best-effort: never let a capture failure disrupt the agent loop.
        pass

    print(json.dumps(result))


if __name__ == "__main__":
    main()
