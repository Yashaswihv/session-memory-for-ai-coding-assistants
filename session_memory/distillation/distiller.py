from typing import Optional

from session_memory.distillation.log_gatherer import gather_session_logs
from session_memory.hooks.project_instructions import replace_dynamic_block


def dump_logs_for_distillation(memory_dir: str, since: Optional[float] = None) -> str:
    """Everything a distillation pass needs to read (paper section 3.4,
    Strategy A). This framework doesn't call an LLM itself — it hands the
    accumulated logs to whatever is doing the summarizing, typically the
    AI assistant itself via a skill/slash command, using its own
    already-running model rather than a separate API call."""
    return gather_session_logs(memory_dir, since=since)


def apply_distillation(root: str, distilled_content: str) -> None:
    """Persists an already-produced distillation into AGENTS.md's
    `<!-- DYNAMIC -->` section."""
    replace_dynamic_block(root, distilled_content)
