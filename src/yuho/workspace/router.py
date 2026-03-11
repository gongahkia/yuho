"""Workspace-aware request routing."""

from typing import Optional
from yuho.workspace.model import Workspace, WorkspaceStore


class WorkspaceRouter:
    """Routes requests to the appropriate workspace based on headers."""
    def __init__(self, store: Optional[WorkspaceStore] = None) -> None:
        self._store = store or WorkspaceStore()

    def resolve(self, workspace_id: Optional[str] = None, api_key: Optional[str] = None) -> Optional[Workspace]:
        """Resolve workspace from X-Workspace-ID header or API key."""
        if workspace_id:
            return self._store.get(workspace_id)
        if api_key:
            return self._store.get_by_api_key(api_key)
        return None

    def check_quota(self, workspace: Workspace) -> bool:
        """Check if workspace is within its quota."""
        return workspace.usage.requests_today < workspace.quota.max_requests_per_day

    def record_usage(self, workspace: Workspace, operation: str) -> None:
        """Increment usage counters."""
        workspace.usage.requests_today += 1
        if operation == "parse":
            workspace.usage.parse_count += 1
        elif operation == "transpile":
            workspace.usage.transpile_count += 1
        elif operation == "verify":
            workspace.usage.verify_count += 1
        elif operation == "lint":
            workspace.usage.lint_count += 1
