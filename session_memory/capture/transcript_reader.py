from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


def parse_iso_timestamp(value: Optional[str]) -> float:
    """
    Converts an ISO-8601 timestamp (e.g. "2026-07-26T19:41:27Z" or
    "2026-07-26T20:11:15.938Z") as used by session transcripts into an
    epoch float. Returns 0.0 if value is missing or unparsable, rather
    than raising, since a malformed timestamp shouldn't drop a turn.
    """
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


class Turn(BaseModel):
    """
    A unified data model representing a single normalized developer-assistant turn.
    """
    developer_text: str = Field(..., description="The cleaned query or input from the developer.")
    assistant_text: str = Field(..., description="The canonical assistant response text.")
    timestamp: float = Field(..., description="Epoch timestamp of the turn.")
    commit_hash: str = Field(..., description="The git HEAD commit hash when the turn occurred.")
    session_id: str = Field(..., description="A unique identifier for the session.")
    turn_index: int = Field(..., description="0-indexed position of the turn in the session.")

class TranscriptReader(ABC):
    """
    Abstract Base Class for parsing assistant-specific session logs
    and extracting normalized Turn objects.
    """
    @abstractmethod
    def parse_transcript(self, file_path: str, session_id: str, commit_hash: str) -> List[Turn]:
        """
        Parses a session transcript from the disk.
        
        Args:
            file_path: Absolute path to the transcript file.
            session_id: The ID of this session.
            commit_hash: The current commit hash.
            
        Returns:
            A list of normalized Turn objects.
        """
        pass
