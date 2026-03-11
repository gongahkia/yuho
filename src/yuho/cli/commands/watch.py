"""File watcher command - monitors .yh files and re-validates on change."""

import os
import time
from pathlib import Path
from typing import Dict

import click

from yuho.services.analysis import analyze_file
from yuho.events.model import Event, EventType
from yuho.events.webhook import get_webhook_manager


def _get_mtimes(directory: str) -> Dict[str, float]:
    """Get modification times for all .yh files."""
    mtimes = {}
    for p in Path(directory).rglob("*.yh"):
        try:
            mtimes[str(p)] = p.stat().st_mtime
        except OSError:
            pass
    return mtimes


def run_watch(directory: str = ".", interval: float = 2.0, verbose: bool = False) -> None:
    """Watch directory for .yh file changes, re-validate, fire events."""
    click.echo(f"Watching {directory} for .yh changes (every {interval}s)...")
    prev = _get_mtimes(directory)
    manager = get_webhook_manager()
    try:
        while True:
            time.sleep(interval)
            curr = _get_mtimes(directory)
            changed = set()
            for f, mt in curr.items():
                if f not in prev or prev[f] < mt:
                    changed.add(f)
            for f in changed:
                click.echo(f"  Changed: {f}")
                result = analyze_file(f)
                if result.errors or result.parse_errors:
                    click.echo(f"    Errors: {len(result.errors) + len(result.parse_errors)}")
                    manager.dispatch(Event(
                        type=EventType.VALIDATION_ERROR,
                        source=f,
                        data={"error_count": len(result.errors) + len(result.parse_errors)},
                    ))
                else:
                    click.echo(f"    Valid")
                    manager.dispatch(Event(
                        type=EventType.STATUTE_UPDATED,
                        source=f,
                    ))
            prev = curr
    except KeyboardInterrupt:
        click.echo("\nStopped watching.")
