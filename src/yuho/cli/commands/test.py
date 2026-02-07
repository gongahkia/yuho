"""
Test command - run tests for Yuho statute files.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

import click

from yuho.parser import Parser
from yuho.ast import ASTBuilder
from yuho.cli.error_formatter import Colors, colorize


def run_test(
    file: Optional[str] = None,
    run_all: bool = False,
    json_output: bool = False,
    verbose: bool = False,
    coverage: bool = False,
    coverage_html: Optional[str] = None,
) -> None:
    """
    Run tests for Yuho statute files.

    Args:
        file: Path to .yh file (looks for associated test file)
        run_all: Run all tests in current directory
        json_output: Output results as JSON
        verbose: Enable verbose output
        coverage: Enable coverage tracking
        coverage_html: Path to write HTML coverage report
    """
    test_files: List[Path] = []
    statute_files: List[Path] = []

    if run_all:
        # Find all test files
        cwd = Path.cwd()
        test_files.extend(cwd.glob("test_*.yh"))
        test_files.extend(cwd.glob("tests/*_test.yh"))
        test_files.extend(cwd.glob("**/test_*.yh"))
        # Find statute files for coverage
        if coverage:
            statute_files.extend(f for f in cwd.glob("**/*.yh") if "test" not in f.name.lower())
    elif file:
        file_path = Path(file)
        
        # Check if the file itself is a test file
        is_test_file = file_path.name.startswith("test_") or file_path.name.endswith("_test.yh")
        
        if is_test_file:
            # The file IS the test file, run it directly
            if not file_path.exists():
                click.echo(colorize(f"Test file not found: {file}", Colors.RED), err=True)
                sys.exit(1)
            test_files.append(file_path)
            
            # For coverage, find the associated statute file
            if coverage:
                # test_statute.yh -> statute.yh
                if file_path.name.startswith("test_"):
                    statute_name = file_path.name[5:]  # Remove "test_" prefix
                    statute_path = file_path.parent / statute_name
                    if statute_path.exists():
                        statute_files.append(statute_path)
                # statute_test.yh -> statute.yh
                elif file_path.name.endswith("_test.yh"):
                    statute_name = file_path.stem[:-5] + ".yh"  # Remove "_test" suffix
                    statute_path = file_path.parent / statute_name
                    if not statute_path.exists():
                        # Check parent directory (tests/ -> parent)
                        statute_path = file_path.parent.parent / statute_name
                    if statute_path.exists():
                        statute_files.append(statute_path)
        else:
            # File is a statute, look for associated test file
            if coverage:
                statute_files.append(file_path)
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

    # Initialize coverage tracker if needed
    coverage_tracker = None
    if coverage:
        from yuho.testing.coverage import CoverageTracker
        coverage_tracker = CoverageTracker()

        # Load statutes for coverage tracking
        for statute_file in statute_files:
            try:
                parser = Parser()
                result = parser.parse_file(statute_file)
                if result.is_valid:
                    builder = ASTBuilder(result.source, str(statute_file))
                    ast = builder.build(result.root_node)
                    coverage_tracker.load_statutes_from_ast(ast)
            except Exception:
                continue

    # Run tests
    results = []
    passed = 0
    failed = 0

    for test_file in test_files:
        if verbose:
            click.echo(f"Running {test_file}...")

        result = _run_test_file(test_file, verbose, coverage_tracker)
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

    # Generate coverage report
    if coverage and coverage_tracker:
        report = coverage_tracker.generate_report()

        if coverage_html:
            html_path = Path(coverage_html)
            _generate_html_coverage_report(report, html_path)
            if not json_output:
                click.echo(f"\nCoverage report written to: {html_path}")
        elif not json_output:
            coverage_tracker.print_summary()

    # Summary
    if json_output:
        output_data = {
            "total": len(test_files),
            "passed": passed,
            "failed": failed,
            "results": results,
        }
        if coverage and coverage_tracker:
            output_data["coverage"] = coverage_tracker.generate_report().to_dict()
        print(json.dumps(output_data, indent=2))
    else:
        click.echo()
        if failed == 0:
            click.echo(colorize(f"All {passed} tests passed", Colors.CYAN + Colors.BOLD))
        else:
            click.echo(colorize(f"{passed} passed, {failed} failed", Colors.RED + Colors.BOLD))
            sys.exit(1)


def _run_test_file(test_file: Path, verbose: bool, coverage_tracker=None) -> dict:
    """Run a single test file and return results."""
    result = {
        "file": str(test_file),
        "passed": False,
        "errors": [],
        "assertions": {"passed": 0, "failed": 0},
    }

    # Parse test file
    parser = Parser()
    try:
        parse_result = parser.parse_file(test_file)
    except Exception as e:
        result["errors"].append(f"Parse error: {e}")
        if coverage_tracker:
            coverage_tracker.add_test_result(passed=False)
        return result

    if parse_result.errors:
        result["errors"].extend(f"{e.location}: {e.message}" for e in parse_result.errors)
        if coverage_tracker:
            coverage_tracker.add_test_result(passed=False)
        return result

    # Build AST
    try:
        builder = ASTBuilder(parse_result.source, str(test_file))
        ast = builder.build(parse_result.root_node)
    except Exception as e:
        result["errors"].append(f"AST error: {e}")
        if coverage_tracker:
            coverage_tracker.add_test_result(passed=False)
        return result

    # Evaluate assertions if present
    if hasattr(ast, 'assertions') and ast.assertions:
        env = _build_test_environment(ast)
        for assertion in ast.assertions:
            try:
                passed, error_msg = _evaluate_assertion(assertion, env, verbose)
                if passed:
                    result["assertions"]["passed"] += 1
                else:
                    result["assertions"]["failed"] += 1
                    loc = assertion.source_location
                    loc_str = f"{loc.line}:{loc.col}" if loc else "?"
                    result["errors"].append(f"Assertion failed at {loc_str}: {error_msg}")
            except Exception as e:
                result["assertions"]["failed"] += 1
                result["errors"].append(f"Assertion evaluation error: {e}")

    # Track coverage if enabled
    if coverage_tracker:
        for statute in ast.statutes:
            section = statute.section_number

            # Mark elements as covered
            for elem in (statute.elements or []):
                coverage_tracker.mark_element_covered(
                    section,
                    elem.element_type,
                    elem.name,
                    str(test_file),
                )

            # Mark penalty as covered if present
            if statute.penalty:
                coverage_tracker.mark_penalty_covered(section)

            # Mark illustrations as covered
            if hasattr(statute, 'illustrations') and statute.illustrations:
                for ill in statute.illustrations:
                    if hasattr(ill, 'label') and ill.label:
                        coverage_tracker.mark_illustration_covered(section, ill.label)

        coverage_tracker.add_test_result(passed=result["assertions"]["failed"] == 0)

    # Test passes if no assertion failures and no parse errors
    result["passed"] = result["assertions"]["failed"] == 0 and len(result["errors"]) == 0
    result["stats"] = {
        "statutes": len(ast.statutes),
        "functions": len(ast.function_defs),
        "assertions_total": result["assertions"]["passed"] + result["assertions"]["failed"],
    }

    return result


def _build_test_environment(ast) -> dict:
    """Build an environment mapping variable names to their values."""
    from yuho.ast import nodes

    env = {}

    # Add struct types to environment
    for struct_def in ast.type_defs:
        env[struct_def.name] = {"_type": "struct_def", "fields": {f.name: f for f in struct_def.fields}}

    # Add variables to environment
    for var in ast.variables:
        if var.value:
            env[var.name] = _evaluate_expr(var.value, env)

    return env


def _evaluate_expr(expr, env: dict):
    """Evaluate an expression in the given environment."""
    from yuho.ast import nodes

    if isinstance(expr, nodes.BoolLit):
        return expr.value
    elif isinstance(expr, nodes.IntLit):
        return expr.value
    elif isinstance(expr, nodes.FloatLit):
        return expr.value
    elif isinstance(expr, nodes.StringLit):
        return expr.value
    elif isinstance(expr, nodes.IdentifierNode):
        return env.get(expr.name, f"<unbound:{expr.name}>")
    elif isinstance(expr, nodes.FieldAccessNode):
        base = _evaluate_expr(expr.base, env)
        if isinstance(base, dict):
            return base.get(expr.field_name, f"<no field:{expr.field_name}>")
        # Handle enum-style access like Party.Accused
        if isinstance(base, str) and base.startswith("<unbound:"):
            # This is an enum reference like ConsequenceDefinition.Murder
            type_name = base.replace("<unbound:", "").replace(">", "")
            return f"{type_name}.{expr.field_name}"
        return f"<field access error>"
    elif isinstance(expr, nodes.StructLiteralNode):
        result = {"_struct_name": expr.struct_name}
        for fa in expr.field_values:
            result[fa.name] = _evaluate_expr(fa.value, env)
        return result
    elif isinstance(expr, nodes.BinaryExprNode):
        left = _evaluate_expr(expr.left, env)
        right = _evaluate_expr(expr.right, env)
        if expr.operator == "==":
            return left == right
        elif expr.operator == "!=":
            return left != right
        elif expr.operator == "&&":
            return left and right
        elif expr.operator == "||":
            return left or right
        return f"<binary:{expr.operator}>"
    elif isinstance(expr, nodes.PassExprNode):
        return None
    else:
        return f"<unevaluated:{type(expr).__name__}>"


def _evaluate_assertion(assertion, env: dict, verbose: bool) -> tuple:
    """Evaluate an assertion and return (passed, error_message)."""
    from yuho.ast import nodes

    condition = assertion.condition

    # Handle equality assertions like: assert var.field == ExpectedValue
    if isinstance(condition, nodes.BinaryExprNode) and condition.operator == "==":
        left = _evaluate_expr(condition.left, env)
        right = _evaluate_expr(condition.right, env)

        if left == right:
            return (True, "")
        else:
            return (False, f"expected {right}, got {left}")

    # Handle simple boolean assertions
    result = _evaluate_expr(condition, env)
    if result is True:
        return (True, "")
    elif result is False:
        return (False, "assertion evaluated to FALSE")
    else:
        # Non-boolean result, check for truthiness
        if result:
            return (True, "")
        return (False, f"assertion evaluated to: {result}")


def _generate_html_coverage_report(report, output_path: Path) -> None:
    """Generate an HTML coverage report."""
    report_dict = report.to_dict()
    summary = report_dict["summary"]
    statutes = report_dict["statutes"]

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Yuho Coverage Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }}
        .metric {{
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            color: #007bff;
        }}
        .metric-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .statute {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .statute-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .statute-title {{
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }}
        .coverage-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            color: white;
        }}
        .coverage-high {{ background: #28a745; }}
        .coverage-medium {{ background: #ffc107; color: #333; }}
        .coverage-low {{ background: #dc3545; }}
        .elements-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .elements-table th, .elements-table td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }}
        .elements-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .status-covered {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-uncovered {{
            color: #dc3545;
            font-weight: bold;
        }}
        .generated {{
            text-align: center;
            color: #999;
            font-size: 0.9em;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Yuho Coverage Report</h1>

        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-grid">
                <div class="metric">
                    <div class="metric-value">{summary['overall_coverage']}</div>
                    <div class="metric-label">Overall Coverage</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary['total_statutes']}</div>
                    <div class="metric-label">Statutes</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{summary['passed_tests']}/{summary['total_tests']}</div>
                    <div class="metric-label">Tests Passed</div>
                </div>
            </div>
        </div>
"""

    for section, data in statutes.items():
        coverage_pct = float(data['overall_coverage'].rstrip('%'))
        if coverage_pct >= 80:
            badge_class = "coverage-high"
        elif coverage_pct >= 50:
            badge_class = "coverage-medium"
        else:
            badge_class = "coverage-low"

        html += f"""
        <div class="statute">
            <div class="statute-header">
                <span class="statute-title">Section {section}: {data['title']}</span>
                <span class="coverage-badge {badge_class}">{data['overall_coverage']}</span>
            </div>
            <table class="elements-table">
                <thead>
                    <tr>
                        <th>Element</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Tests</th>
                    </tr>
                </thead>
                <tbody>
"""
        for elem_name, elem_data in data['elements'].items():
            status_class = "status-covered" if elem_data['covered'] else "status-uncovered"
            status_text = "COVERED" if elem_data['covered'] else "NOT COVERED"
            html += f"""
                    <tr>
                        <td>{elem_name.split(':')[1] if ':' in elem_name else elem_name}</td>
                        <td>{elem_data['type']}</td>
                        <td class="{status_class}">{status_text}</td>
                        <td>{elem_data['test_count']}</td>
                    </tr>
"""

        penalty_status = "COVERED" if data['penalty_covered'] else "NOT COVERED"
        penalty_class = "status-covered" if data['penalty_covered'] else "status-uncovered"
        html += f"""
                    <tr>
                        <td>Penalty</td>
                        <td>penalty</td>
                        <td class="{penalty_class}">{penalty_status}</td>
                        <td>-</td>
                    </tr>
                </tbody>
            </table>
        </div>
"""

    html += f"""
        <p class="generated">Generated by Yuho v5 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""

    output_path.write_text(html)

