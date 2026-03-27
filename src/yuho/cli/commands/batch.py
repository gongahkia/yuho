"""
Batch operations for processing multiple Yuho files.
"""

import json
import sys
from pathlib import Path
from typing import Optional, List

import click

from yuho.cli.error_formatter import Colors, colorize
from yuho.services.analysis import analyze_file


def run_batch_check(
    directory: str,
    *,
    recursive: bool = True,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Check all .yh files in a directory.

    Reports per-file pass/fail and aggregate summary.
    """
    files = _find_yh_files(directory, recursive)
    if not files:
        click.echo(colorize(f"No .yh files found in {directory}", Colors.RED), err=True)
        sys.exit(1)
    passed = 0
    failed = 0
    results = []
    for f in files:
        result = analyze_file(f)
        ok = result.is_valid
        entry = {"file": str(f), "valid": ok}
        if not ok:
            entry["errors"] = [e.message for e in result.errors]
        results.append(entry)
        if ok:
            passed += 1
            if not json_output:
                click.echo(colorize(f"  PASS  {f}", Colors.CYAN))
        else:
            failed += 1
            if not json_output:
                click.echo(colorize(f"  FAIL  {f}", Colors.RED))
                for e in result.errors:
                    click.echo(f"        {e.message}")
    if json_output:
        print(
            json.dumps(
                {"total": len(files), "passed": passed, "failed": failed, "results": results},
                indent=2,
            )
        )
    else:
        click.echo()
        if failed == 0:
            click.echo(colorize(f"All {passed} files passed", Colors.CYAN + Colors.BOLD))
        else:
            click.echo(
                colorize(
                    f"{passed} passed, {failed} failed out of {len(files)}",
                    Colors.RED + Colors.BOLD,
                )
            )
    if failed > 0:
        sys.exit(1)


def run_batch_transpile(
    directory: str,
    *,
    target: str = "json",
    output_dir: Optional[str] = None,
    recursive: bool = True,
    json_output: bool = False,
    verbose: bool = False,
) -> None:
    """
    Transpile all .yh files in a directory.
    """
    from yuho.transpile import TranspileTarget, get_transpiler

    files = _find_yh_files(directory, recursive)
    if not files:
        click.echo(colorize(f"No .yh files found in {directory}", Colors.RED), err=True)
        sys.exit(1)
    try:
        transpile_target = TranspileTarget.from_string(target)
        transpiler = get_transpiler(transpile_target)
    except ValueError as e:
        click.echo(colorize(f"error: {e}", Colors.RED), err=True)
        sys.exit(1)
    out_dir = Path(output_dir) if output_dir else Path(directory) / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    failed = 0
    for f in files:
        result = analyze_file(f, run_semantic=False)
        if not result.ast:
            failed += 1
            results.append({"file": str(f), "error": "parse/AST failed"})
            if not json_output:
                click.echo(colorize(f"  FAIL  {f}", Colors.RED))
            continue
        try:
            output_text = transpiler.transpile(result.ast)
            rel = f.relative_to(Path(directory).resolve()) if f.is_absolute() else f
            out_path = out_dir / rel.with_suffix(transpile_target.file_extension)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(output_text, encoding="utf-8")
            results.append({"file": str(f), "output": str(out_path)})
            if not json_output:
                click.echo(f"  {f} -> {out_path}")
        except Exception as e:
            failed += 1
            results.append({"file": str(f), "error": str(e)})
            if not json_output:
                click.echo(colorize(f"  FAIL  {f}: {e}", Colors.RED))
    if json_output:
        print(
            json.dumps(
                {"total": len(files), "failed": failed, "target": target, "results": results},
                indent=2,
            )
        )
    else:
        click.echo(f"\nTranspiled {len(files) - failed}/{len(files)} files to {target}")
    if failed > 0:
        sys.exit(1)


def _find_yh_files(directory: str, recursive: bool) -> List[Path]:
    """Find all .yh files in directory."""
    base = Path(directory).resolve()
    if not base.is_dir():
        return []
    pattern = "**/*.yh" if recursive else "*.yh"
    return sorted(base.glob(pattern))
