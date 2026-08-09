---
description: Summarize accumulated conversation history into AGENTS.md/CLAUDE.md's persistent DYNAMIC section
allowed-tools: Bash
---

This framework is local-first and doesn't call an LLM on its own -- distillation is done by you, the assistant, using your own already-running reasoning, at a deliberate checkpoint the developer chose. Do not skip reading the dumped content; the quality of this summary is the whole point.

1. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
2. Run `$SM distill dump --path "$(pwd)"` and read its full output. If it reports no accumulated logs, tell the user and stop -- there's nothing to distill yet.
3. Write a concise, high-signal summary of what's accumulated: durable architectural decisions, constraints, and their rationale -- not a transcript recap. Favor "we decided X because Y" statements over narration. Keep it something a future session should actually read, not exhaustive.
4. Write that summary to a temp file (e.g. `/tmp/sm-distill-$$.md`), then run:
   `$SM distill write --path "$(pwd)" --file /tmp/sm-distill-$$.md`
5. Clean up the temp file afterward.

Report back to the user what got written and where (AGENTS.md's or CLAUDE.md's `<!-- DYNAMIC -->` section, per the command's own confirmation output).
