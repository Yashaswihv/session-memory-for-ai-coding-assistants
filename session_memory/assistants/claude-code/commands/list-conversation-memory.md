---
description: List every workspace registered with session-memory on this machine
argument-hint: [--clean]
allowed-tools: Bash
---

1. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
2. Run `$SM list`. If the user's arguments ($ARGUMENTS) include `--clean` (or they otherwise asked to prune stale entries), run `$SM list --clean` instead, which also removes registered workspaces whose path no longer exists on disk.

Present the result back to the user clearly (workspace name, path, id).
