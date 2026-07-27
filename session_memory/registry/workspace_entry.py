import hashlib
import os
from dataclasses import asdict, dataclass, field
from typing import List, Optional


def generate_workspace_id(path: str) -> str:
    """Stable short id for a workspace, derived from its resolved real path
    (not just abspath) so a symlinked path resolves to the same id as its
    canonical target."""
    return hashlib.sha256(os.path.realpath(path).encode("utf-8")).hexdigest()[:8]


@dataclass
class WorkspaceEntry:
    id: str
    name: str
    path: str
    memory_dir: str
    initialized_at: str
    tags: List[str] = field(default_factory=list)
    git_remote: Optional[str] = None
    last_session_at: Optional[str] = None
    assistants_used: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "WorkspaceEntry":
        return cls(**data)
