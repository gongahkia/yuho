"""
Check command - parse and validate Yuho files.
"""

import json
import sys
from pathlib import Path
from typing import Optional

import click

from yuho.parser import Parser
from yuho.ast import ASTBuilder
from yuho.cli.error_formatter import format_errors, format_suggestion, Colors, colorize


def run_check(file: str, json_output: bool = False, verbose: bool = False) -> None:
    """
    Parse and validate a Yuho source file.

    Args:
        file: Path to the .yh file
        json_output: Output errors as JSON
        verbose: Enable verbose output
    """
    file_path = Path(file)

    if verbose:
        click.echo(f"Checking {file_path}...")

    # Parse the file
    parser = Parser()
    try:
        result = parser.parse_file(file_path)
    except FileNotFoundError:
        if json_output:
            print(json.dumps({"valid": False, "errors": [{"message": f"File not found: {file}"}]}))
        else:
            click.echo(colorize(f"error: File not found: {file}", Colors.RED), err=True)
        sys.exit(1)
    except UnicodeDecodeError as e:
        if json_output:
            print(json.dumps({"valid": False, "errors": [{"message": f"Invalid UTF-8: {e}"}]}))
        else:
            click.echo(colorize(f"error: Invalid UTF-8 encoding: {e}", Colors.RED), err=True)
        sys.exit(1)

    # Report parse errors
    if result.errors:
        if json_output:
            errors_json = [
                {
                    "message": err.message,
                    "location": {
                        "file": err.location.file,
                        "line": err.location.line,
                        "col": err.location.col,
                        "end_line": err.location.end_line,
                        "end_col": err.location.end_col,
                    },
                    "node_type": err.node_type,
                }
                for err in result.errors
            ]
            print(json.dumps({"valid": False, "errors": errors_json}, indent=2))
        else:
            error_output = format_errors(result.errors, result.source, str(file_path))
            click.echo(error_output, err=True)

            # Add suggestions
            for err in result.errors:
                suggestion = format_suggestion(err, result.source)
                if suggestion:
                    click.echo(colorize(f"  hint: {suggestion}", Colors.YELLOW), err=True)

        sys.exit(1)

    # Build AST
    try:
        builder = ASTBuilder(result.source, str(file_path))
        ast = builder.build(result.root_node)
    except Exception as e:
        if json_output:
            print(json.dumps({"valid": False, "errors": [{"message": f"AST error: {e}"}]}))
        else:
            click.echo(colorize(f"error: Failed to build AST: {e}", Colors.RED), err=True)
        sys.exit(1)

    # Success
    if json_output:
        summary = {
            "valid": True,
            "file": str(file_path),
            "stats": {
                "imports": len(ast.imports),
                "structs": len(ast.type_defs),
                "functions": len(ast.function_defs),
                "statutes": len(ast.statutes),
                "variables": len(ast.variables),
            }
        }
        print(json.dumps(summary, indent=2))
    else:
        click.echo(colorize(f"OK: {file_path}", Colors.CYAN + Colors.BOLD))
        if verbose:
            click.echo(f"  {len(ast.imports)} imports")
            click.echo(f"  {len(ast.type_defs)} type definitions")
            click.echo(f"  {len(ast.function_defs)} functions")
            click.echo(f"  {len(ast.statutes)} statutes")
            click.echo(f"  {len(ast.variables)} variables")

    sys.exit(0)
