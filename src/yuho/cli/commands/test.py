"""
Test command - run tests for Yuho statute files.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List

import click

from yuho.parser import Parser
from yuho.ast import ASTBuilder
from yuho.cli.error_formatter import Colors, colorize


def run_test(file: Optional[str] = None, run_all: bool = False, json_output: bool = False, verbose: bool = False) -> None:
    """
    Run tests for Yuho statute files.

    Args:
        file: Path to .yh file (looks for associated test file)
        run_all: Run all tests in current directory
        json_output: Output results as JSON
        verbose: Enable verbose output
    """
    test_files: List[Path] = []

    if run_all:
        # Find all test files
        cwd = Path.cwd()
        test_files.extend(cwd.glob("test_*.yh"))
        test_files.extend(cwd.glob("tests/*_test.yh"))
        test_files.extend(cwd.glob("**/test_*.yh"))
    elif file:
        file_path = Path(file)
        # Look for associated test file
        candidates = [
            file_path.parent / f"test_{file_path.name}",
            file_path.parent / "tests" / f"{file_path.stem}_test.yh",
            file_path.parent / "tests" / f"test_{file_path.name}",
        ]
        for candidate in candidates:
            if candidate.exists():
                test_files.append(candidate)
                break

        if not test_files:
            click.echo(colorize(f"No test file found for {file}", Colors.YELLOW))
            click.echo("Expected:")
            for c in candidates:
                click.echo(f"  - {c}")
            sys.exit(1)
    else:
        click.echo(colorize("error: Specify a file or use --all", Colors.RED), err=True)
        sys.exit(1)

    if not test_files:
        click.echo(colorize("No test files found", Colors.YELLOW))
        sys.exit(0)

    # Run tests
    results = []
    passed = 0
    failed = 0

    for test_file in test_files:
        if verbose:
            click.echo(f"Running {test_file}...")

        result = _run_test_file(test_file, verbose)
        results.append(result)

        if result["passed"]:
            passed += 1
            if not json_output:
                click.echo(colorize(f"  PASS: {test_file.name}", Colors.CYAN))
        else:
            failed += 1
            if not json_output:
                click.echo(colorize(f"  FAIL: {test_file.name}", Colors.RED))
                for err in result.get("errors", []):
                    click.echo(f"    - {err}")

    # Summary
    if json_output:
        print(json.dumps({
            "total": len(test_files),
            "passed": passed,
            "failed": failed,
            "results": results,
        }, indent=2))
    else:
        click.echo()
        if failed == 0:
            click.echo(colorize(f"All {passed} tests passed", Colors.CYAN + Colors.BOLD))
        else:
            click.echo(colorize(f"{passed} passed, {failed} failed", Colors.RED + Colors.BOLD))
            sys.exit(1)


def _run_test_file(test_file: Path, verbose: bool) -> dict:
    """Run a single test file and return results."""
    result = {
        "file": str(test_file),
        "passed": False,
        "errors": [],
    }

    # Parse test file
    parser = Parser()
    try:
        parse_result = parser.parse_file(test_file)
    except Exception as e:
        result["errors"].append(f"Parse error: {e}")
        return result

    if parse_result.errors:
        result["errors"].extend(f"{e.location}: {e.message}" for e in parse_result.errors)
        return result

    # Build AST
    try:
        builder = ASTBuilder(parse_result.source, str(test_file))
        ast = builder.build(parse_result.root_node)
    except Exception as e:
        result["errors"].append(f"AST error: {e}")
        return result

    # For now, just verify it parses successfully
    # TODO: Implement actual test assertions once test format is defined
    result["passed"] = True
    result["stats"] = {
        "statutes": len(ast.statutes),
        "functions": len(ast.function_defs),
    }

    return result
