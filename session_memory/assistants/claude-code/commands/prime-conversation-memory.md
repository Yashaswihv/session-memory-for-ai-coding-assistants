---
description: Seed this git worktree's conversation memory from its parent repo's accumulated history
allowed-tools: Bash
---

This is only useful inside a linked git worktree whose parent repository already has conversation memory initialized.

1. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
2. Run: `$SM prime --path "$(pwd)"`

Report the output back to the user in your own words. If this directory isn't a worktree with a memory-enabled parent, the command will say so -- report that plainly rather than treating it as a failure.
