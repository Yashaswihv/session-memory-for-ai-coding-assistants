---
name: initialize-conversation-memory
description: >-
  Use this skill when the user asks to set up, initialize, or backfill
  session-memory conversation history for the current directory (e.g. "set
  up conversation memory here", "backfill my conversation history").
---

# Initialize Conversation Memory

Set up conversation memory for the current directory and capture everything already on disk for it.

## Steps

1. Resolve the binary: run `command -v session-memory`; if that prints nothing, use `~/.local/bin/session-memory` instead for the step below. Call whichever one resolves `$SM`.
2. Run: `$SM backfill --path "$(pwd)" --assistant agy`

That single command initializes the workspace if it isn't already (creates `.conversation-memory/`, registers it, injects the AGENTS.md retrieval pointer) and then captures whatever agy transcript this machine has on disk for this directory.

## Important limitation

Unlike Claude Code, agy only persists a workspace -> most-recently-used-session mapping on disk (there is no full history index of every past agy session for a directory). So this can only recover the **current or most recent** agy session in this directory, not full history. If the user expects older sessions to show up and they don't, this is why -- say so plainly rather than implying something went wrong.

## Reporting back

Tell the user how many sessions were found and how many new turns were captured (from the command's own output). "No transcripts found" is not an error -- it just means nothing has been recorded here yet.

Re-running this skill later is safe -- it only ever appends what's new.
