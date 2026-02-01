"""
Contribute command - validate and package statutes for sharing.
"""

import json
import sys
import tarfile
from pathlib import Path
from typing import Optional

import click

from yuho.parser import Parser
from yuho.ast import ASTBuilder
from yuho.cli.error_formatter import Colors, colorize


def run_contribute(file: str, package: bool = False, output: Optional[str] = None, verbose: bool = False) -> None:
    """
    Validate a statute file for contribution.

    Args:
        file: Path to the .yh file
        package: Create distributable package
        output: Output path for package
        verbose: Enable verbose output
    """
    file_path = Path(file)

    if verbose:
        click.echo(f"Validating {file_path}...")

    # Parse and validate
    parser = Parser()
    try:
        result = parser.parse_file(file_path)
    except FileNotFoundError:
        click.echo(colorize(f"error: File not found: {file}", Colors.RED), err=True)
        sys.exit(1)

    if result.errors:
        click.echo(colorize(f"FAIL: Parse errors in {file}", Colors.RED))
        for err in result.errors:
            click.echo(f"  {err.location}: {err.message}")
        sys.exit(1)

    builder = ASTBuilder(result.source, str(file_path))
    ast = builder.build(result.root_node)

    # Check for required metadata
    if not ast.statutes:
        click.echo(colorize("FAIL: No statute definitions found", Colors.RED))
        sys.exit(1)

    # Check for associated tests
    test_paths = [
        file_path.parent / f"test_{file_path.name}",
        file_path.parent / "tests" / f"{file_path.stem}_test.yh",
    ]
    test_file = None
    for tp in test_paths:
        if tp.exists():
            test_file = tp
            break

    if not test_file:
        click.echo(colorize("WARNING: No test file found", Colors.YELLOW))
        click.echo(f"  Expected: test_{file_path.name} or tests/{file_path.stem}_test.yh")

    # Check for metadata.toml
    metadata_path = file_path.parent / "metadata.toml"
    has_metadata = metadata_path.exists()
    if not has_metadata:
        click.echo(colorize("WARNING: No metadata.toml found", Colors.YELLOW))

    # Summary
    click.echo(colorize(f"OK: {file_path} is valid for contribution", Colors.CYAN + Colors.BOLD))
    click.echo(f"  Statutes: {len(ast.statutes)}")
    for statute in ast.statutes:
        title = statute.title.value if statute.title else "(untitled)"
        click.echo(f"    - Section {statute.section_number}: {title}")

    if test_file:
        click.echo(f"  Tests: {test_file}")
    if has_metadata:
        click.echo(f"  Metadata: {metadata_path}")

    # Package if requested
    if package:
        _create_package(file_path, test_file, metadata_path if has_metadata else None, output, verbose)


def _create_package(
    statute_file: Path,
    test_file: Optional[Path],
    metadata_file: Optional[Path],
    output: Optional[str],
    verbose: bool
) -> None:
    """Create a .yhpkg archive."""
    # Determine output path
    if output:
        pkg_path = Path(output)
    else:
        pkg_path = statute_file.parent / f"{statute_file.stem}.yhpkg"

    if verbose:
        click.echo(f"Creating package: {pkg_path}")

    with tarfile.open(pkg_path, "w:gz") as tar:
        # Add statute file
        tar.add(statute_file, arcname=statute_file.name)

        # Add test file if exists
        if test_file:
            tar.add(test_file, arcname=f"tests/{test_file.name}")

        # Add metadata if exists
        if metadata_file:
            tar.add(metadata_file, arcname="metadata.toml")

    click.echo(colorize(f"Package created: {pkg_path}", Colors.CYAN + Colors.BOLD))
