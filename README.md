# Session Memory for AI Coding Assistants

A local-first framework that gives AI coding assistants automatic, cross-session memory: it captures every developer–assistant turn from the on-disk session transcript, indexes it with a hybrid FAISS + BM25 retrieval pipeline, and exposes it back to the assistant through an MCP tool — without cloud dependencies, explicit developer logging, or per-question prompting.

## Paper

This implementation follows the design described in:

> Yashaswi Hirekabbigere Vedamurthy. **"Session Memory for AI Coding Assistants: Automatic Capture, Semantic Retrieval, and Cross-Session Context Preservation."** Zenodo, 2026. https://doi.org/10.5281/zenodo.21301267

```bibtex
@misc{vedamurthy2026sessionmemory,
  author       = {Vedamurthy, Yashaswi Hirekabbigere},
  title        = {Session Memory for AI Coding Assistants: Automatic Capture, Semantic Retrieval, and Cross-Session Context Preservation},
  year         = {2026},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.21301267},
  url          = {https://doi.org/10.5281/zenodo.21301267}
}
```

The paper motivates the design around three failure modes in AI-assisted coding — session-boundary loss, in-session context truncation, and developer-handoff loss — and addresses them with three combined mechanisms: context-loss-resistant capture (reading the on-disk transcript rather than the model's in-memory context), zero-curation automatic capture (no per-turn developer judgment required), and git-native sharing with reviewable pre-share redaction.

## Architecture

```
SESSION-START HOOK                    SESSION-END HOOK
- injects retrieval pointer           - reads on-disk session transcript
  into project instruction file       - extracts clean turn pairs
                                       - appends to per-session log
                                       - incremental FAISS + BM25 indexing
                                                |
                                                v
                    +--------------------------------------------------+
                    | .conversation-memory/  (raw, local-only,          |
                    |   conversation_log_<commit>_<session>.md          |
                    |   conversation_log_<commit>_<session>.faiss       |
                    |   conversation_log_<commit>_<session>.bm25.pkl    |
                    |   conversation_log_<commit>_<session>.chunks.pkl  |
                    +--------------------------------------------------+
                                |                        |
                                v                        v
                +---------------------------+   +------------------------+
                | sanitize (on demand,      |   | MCP memory server      |
                | reviewed):                |   | search_conversation_log:|
                | - applies redaction       |   | - unions all session   |
                |   patterns, reports       |   |   indexes (raw, else   |
                |   matches                 |   |   sanitized fallback)  |
                | - writes shareable        |   | - hybrid FAISS+BM25,   |
                |   *.sanitized.* files     |   |   RRF, date filter     |
                +---------------------------+   +------------------------+
                                |                        |
                                v                        v
                +---------------------------+   distillation:      AI assistant
                | shared git repository:    |   rewrites the       autonomously
                | per-session files ->      |   instruction file's  calls the
                | git clone/pull -> team    |   DYNAMIC section     search tool
                | inherits                  |                       on demand
                +---------------------------+
```

## Package layout

| Module | Responsibility |
|---|---|
| `capture/` | Per-assistant transcript readers (`agy`, `claude-code`) normalizing to a shared `Turn` model |
| `store/` | Workspace resolution (git-independent), per-session log writing, re-entrant capture state, surgical turn cleanup |
| `registry/` | Cross-workspace registry at `~/.config/session-memory/registry.json` |
| `indexing/` | Turn chunking, `all-MiniLM-L6-v2` embeddings, FAISS + BM25 index builders |
| `retrieval/` | Reciprocal Rank Fusion, per-workspace and cross-workspace search, version-resilient index rebuilding |
| `redaction/` | Pattern + entropy-based secret redaction for the `sanitize` command |
| `distillation/` | Gathers accumulated logs and writes assistant-produced summaries into `AGENTS.md` |
| `hooks/` | `session_start` / `session_end` lifecycle hook logic |
| `mcp_server/` | Stdio MCP server exposing `search_conversation_log` and `search_all_workspaces` |
| `cli/` | The `session-memory` command-line tool |
| `setup/` | Global install/uninstall plumbing (`session-memory setup install/uninstall`) — wires slash commands/skills, hooks, and MCP registration into Claude Code and agy's own config |
| `assistants/` | Per-assistant asset source: Claude Code `commands/*.md` + hook wrapper scripts, agy `skills/<name>/SKILL.md` + hook wrapper script — copied into place by `setup install` |

## Global installation (recommended)

`setup.sh` builds a dedicated venv (independent of wherever you clone this repo), symlinks a `session-memory` binary onto your `PATH`, and wires the framework into **both** Claude Code and agy globally: slash commands/skills, lifecycle hooks (so capture is automatic once a workspace opts in), and MCP server registration. Run it once, from anywhere:

```bash
./setup.sh
```

Then, in any project directory, in either assistant:

```
/initialize-conversation-memory
```

This opts that directory in (`.conversation-memory/` gets created, the AGENTS.md/CLAUDE.md retrieval pointer gets injected, the workspace is registered) and backfills every transcript already on disk for it into `conversation_log_<commit>_<session>.{md,faiss,bm25.pkl,chunks.pkl}` files. After that, capture happens automatically on future sessions via each assistant's lifecycle hooks — no need to run it again except to catch up on history.

| Command / skill | Does |
|---|---|
| `/initialize-conversation-memory` | Opts a workspace in and backfills every transcript on disk for it |
| `/prime-conversation-memory` | Seeds a git worktree from its parent repo's accumulated memory |
| `/distill-conversation-memory` | Summarizes accumulated history into AGENTS.md's persistent section |
| `/sanitize-conversation-memory` | Produces redacted, shareable `*.sanitized.*` files |
| `/cleanup-conversation-memory` | Removes specific low-quality/sensitive turns |
| `/list-conversation-memory` | Lists every registered workspace on this machine |
| `/deregister-conversation-memory` | Removes a workspace from the registry (doesn't delete its files) |

**A real asymmetry worth knowing about**: Claude Code keeps every past session as its own file, so `/initialize-conversation-memory` there recovers full history. agy only persists a workspace → *most-recently-used-session* mapping on disk — there's no on-disk index of every past agy session for a directory — so agy backfill can only ever recover the current/most-recent session, not full history. Automatic *going-forward* capture is unaffected by this and, for agy specifically, is actually more granular than Claude Code's: agy has no session-end-equivalent hook, so capture is wired to its `Stop` event instead, which fires after every turn rather than only at session close.

### Manual / library installation

If you'd rather not run the global installer (e.g. you're only using the CLI directly, or contributing to the framework itself):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

```bash
# Initialize conversation memory for a workspace (works with or without git)
session-memory init --path . --tags backend,python

# Backfill every transcript already on disk for this workspace
session-memory backfill --path .

# Wire into an assistant's lifecycle hooks directly (setup.sh does this globally for you)
session-memory hook session-start --cwd .
session-memory hook session-end --cwd . --session-id <id> --transcript-path <path> --assistant agy

# Run the MCP server (point an assistant's MCP config at this)
session-memory serve

# Review and share redacted logs
session-memory sanitize --path .

# Distill accumulated logs into AGENTS.md (summarization is done by the assistant itself)
session-memory distill dump --path . | <assistant summarizes> | session-memory distill write --path .

# Worktree context inheritance
session-memory prime --path <worktree-dir>

# Registry management
session-memory list
session-memory deregister <workspace-id>

# Remove specific low-quality/sensitive turns from a session
session-memory cleanup --path . --session-id <id> --turn <index>
```

## Uninstalling

```bash
./uninstall.sh                # removes the framework; leaves every workspace's .conversation-memory/ and the registry in place
./uninstall.sh --purge-data   # also deletes .conversation-memory/ per workspace (prompts for each) and the global registry
```

`uninstall.sh` removes the venv, the `session-memory` symlink, all slash commands/skills, and every hook/MCP registration entry it added to Claude Code's and agy's config — without touching anything else already in those config files.

## Design notes

- **Local-first**: no cloud dependency, no account. Memory lives in gitignored files under `.conversation-memory/`; sharing is an explicit, reviewed step.
- **Works without git**: workspace resolution doesn't require a git repository — commit hashes fall back to a `no-git` sentinel.
- **Hybrid retrieval**: dense (FAISS, cosine similarity) and sparse (BM25 with an identifier-preserving tokenizer) retrieval merged via Reciprocal Rank Fusion, addressing the exact-identifier recall gap in pure semantic search over developer conversation logs.
- **Version-resilient sharing**: a session's raw index is preferred when present; a teammate's clone falls back to the sanitized index, and either is transparently rebuilt from its portable chunk list if the binary index fails to load.
