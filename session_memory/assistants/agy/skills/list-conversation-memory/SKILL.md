---
name: list-conversation-memory
description: >-
  Use this skill when the user asks to list, show, or review every
  workspace registered with session-memory on this machine (e.g. "what
  projects have conversation memory set up?").
---

# List Conversation Memory

## Steps

1. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
2. Run `$SM list`. If the user asked to also prune stale entries, run `$SM list --clean` instead, which also removes registered workspaces whose path no longer exists on disk.

## Reporting back

Present the result back to the user clearly (workspace name, path, id).
