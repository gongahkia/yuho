"""
Serve command - start MCP server.
"""

import sys
from typing import Optional

import click

from yuho.cli.error_formatter import Colors, colorize


def run_serve(
    port: Optional[int] = None,
    host: Optional[str] = None,
    stdio: bool = False,
    verbose: bool = False,
) -> None:
    """
    Start the MCP (Model Context Protocol) server.

    Args:
        port: Port to listen on (defaults to config mcp.port)
        host: Host to bind to (defaults to config mcp.host)
        stdio: Use stdio transport
        verbose: Enable verbose output
    """
    try:
        from yuho.mcp import create_server
    except ImportError:
        click.echo(colorize("error: MCP module not available. Install with: pip install yuho[mcp]", Colors.RED), err=True)
        sys.exit(1)

    from yuho.config.loader import get_config

    mcp_config = get_config().mcp
    resolved_host = host or mcp_config.host
    resolved_port = port if port is not None else mcp_config.port

    server = create_server()

    if stdio:
        if verbose:
            click.echo("Starting MCP server on stdio...")
        server.run_stdio()
    else:
        if verbose:
            click.echo(f"Starting MCP server on {resolved_host}:{resolved_port}...")
        click.echo(colorize(f"Yuho MCP server listening on http://{resolved_host}:{resolved_port}", Colors.CYAN + Colors.BOLD))
        click.echo(colorize("Press Ctrl+C to stop", Colors.DIM))

        try:
            server.run_http(host=resolved_host, port=resolved_port)
        except KeyboardInterrupt:
            click.echo("\nShutting down...")
