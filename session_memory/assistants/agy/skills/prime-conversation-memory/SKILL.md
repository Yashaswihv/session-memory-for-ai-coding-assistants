---
name: prime-conversation-memory
description: >-
  Use this skill when the user asks to seed or prime this directory's
  conversation memory from a parent repository, typically inside a git
  worktree (e.g. "prime memory from the parent repo").
---

# Prime Conversation Memory

Only useful inside a linked git worktree whose parent repository already has conversation memory initialized.

## Steps

1. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
2. Run: `$SM prime --path "$(pwd)"`

## Reporting back

Report the output in your own words. If this directory isn't a worktree with a memory-enabled parent, the command will say so -- report that plainly rather than treating it as a failure.
