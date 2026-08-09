---
name: deregister-conversation-memory
description: >-
  Use this skill when the user asks to deregister, unregister, or remove a
  workspace from the session-memory registry (e.g. "deregister this
  project from session memory").
---

# Deregister Conversation Memory

## Steps

1. If the user hasn't given a workspace id, resolve the binary (below) and run `$SM list` first to show the user their registered workspaces and ask which one to deregister.
2. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
3. Run: `$SM deregister <workspace-id>`

This only stops the workspace from appearing in `list` or being searched by `search_all_workspaces` -- it does not delete its `.conversation-memory/` files. Mention that to the user so they aren't surprised.
