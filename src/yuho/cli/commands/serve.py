"""
Serve command - start MCP server.
"""

import sys
from typing import Optional

import click

from yuho.cli.error_formatter import Colors, colorize


def run_serve(port: int = 8080, host: str = "127.0.0.1", stdio: bool = False, verbose: bool = False) -> None:
    """
    Start the MCP (Model Context Protocol) server.

    Args:
        port: Port to listen on
        host: Host to bind to
        stdio: Use stdio transport
        verbose: Enable verbose output
    """
    try:
        from yuho.mcp import create_server
    except ImportError:
        click.echo(colorize("error: MCP module not available. Install with: pip install yuho[mcp]", Colors.RED), err=True)
        sys.exit(1)

    server = create_server()

    if stdio:
        if verbose:
            click.echo("Starting MCP server on stdio...")
        server.run_stdio()
    else:
        if verbose:
            click.echo(f"Starting MCP server on {host}:{port}...")
        click.echo(colorize(f"Yuho MCP server listening on http://{host}:{port}", Colors.CYAN + Colors.BOLD))
        click.echo(colorize("Press Ctrl+C to stop", Colors.DIM))

        try:
            server.run_http(host=host, port=port)
        except KeyboardInterrupt:
            click.echo("\nShutting down...")
