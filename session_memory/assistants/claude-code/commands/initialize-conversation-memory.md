---
description: Set up (or catch up) session-memory for this directory, backfilling every transcript found on disk
allowed-tools: Bash
---

Set up conversation memory for the current directory and capture everything already on disk for it.

1. Resolve the binary: run `command -v session-memory`; if that prints nothing, use `~/.local/bin/session-memory` for the step below instead. Call whichever one resolves `$SM`.
2. Run: `$SM backfill --path "$(pwd)"`

That single command initializes the workspace if it isn't already (creates `.conversation-memory/`, registers it, injects the AGENTS.md/CLAUDE.md retrieval pointer) and then discovers and captures every transcript this machine has on disk for this directory -- for Claude Code that's full history, one file per past session.

Report back to the user, in your own words: how many sessions were found and how many new turns were captured in total (from the command's own output). If it says "No transcripts found", say so plainly rather than treating it as an error -- it just means nothing has been recorded here yet (e.g. this is the very first message of a brand new session and Claude Code hasn't flushed a transcript file yet).

Re-running this command later is safe and expected -- it only ever appends what's new.
