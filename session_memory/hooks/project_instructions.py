import os

AGENTS_FILENAME = "AGENTS.md"
CLAUDE_FILENAME = "CLAUDE.md"

RETRIEVAL_POINTER = (
    "<!-- SESSION-MEMORY:POINTER -->\n"
    "When you cannot find the rationale for a decision in the project "
    "instructions or code, use the `search_conversation_log` MCP tool. "
    "When claiming that a past decision was made, always call "
    "`search_conversation_log` to verify before stating it.\n"
    "<!-- /SESSION-MEMORY:POINTER -->\n"
)

DYNAMIC_START_MARKER = "<!-- DYNAMIC -->"
DYNAMIC_END_MARKER = "<!-- /DYNAMIC -->"
DYNAMIC_BLOCK = f"{DYNAMIC_START_MARKER}\n{DYNAMIC_END_MARKER}\n"


def ensure_project_instructions(root: str) -> None:
    """
    Ensures AGENTS.md carries the retrieval pointer and a `<!-- DYNAMIC -->`
    section (idempotent: checks for the sentinel before writing anything so
    repeated session-start invocations don't duplicate content), and that
    CLAUDE.md sources it via `@AGENTS.md` — Claude Code's file-import syntax
    keeps AGENTS.md the single source of truth rather than duplicating the
    pointer into two files.
    """
    agents_path = os.path.join(root, AGENTS_FILENAME)
    if not os.path.exists(agents_path):
        with open(agents_path, "w", encoding="utf-8") as f:
            f.write(RETRIEVAL_POINTER + "\n" + DYNAMIC_BLOCK)
    else:
        with open(agents_path, "r", encoding="utf-8") as f:
            content = f.read()
        appended = False
        if "SESSION-MEMORY:POINTER" not in content:
            content += "\n" + RETRIEVAL_POINTER
            appended = True
        if DYNAMIC_START_MARKER not in content:
            content += "\n" + DYNAMIC_BLOCK
            appended = True
        if appended:
            with open(agents_path, "w", encoding="utf-8") as f:
                f.write(content)

    claude_path = os.path.join(root, CLAUDE_FILENAME)
    import_line = f"@{AGENTS_FILENAME}\n"
    if not os.path.exists(claude_path):
        with open(claude_path, "w", encoding="utf-8") as f:
            f.write(import_line)
    else:
        with open(claude_path, "r", encoding="utf-8") as f:
            content = f.read()
        if f"@{AGENTS_FILENAME}" not in content:
            with open(claude_path, "a", encoding="utf-8") as f:
                f.write("\n" + import_line)


def replace_dynamic_block(root: str, new_content: str) -> None:
    """
    Replaces the content between `<!-- DYNAMIC -->` and `<!-- /DYNAMIC -->`
    in AGENTS.md with `new_content` (a full rewrite, not an append — the
    distillation step re-reads all accumulated logs and produces a fresh
    summary each time it's triggered). Ensures the pointer/DYNAMIC
    scaffolding exists first, in case this workspace's AGENTS.md hasn't
    been touched by session-start yet.
    """
    ensure_project_instructions(root)
    agents_path = os.path.join(root, AGENTS_FILENAME)
    with open(agents_path, "r", encoding="utf-8") as f:
        content = f.read()

    start = content.index(DYNAMIC_START_MARKER) + len(DYNAMIC_START_MARKER)
    end = content.index(DYNAMIC_END_MARKER)
    updated = content[:start] + "\n" + new_content.strip() + "\n" + content[end:]

    with open(agents_path, "w", encoding="utf-8") as f:
        f.write(updated)
