---
name: cleanup-conversation-memory
description: >-
  Use this skill when the user asks to remove, delete, or scrub specific
  turns from a captured session's conversation log (e.g. "remove that last
  message from the conversation log", "delete turn 4 from session X").
---

# Cleanup Conversation Memory

This permanently removes turns from a session's log and index -- for low-quality, sensitive, or superseded turns the developer wants gone. It is destructive and cannot be undone by this skill.

## Steps

1. If the user hasn't already stated which session id and which turn index/indices to remove, stop and ask -- do not guess.
2. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
3. Confirm with the user which turns are about to be deleted before running anything, unless they already stated it unambiguously.
4. Run: `$SM cleanup --path "$(pwd)" --session-id <id> --turn <n> [--turn <n> ...]` (repeat `--turn` for each index).

## Reporting back

Report back what was removed.
