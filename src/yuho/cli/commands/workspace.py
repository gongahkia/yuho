"""Workspace management CLI commands."""

import json
import uuid
from typing import Optional

import click

from yuho.workspace.model import Workspace, WorkspaceStore


def run_workspace_create(name: str) -> None:
    """Create a new workspace."""
    store = WorkspaceStore()
    ws_id = uuid.uuid4().hex[:12]
    api_key = uuid.uuid4().hex
    ws = Workspace(id=ws_id, name=name, api_key=api_key)
    store.create(ws)
    click.echo(f"Created workspace '{name}'")
    click.echo(f"  ID: {ws_id}")
    click.echo(f"  API Key: {api_key}")
    click.echo(f"  Library: {ws.library_path}")


def run_workspace_list() -> None:
    """List all workspaces."""
    store = WorkspaceStore()
    workspaces = store.list()
    if not workspaces:
        click.echo("No workspaces")
        return
    for ws in workspaces:
        click.echo(f"  {ws.id}  {ws.name}  library={ws.library_path}")


def run_workspace_switch(workspace_id: str) -> None:
    """Set active workspace (writes to config)."""
    store = WorkspaceStore()
    ws = store.get(workspace_id)
    if not ws:
        click.echo(f"Workspace {workspace_id} not found", err=True)
        return
    click.echo(f"Switched to workspace '{ws.name}' ({ws.id})")
