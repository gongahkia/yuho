"""
LSP command - start Language Server Protocol server.
"""

import sys
from typing import Optional

import click

from yuho.cli.error_formatter import Colors, colorize


def run_lsp(tcp: Optional[int] = None, verbose: bool = False) -> None:
    """
    Start the Language Server Protocol server.

    Args:
        tcp: TCP port to listen on (default: stdio)
        verbose: Enable verbose output
    """
    try:
        from yuho.lsp import YuhoLanguageServer
    except ImportError:
        click.echo(colorize("error: LSP module not available. Install with: pip install yuho[lsp]", Colors.RED), err=True)
        sys.exit(1)

    server = YuhoLanguageServer()

    if tcp:
        if verbose:
            click.echo(f"Starting LSP server on TCP port {tcp}...")
        server.start_tcp("127.0.0.1", tcp)
    else:
        if verbose:
            click.echo("Starting LSP server on stdio...", err=True)
        server.start_io()
