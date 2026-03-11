"""Webhook management CLI commands."""

import json
import uuid
from typing import Optional

import click

from yuho.events.model import Event, EventType
from yuho.events.webhook import WebhookEndpoint, get_webhook_manager


def run_webhook_add(url: str, events: list, secret: Optional[str] = None) -> None:
    """Register a webhook endpoint."""
    endpoint_id = uuid.uuid4().hex[:12]
    secret = secret or uuid.uuid4().hex
    ep = WebhookEndpoint(
        id=endpoint_id,
        url=url,
        secret=secret,
        events=events if events else ["*"],
    )
    get_webhook_manager().register(ep)
    click.echo(f"Registered webhook {endpoint_id}")
    click.echo(f"  URL: {url}")
    click.echo(f"  Secret: {secret}")
    click.echo(f"  Events: {', '.join(ep.events)}")


def run_webhook_list() -> None:
    """List registered webhooks."""
    endpoints = get_webhook_manager().list_endpoints()
    if not endpoints:
        click.echo("No webhooks registered")
        return
    for ep in endpoints:
        status = "enabled" if ep.enabled else "disabled"
        click.echo(f"  {ep.id}  {ep.url}  [{status}]  events={','.join(ep.events)}")


def run_webhook_test(endpoint_id: str) -> None:
    """Send a test event to a webhook."""
    mgr = get_webhook_manager()
    ep = None
    for e in mgr.list_endpoints():
        if e.id == endpoint_id:
            ep = e
            break
    if not ep:
        click.echo(f"Webhook {endpoint_id} not found", err=True)
        return
    test_event = Event(
        type=EventType.STATUTE_UPDATED,
        source="test",
        data={"test": True},
    )
    click.echo(f"Sending test event to {ep.url}...")
    success = mgr._deliver(ep, test_event)
    click.echo("Delivered" if success else "Failed")
