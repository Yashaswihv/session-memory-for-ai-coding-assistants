---
name: distill-conversation-memory
description: >-
  Use this skill when the user asks to distill, summarize, or consolidate
  accumulated conversation history into a persistent project notes section
  (e.g. "distill our conversation history", "summarize what we've decided
  so far into the project notes").
---

# Distill Conversation Memory

This framework is local-first and doesn't call an LLM on its own -- distillation is done by you, the agent, using your own already-running reasoning, at a deliberate checkpoint the developer chose. Do not skip reading the dumped content; the quality of this summary is the whole point.

## Steps

1. Resolve the binary: run `command -v session-memory`; if empty, use `~/.local/bin/session-memory` instead. Call it `$SM`.
2. Run `$SM distill dump --path "$(pwd)"` and read its full output. If it reports no accumulated logs, tell the user and stop -- there's nothing to distill yet.
3. Write a concise, high-signal summary of what's accumulated: durable architectural decisions, constraints, and their rationale -- not a transcript recap. Favor "we decided X because Y" statements over narration. Keep it something a future session should actually read, not exhaustive.
4. Write that summary to a temp file (e.g. `/tmp/sm-distill-$$.md`), then run:
   `$SM distill write --path "$(pwd)" --file /tmp/sm-distill-$$.md`
5. Clean up the temp file afterward.

## Reporting back

Tell the user what got written and where (AGENTS.md's `<!-- DYNAMIC -->` section, per the command's own confirmation output).
