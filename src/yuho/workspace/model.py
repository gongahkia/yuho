"""Workspace model for multi-tenant isolation."""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WorkspaceQuota:
    """Per-workspace usage limits."""

    max_requests_per_day: int = 10000
    max_source_length: int = 1_048_576
    allowed_transpile_targets: List[str] = field(default_factory=list)  # empty = all


@dataclass
class WorkspaceUsage:
    """Usage counters for a workspace."""

    requests_today: int = 0
    parse_count: int = 0
    transpile_count: int = 0
    verify_count: int = 0
    lint_count: int = 0


@dataclass
class Workspace:
    """An isolated workspace with its own library and config."""

    id: str
    name: str
    api_key: str = ""
    library_path: str = ""
    config_overrides: Dict[str, Any] = field(default_factory=dict)
    quota: WorkspaceQuota = field(default_factory=WorkspaceQuota)
    usage: WorkspaceUsage = field(default_factory=WorkspaceUsage)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workspace":
        quota = WorkspaceQuota(**data.pop("quota", {}))
        usage = WorkspaceUsage(**data.pop("usage", {}))
        return cls(**data, quota=quota, usage=usage)


class WorkspaceStore:
    """Persistent workspace storage."""

    def __init__(self, data_dir: Optional[str] = None) -> None:
        self._dir = Path(data_dir) if data_dir else Path.home() / ".config" / "yuho" / "workspaces"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._workspaces: Dict[str, Workspace] = {}
        self._load()

    def _load(self) -> None:
        index = self._dir / "index.json"
        if index.exists():
            try:
                data = json.loads(index.read_text(encoding="utf-8"))
                for ws_data in data:
                    ws = Workspace.from_dict(ws_data)
                    self._workspaces[ws.id] = ws
            except Exception:
                pass

    def _save(self) -> None:
        index = self._dir / "index.json"
        data = [ws.to_dict() for ws in self._workspaces.values()]
        index.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def create(self, workspace: Workspace) -> None:
        ws_dir = self._dir / workspace.id
        ws_dir.mkdir(exist_ok=True)
        if not workspace.library_path:
            workspace.library_path = str(ws_dir / "library")
            Path(workspace.library_path).mkdir(exist_ok=True)
        self._workspaces[workspace.id] = workspace
        self._save()

    def get(self, workspace_id: str) -> Optional[Workspace]:
        return self._workspaces.get(workspace_id)

    def get_by_api_key(self, api_key: str) -> Optional[Workspace]:
        for ws in self._workspaces.values():
            if ws.api_key and ws.api_key == api_key:
                return ws
        return None

    def list(self) -> List[Workspace]:
        return list(self._workspaces.values())

    def delete(self, workspace_id: str) -> bool:
        if workspace_id in self._workspaces:
            del self._workspaces[workspace_id]
            self._save()
            return True
        return False
