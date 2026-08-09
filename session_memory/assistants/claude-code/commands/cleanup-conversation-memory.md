---
description: Surgically remove specific turns from a captured session's log and index
argument-hint: <session-id> <turn-index> [turn-index ...]
allowed-tools: Bash
---

This permanently removes turns from a session's log and index -- for low-quality, sensitive, or superseded turns the developer wants gone. It is destructive and cannot be undone by this command.

Arguments given: $ARGUMENTS

1. If no arguments were given, or a session id wasn't given, stop and ask the user for the session id and the turn index/indices to remove -- do not guess which turns they mean.
2. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
3. Confirm with the user which turns are about to be deleted before running anything, unless they already stated it unambiguously in $ARGUMENTS.
4. Run: `$SM cleanup --path "$(pwd)" --session-id <id> --turn <n> [--turn <n> ...]` (repeat `--turn` for each index).

Report back what was removed.
