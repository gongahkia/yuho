"""
Verify command - formal verification via Alloy and/or Z3.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import click

from yuho.services.analysis import analyze_file
from yuho.verify.alloy import AlloyAnalyzer, AlloyGenerator
from yuho.verify.combined import CombinedVerifier
from yuho.verify.z3_solver import Z3Solver


def run_verify(
    file: Optional[str],
    *,
    engine: str = "combined",
    alloy_jar: Optional[str] = None,
    alloy_timeout: int = 30,
    z3_timeout_ms: int = 5000,
    capabilities_only: bool = False,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """Run formal verification on a Yuho file, or report backend capabilities."""
    alloy_analyzer = AlloyAnalyzer(alloy_jar=alloy_jar, timeout=alloy_timeout)
    z3_solver = Z3Solver(timeout_ms=z3_timeout_ms)
    capabilities = _build_capabilities(
        alloy_analyzer=alloy_analyzer,
        z3_solver=z3_solver,
        alloy_jar=alloy_jar,
    )

    if capabilities_only:
        _emit_capabilities(capabilities, json_output=json_output)
        sys.exit(0)

    if not file:
        click.echo("error: FILE is required unless --capabilities is set.", err=True)
        sys.exit(2)

    engine_key = engine.lower()
    if engine_key == "alloy" and not capabilities["alloy"]["available"]:
        _emit_unavailable("alloy", capabilities["alloy"]["reason"], json_output)
        sys.exit(2)
    if engine_key == "z3" and not capabilities["z3"]["available"]:
        _emit_unavailable("z3", capabilities["z3"]["reason"], json_output)
        sys.exit(2)
    if engine_key == "combined" and not capabilities["combined"]["available"]:
        _emit_unavailable("combined", capabilities["combined"]["reason"], json_output)
        sys.exit(2)

    try:
        analysis = analyze_file(file, run_semantic=False)
    except ImportError as exc:
        message = f"Parser runtime unavailable: {exc}"
        if json_output:
            print(json.dumps({"ok": False, "engine": engine_key, "error": message}, indent=2))
        else:
            click.echo(f"error: {message}", err=True)
        sys.exit(2)
    except Exception as exc:
        message = f"Failed to parse input for verification: {exc}"
        if json_output:
            print(json.dumps({"ok": False, "engine": engine_key, "error": message}, indent=2))
        else:
            click.echo(f"error: {message}", err=True)
        sys.exit(1)
    if analysis.parse_errors:
        if json_output:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "engine": engine_key,
                        "error": "Parse failed",
                        "parse_errors": [
                            {
                                "message": err.message,
                                "line": err.location.line,
                                "col": err.location.col,
                            }
                            for err in analysis.parse_errors
                        ],
                    },
                    indent=2,
                )
            )
        else:
            click.echo(
                f"error: cannot verify {file}; parser reported {len(analysis.parse_errors)} error(s).",
                err=True,
            )
            if verbose:
                for err in analysis.parse_errors:
                    click.echo(
                        f"  - {err.location.file}:{err.location.line}:{err.location.col}: {err.message}",
                        err=True,
                    )
        sys.exit(1)

    if analysis.ast is None:
        ast_error = next((e.message for e in analysis.errors if e.stage == "ast"), "Unknown AST error")
        if json_output:
            print(json.dumps({"ok": False, "engine": engine_key, "error": ast_error}, indent=2))
        else:
            click.echo(f"error: cannot verify {file}; failed to build AST: {ast_error}", err=True)
        sys.exit(1)

    ast = analysis.ast
    if engine_key == "alloy":
        generator = AlloyGenerator()
        model = generator.generate(ast)
        results = alloy_analyzer.analyze(model)
        failures = [r for r in results if r.violated]
        ok = len(failures) == 0
        if json_output:
            print(
                json.dumps(
                    {
                        "ok": ok,
                        "engine": "alloy",
                        "capabilities": capabilities,
                        "failures": [f.__dict__ for f in failures],
                        "results": [r.__dict__ for r in results],
                    },
                    indent=2,
                )
            )
        else:
            click.echo(f"Alloy verification: {'PASS' if ok else 'FAIL'}")
            if not ok:
                for failure in failures:
                    click.echo(f"  - {failure.assertion_name}: {failure.message}", err=True)
        sys.exit(0 if ok else 1)

    if engine_key == "z3":
        ok, diagnostics = z3_solver.check_statute_consistency(ast)
        failures = [d for d in diagnostics if not d.passed]
        if json_output:
            print(
                json.dumps(
                    {
                        "ok": ok,
                        "engine": "z3",
                        "capabilities": capabilities,
                        "failures": [d.__dict__ for d in failures],
                        "results": [d.__dict__ for d in diagnostics],
                    },
                    indent=2,
                )
            )
        else:
            click.echo(f"Z3 verification: {'PASS' if ok else 'FAIL'}")
            if failures:
                for failure in failures:
                    click.echo(f"  - {failure.check_name}: {failure.message}", err=True)
        sys.exit(0 if ok else 1)

    verifier = CombinedVerifier(
        alloy_jar=alloy_jar,
        alloy_timeout=alloy_timeout,
        z3_timeout_ms=z3_timeout_ms,
    )
    combined = verifier.verify(ast)
    alloy_failed = any(r.violated for r in combined.alloy_results) if combined.alloy_available else False
    z3_failed = any(not d.passed for d in combined.z3_results) if combined.z3_available else False
    ok = not alloy_failed and not z3_failed and (combined.alloy_available or combined.z3_available)

    if json_output:
        print(
            json.dumps(
                {
                    "ok": ok,
                    "engine": "combined",
                    "capabilities": capabilities,
                    "result": combined.to_dict(),
                },
                indent=2,
            )
        )
    else:
        click.echo(f"Combined verification: {'PASS' if ok else 'FAIL'}")
        click.echo(f"  {combined.message}")
        if not combined.alloy_available:
            click.echo(f"  Alloy unavailable: {capabilities['alloy']['reason']}")
        if not combined.z3_available:
            click.echo(f"  Z3 unavailable: {capabilities['z3']['reason']}")

    sys.exit(0 if ok else 1)


def _build_capabilities(
    *,
    alloy_analyzer: AlloyAnalyzer,
    z3_solver: Z3Solver,
    alloy_jar: Optional[str],
) -> Dict[str, Dict[str, Any]]:
    alloy_available = alloy_analyzer.is_available()
    z3_available = z3_solver.is_available()
    java_available = shutil.which("java") is not None

    if alloy_available:
        alloy_reason = "Alloy analyzer available"
    elif alloy_jar:
        alloy_reason = f"Alloy JAR not found at {Path(alloy_jar)}"
    elif not java_available:
        alloy_reason = "Java runtime not found; install Java and provide --alloy-jar"
    else:
        alloy_reason = "Alloy JAR not found; provide --alloy-jar or install to a known location"

    if z3_available:
        z3_reason = "Z3 solver available"
    else:
        z3_reason = "z3-solver Python package is not installed"

    combined_available = alloy_available or z3_available
    combined_reason = (
        "At least one verifier backend is available"
        if combined_available
        else "No verification backends available (Alloy and Z3 are both unavailable)"
    )

    return {
        "alloy": {"available": alloy_available, "reason": alloy_reason},
        "z3": {"available": z3_available, "reason": z3_reason},
        "combined": {"available": combined_available, "reason": combined_reason},
    }


def _emit_capabilities(capabilities: Dict[str, Dict[str, Any]], *, json_output: bool) -> None:
    if json_output:
        print(json.dumps({"capabilities": capabilities}, indent=2))
        return

    click.echo("Verification capabilities:")
    click.echo(
        f"  Alloy:   {'available' if capabilities['alloy']['available'] else 'unavailable'}"
        f" ({capabilities['alloy']['reason']})"
    )
    click.echo(
        f"  Z3:      {'available' if capabilities['z3']['available'] else 'unavailable'}"
        f" ({capabilities['z3']['reason']})"
    )
    click.echo(
        f"  Combined:{'available' if capabilities['combined']['available'] else 'unavailable'}"
        f" ({capabilities['combined']['reason']})"
    )


def _emit_unavailable(engine: str, reason: str, json_output: bool) -> None:
    if json_output:
        print(json.dumps({"ok": False, "engine": engine, "error": reason}, indent=2))
        return
    click.echo(f"error: {engine} verification unavailable: {reason}", err=True)
