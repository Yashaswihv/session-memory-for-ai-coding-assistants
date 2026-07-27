from typing import Optional
from session_memory.capture.transcript_reader import TranscriptReader
from session_memory.capture.readers.agy_reader import AgyReader
from session_memory.capture.readers.claude_code_reader import ClaudeCodeReader

class ReaderFactory:
    @staticmethod
    def get_reader(assistant_name: str) -> TranscriptReader:
        """
        Returns the appropriate reader for a given assistant name.
        """
        name = assistant_name.lower().strip()
        if name in ("agy", "antigravity"):
            return AgyReader()
        elif name in ("claude", "claude-code", "claudecode"):
            return ClaudeCodeReader()
        else:
            raise ValueError(f"Unsupported assistant format: {assistant_name}")
            
    _AGY_TYPES = {
        "USER_INPUT", "PLANNER_RESPONSE", "CODE_ACTION", "RUN_COMMAND",
        "VIEW_FILE", "LIST_DIRECTORY", "SEARCH_WEB", "CHECKPOINT",
    }

    @staticmethod
    def detect_and_get_reader(file_path: str, max_lines_scanned: int = 50) -> TranscriptReader:
        """
        Heuristically detects the assistant transcript type by scanning up to
        `max_lines_scanned` lines for a distinguishing signal. A single line
        is not enough: real Claude Code transcripts lead with bookkeeping
        lines (`mode`, `permission-mode`, ...) that carry no schema signal
        before the first `user`/`assistant` line appears.
        """
        import json
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if idx >= max_lines_scanned:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    line_type = data.get("type")
                    if line_type in ReaderFactory._AGY_TYPES:
                        return AgyReader()
                    if line_type in ("user", "assistant") and "message" in data:
                        return ClaudeCodeReader()
        except OSError:
            pass
        # No confident signal found within the scanned window.
        return AgyReader()
