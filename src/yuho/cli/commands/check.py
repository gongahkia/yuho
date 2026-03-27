"""
Check command - parse and validate Yuho files.
"""

import json
import sys
from pathlib import Path
from typing import Any, Optional

import click

from yuho.cli.error_formatter import format_errors, format_suggestion, Colors, colorize
from yuho.services.analysis import analyze_file, analyze_source
from yuho.output.sarif import make_sarif_result, to_sarif


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
    metrics: bool = False,
    output_format: str = "text",
    syntax_only: bool = False,
) -> None:
    """
    Parse and validate a Yuho source file.

    Args:
        file: Path to the .yh file
        json_output: Output errors as JSON
        verbose: Enable verbose output
        explain_errors: Show detailed explanations for errors
        metrics: Include code_scale and clock_load_scale metrics in output
        syntax_only: Skip semantic analysis and lint phase reporting beyond parse/AST
    """
    if output_format == "json":
        json_output = True
    file_label = "<stdin>" if file == "-" else str(Path(file))

    if verbose:
        click.echo(f"Checking {file_label}...")

    # Parse + AST via shared analysis service
    if file == "-":
        stdin_source = sys.stdin.read()
        analysis = analyze_source(stdin_source, file=file_label, run_semantic=not syntax_only)
    else:
        analysis = analyze_file(file, run_semantic=not syntax_only)

    payload = analysis.validation_payload(include_metrics=metrics)
    payload["mode"] = "syntax-only" if syntax_only else "full"

    if explain_errors:
        for item in payload["errors"]:
            if item["stage"] != "parse":
                continue
            item["explanation"] = get_error_explanation(
                item["message"],
                item.get("node_type"),
            )

    if output_format == "sarif":
        sarif_results = [
            make_sarif_result(
                f"yuho/{item['stage']}",
                item["message"],
                file_label,
                line=item.get("line") or 1,
                col=item.get("column") or 1,
                level=item.get("severity", "error"),
            )
            for item in payload["errors"] + payload["warnings"] + payload["lint_warnings"]
        ]
        print(to_sarif(sarif_results))
        sys.exit(1 if payload["errors"] else 0)

    if json_output:
        print(json.dumps(payload, indent=2))
        sys.exit(1 if payload["errors"] else 0)

    phase_labels = []
    for name, phase in payload["phases"].items():
        valid = phase["valid"]
        if valid is True:
            status = "OK"
        elif valid is False:
            status = "FAIL"
        else:
            status = "SKIP"
        phase_labels.append(f"{name}={status}")

    if payload["errors"]:
        click.echo(
            colorize(f"INVALID: {file_label}", Colors.RED + Colors.BOLD),
            err=True,
        )
    else:
        click.echo(colorize(f"VALID: {file_label}", Colors.CYAN + Colors.BOLD))
    click.echo(f"  phases: {', '.join(phase_labels)}")

    if analysis.parse_errors:
        error_output = format_errors(analysis.parse_errors, analysis.source, file_label)
        click.echo(error_output, err=True)
        for err in analysis.parse_errors:
            suggestion = format_suggestion(err, analysis.source)
            if suggestion:
                click.echo(colorize(f"  hint: {suggestion}", Colors.YELLOW), err=True)
            if explain_errors:
                explanation = get_error_explanation(err.message, err.node_type)
                if explanation:
                    click.echo(
                        colorize("\n  Explanation:", Colors.CYAN + Colors.BOLD),
                        err=True,
                    )
                    for line in explanation.strip().split("\n"):
                        click.echo(colorize(f"    {line}", Colors.DIM), err=True)
                    click.echo("", err=True)

    for item in payload["errors"]:
        if item["stage"] == "parse":
            continue
        location = ""
        if item.get("line") is not None:
            location = f" {item['line']}:{item.get('column') or 1}"
        click.echo(
            colorize(
                f"  {item['stage']}{location}: {item['message']}",
                Colors.RED,
            ),
            err=True,
        )

    combined_warnings = payload["warnings"] + payload["lint_warnings"]
    for warning in combined_warnings:
        stage = warning.get("stage", "warning")
        detail = warning["message"]
        if warning.get("statute_section"):
            detail = f"s{warning['statute_section']}: {detail}"
        click.echo(colorize(f"  {stage}: {detail}", Colors.YELLOW))

    if verbose and analysis.ast_summary is not None:
        stats = analysis.ast_summary.to_dict()
        click.echo(f"  imports: {stats['imports']}")
        click.echo(f"  structs: {stats['structs']}")
        click.echo(f"  functions: {stats['functions']}")
        click.echo(f"  statutes: {stats['statutes']}")
        click.echo(f"  variables: {stats['variables']}")

    if metrics:
        if analysis.code_scale:
            code_scale = analysis.code_scale.to_dict()
            click.echo(
                "  code_scale: "
                f"source_loc={code_scale['source_loc']}, "
                f"ast_nodes={code_scale['ast_nodes']}, "
                f"statute_count={code_scale['statute_count']}, "
                f"definition_count={code_scale['definition_count']}"
            )
        if analysis.clock_load_scale:
            clock_load = analysis.clock_load_scale.to_dict()
            click.echo(
                "  clock_load_scale: "
                f"parse_ms={clock_load['parse_ms']:.3f}, "
                f"ast_build_ms={clock_load['ast_build_ms']:.3f}, "
                f"total_ms={clock_load['total_ms']:.3f}"
            )

    sys.exit(1 if payload["errors"] else 0)
