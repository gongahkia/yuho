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


# Detailed explanations for common error patterns
ERROR_EXPLANATIONS = {
    "Unexpected syntax": """
This error occurs when the parser encounters code it doesn't recognize.

Common causes:
  - Missing or extra punctuation (commas, braces, colons)
  - Typo in a keyword (e.g., 'strcut' instead of 'struct')
  - Using syntax from another language that Yuho doesn't support
  - Incomplete statement or expression

How to fix:
  1. Check for typos in keywords: struct, fn, match, case, consequence, etc.
  2. Ensure all braces {{ }} and parentheses ( ) are balanced
  3. Verify that statements are complete (not cut off mid-expression)
  4. Compare your code against examples in the documentation
""",
    "Missing semicolon": """
Yuho doesn't require semicolons in most places, but they can be used
optionally at the end of statements.

This error usually means the parser expected a statement terminator
but found something else. Check that:
  - The previous statement is complete
  - You're not missing a closing brace or parenthesis
  - Field assignments in structs are separated by commas
""",
    "Missing closing brace": """
A closing brace '}}' is expected but was not found.

Common causes:
  - Forgetting to close a struct, function, or match block
  - Nested braces that don't match up
  - An error earlier in the file causing the parser to get confused

How to fix:
  1. Count your opening {{ and closing }} braces - they should match
  2. Use editor features to highlight matching braces
  3. Look for the last complete block before the error
""",
    "Expected identifier": """
An identifier (name) was expected but something else was found.

In Yuho, identifiers:
  - Start with a letter or underscore
  - Can contain letters, numbers, and underscores
  - Are case-sensitive
  - Cannot be reserved keywords

Examples of valid identifiers: myVar, _private, CamelCase, snake_case
""",
    "Expected type annotation": """
A type annotation was expected but not found.

In Yuho, variable declarations require explicit types:

  Correct:   int count := 0
  Incorrect: count := 0

Built-in types: int, float, bool, string, money, percent, date, duration
User-defined types: Any struct name you've defined
""",
    "MISSING": """
The parser expected to find something that wasn't there.

This usually indicates incomplete code. Check that:
  - All statements and expressions are complete
  - Required parts of syntax aren't missing
  - The file didn't get truncated
""",
}


def get_error_explanation(error_message: str, node_type: Optional[str]) -> Optional[str]:
    """Get a detailed explanation for an error."""
    # Check node type first
    if node_type and node_type.startswith("MISSING:"):
        missing_what = node_type.replace("MISSING:", "")
        if missing_what in ERROR_EXPLANATIONS:
            return ERROR_EXPLANATIONS[missing_what]
        return ERROR_EXPLANATIONS.get("MISSING")

    # Check error message patterns
    for pattern, explanation in ERROR_EXPLANATIONS.items():
        if pattern in error_message:
            return explanation

    return None


def run_check(
    file: str,
    json_output: bool = False,
    verbose: bool = False,
    explain_errors: bool = False,
) -> None:
    """
    Parse and validate a Yuho source file.

    Args:
        file: Path to the .yh file
        json_output: Output errors as JSON
        verbose: Enable verbose output
        explain_errors: Show detailed explanations for errors
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
                    "explanation": get_error_explanation(err.message, err.node_type) if explain_errors else None,
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

                # Add detailed explanation if requested
                if explain_errors:
                    explanation = get_error_explanation(err.message, err.node_type)
                    if explanation:
                        click.echo(colorize("\n  Explanation:", Colors.CYAN + Colors.BOLD), err=True)
                        for line in explanation.strip().split("\n"):
                            click.echo(colorize(f"    {line}", Colors.DIM), err=True)
                        click.echo("", err=True)

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
