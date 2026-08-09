"""
Bulk transcript discovery for `session-memory backfill`.

Finds every on-disk transcript an assistant has ever written for a given
workspace directory, without requiring the caller to already know a
session id -- this is what makes backfill possible (the normal `hook
session-end` entry point needs the session id and transcript path handed
to it by the assistant's own lifecycle hook).

Claude Code and agy differ in what they make discoverable:

- Claude Code keeps every past session as its own `<session-id>.jsonl`
  file inside a per-project directory, so full history is enumerable.
- agy only persists a workspace -> most-recently-used-session mapping
  (`cache/last_conversations.json`); there is no on-disk index of every
  past agy session tied to a given directory. So agy backfill can only
  ever recover the most recent session, not full history. This is a real
  limitation of what agy itself records, not a gap in this reader.
"""
import glob
import json
import os
import re
from typing import List, Optional, Tuple

CLAUDE_PROJECTS_DIR = os.path.expanduser("~/.claude/projects")
AGY_LAST_CONVERSATIONS = os.path.expanduser("~/.gemini/antigravity-cli/cache/last_conversations.json")
AGY_BRAIN_DIR = os.path.expanduser("~/.gemini/antigravity-cli/brain")

# (session_id, transcript_path, assistant_name)
Discovered = Tuple[str, str, str]


def _slugify_claude_code_path(path: str) -> str:
    """Claude Code's own project-directory naming: every character that
    isn't a letter or digit becomes `-`. Empirically verified against a
    real project directory rather than assumed."""
    return re.sub(r"[^a-zA-Z0-9]", "-", path)


def discover_claude_code_transcripts(root: str) -> List[Tuple[str, str]]:
    root = os.path.realpath(root)
    slug = _slugify_claude_code_path(root)
    project_dir = os.path.join(CLAUDE_PROJECTS_DIR, slug)

    if not os.path.isdir(project_dir):
        # Fallback in case the slug algorithm ever diverges (untested
        # characters, future Claude Code versions, etc.): look for a
        # uniquely-matching project dir by basename instead of guessing.
        basename_slug = _slugify_claude_code_path(os.path.basename(root))
        candidates = [
            d for d in glob.glob(os.path.join(CLAUDE_PROJECTS_DIR, "*"))
            if os.path.isdir(d) and os.path.basename(d).endswith(basename_slug)
        ]
        if len(candidates) != 1:
            return []
        project_dir = candidates[0]

    results = []
    for path in sorted(glob.glob(os.path.join(project_dir, "*.jsonl"))):
        session_id = os.path.splitext(os.path.basename(path))[0]
        results.append((session_id, path))
    return results


def discover_agy_transcripts(root: str) -> List[Tuple[str, str]]:
    root = os.path.realpath(root)
    if not os.path.isfile(AGY_LAST_CONVERSATIONS):
        return []
    try:
        with open(AGY_LAST_CONVERSATIONS, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except (OSError, json.JSONDecodeError):
        return []

    session_id = mapping.get(root)
    if not session_id:
        return []

    transcript_path = os.path.join(AGY_BRAIN_DIR, session_id, ".system_generated", "logs", "transcript.jsonl")
    if not os.path.isfile(transcript_path):
        return []
    return [(session_id, transcript_path)]


def discover_transcripts(root: str, assistant: Optional[str] = None) -> List[Discovered]:
    """Returns every discoverable (session_id, transcript_path, assistant_name)
    for this workspace. `assistant` restricts to one assistant if given
    ("claude-code" or "agy"); omit to search both."""
    results: List[Discovered] = []
    if assistant in (None, "claude-code"):
        results += [(sid, path, "claude-code") for sid, path in discover_claude_code_transcripts(root)]
    if assistant in (None, "agy"):
        results += [(sid, path, "agy") for sid, path in discover_agy_transcripts(root)]
    return results
