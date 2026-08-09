---
description: Remove a workspace from the session-memory registry (does not delete its files)
argument-hint: <workspace-id>
allowed-tools: Bash
---

Arguments given: $ARGUMENTS

1. If no workspace id was given in $ARGUMENTS, run `session-memory list` first (resolving the binary the same way as below) to show the user their registered workspaces and ask which one to deregister.
2. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
3. Run: `$SM deregister <workspace-id>`

This only stops the workspace from appearing in `list` or being searched by `search_all_workspaces` -- it does not delete its `.conversation-memory/` files. Mention that to the user so they aren't surprised.
