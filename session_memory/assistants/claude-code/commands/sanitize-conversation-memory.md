---
description: Produce a redacted, shareable copy of this workspace's conversation logs
allowed-tools: Bash
---

1. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
2. Run: `$SM sanitize --path "$(pwd)"`

This reads the raw conversation logs, applies secret/PII redaction patterns, and writes a parallel `*.sanitized.*` file set (log + rebuilt FAISS/BM25/chunk indexes) safe to commit and share -- the raw originals are left untouched.

Report back to the user what was redacted (the command prints a summary of pattern hits) and where the sanitized files landed.
