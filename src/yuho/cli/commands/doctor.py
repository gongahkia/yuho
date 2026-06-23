"""Environment preflight for local Yuho installs."""

from __future__ import annotations

import importlib.util
import json
import os
import platform
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import click

from yuho import __version__
from yuho.services.analysis import analyze_file, analyze_source


DEFAULT_SAMPLE = Path("library/penal_code/s415_cheating/statute.yh")


@dataclass
class DoctorCheck:
    name: str
    status: str
    detail: str
    hint: Optional[str] = None


def run_doctor(
    *,
    sample: Optional[str] = None,
    json_output: bool = False,
    strict: bool = False,
) -> None:
    """Report install/runtime readiness for local Yuho usage."""
    checks: list[DoctorCheck] = []
    checks.extend(_runtime_checks())
    checks.append(_parser_check())
    checks.append(_sample_check(Path(sample) if sample else DEFAULT_SAMPLE))
    checks.extend(_optional_python_checks())
    checks.extend(_external_tool_checks())

    counts = {
        "ok": sum(1 for check in checks if check.status == "ok"),
        "warn": sum(1 for check in checks if check.status == "warn"),
        "fail": sum(1 for check in checks if check.status == "fail"),
    }
    ok = counts["fail"] == 0 and (counts["warn"] == 0 or not strict)
    next_steps = _next_steps(counts, strict)

    if json_output:
        print(
            json.dumps(
                {
                    "ok": ok,
                    "version": __version__,
                    "strict": strict,
                    "counts": counts,
                    "checks": [asdict(check) for check in checks],
                    "next_steps": next_steps,
                },
                indent=2,
            )
        )
    else:
        click.echo("Yuho doctor")
        for check in checks:
            label = {"ok": "OK", "warn": "WARN", "fail": "FAIL"}[check.status]
            click.echo(f"[{label}] {check.name}: {check.detail}")
            if check.hint:
                click.echo(f"      hint: {check.hint}")
        click.echo(f"summary: {counts['ok']} ok, {counts['warn']} warn, {counts['fail']} fail")
        for step in next_steps:
            click.echo(f"next: {step}")

    sys.exit(0 if ok else 1)


def _runtime_checks() -> list[DoctorCheck]:
    checks = [
        DoctorCheck(
            "yuho",
            "ok",
            f"{__version__} ({Path(__file__).resolve().parents[3]})",
        ),
        DoctorCheck(
            "python",
            "ok" if sys.version_info >= (3, 10) else "fail",
            f"{platform.python_version()} ({sys.executable})",
            None if sys.version_info >= (3, 10) else "install Python 3.10 or newer",
        ),
    ]

    executable = shutil.which("yuho")
    if executable:
        checks.append(DoctorCheck("executable", "ok", executable))
    else:
        checks.append(
            DoctorCheck(
                "executable",
                "warn",
                "yuho is not on PATH",
                "use `uv run yuho ...` or activate `.venv`",
            )
        )
    return checks


def _parser_check() -> DoctorCheck:
    source = """
statute 1 "Doctor" {
  elements {
    actus_reus act := "does an act";
  }
}
"""
    try:
        analysis = analyze_source(source, file="<doctor>", run_semantic=True)
    except Exception as exc:
        return DoctorCheck(
            "parser",
            "fail",
            f"{type(exc).__name__}: {exc}",
            "reinstall from repo root with `uv pip install -e '.[dev]'`",
        )

    if analysis.parse_errors or analysis.ast is None or analysis.errors:
        return DoctorCheck(
            "parser",
            "fail",
            "inline statute failed parser/AST/semantic analysis",
            "run `yuho check --json FILE.yh` for diagnostics",
        )
    return DoctorCheck("parser", "ok", "inline statute parses and validates")


def _sample_check(sample: Path) -> DoctorCheck:
    if not sample.exists():
        return DoctorCheck(
            "sample",
            "warn",
            f"{sample} not found",
            "run from repo root or pass `--sample PATH`",
        )
    try:
        analysis = analyze_file(sample, run_semantic=True)
    except Exception as exc:
        return DoctorCheck("sample", "fail", f"{sample}: {type(exc).__name__}: {exc}")

    if analysis.parse_errors or analysis.ast is None or analysis.errors:
        return DoctorCheck(
            "sample",
            "fail",
            f"{sample} failed validation",
            f"run `yuho check --json {sample}`",
        )
    return DoctorCheck("sample", "ok", f"{sample} validates")


def _optional_python_checks() -> list[DoctorCheck]:
    return [
        _python_module_check("z3", "Z3 verifier", "install `yuho[dev]`"),
        _python_module_check("watchdog", "watch mode", "install `yuho[watch]` or `yuho[dev]`"),
        _python_module_check("pygls", "LSP server", "install `yuho[lsp]` or `yuho[dev]`"),
    ]


def _python_module_check(module: str, name: str, hint: str) -> DoctorCheck:
    if importlib.util.find_spec(module):
        return DoctorCheck(name, "ok", f"Python module `{module}` available")
    return DoctorCheck(name, "warn", f"Python module `{module}` missing", hint)


def _external_tool_checks() -> list[DoctorCheck]:
    checks: list[DoctorCheck] = []
    compiler = _first_on_path([os.environ.get("CC"), "cc", "clang", "gcc"])
    if compiler:
        checks.append(DoctorCheck("C compiler", "ok", compiler))
    else:
        checks.append(
            DoctorCheck(
                "C compiler",
                "warn",
                "not found",
                "macOS: `xcode-select --install`; Linux: install gcc/clang",
            )
        )

    latex = _first_on_path(["latexmk", "pdflatex", "xelatex", "lualatex"])
    if latex:
        checks.append(DoctorCheck("PDF renderer", "ok", latex))
    else:
        checks.append(
            DoctorCheck(
                "PDF renderer",
                "warn",
                "LaTeX engine not found",
                "macOS: `brew install --cask mactex-no-gui`",
            )
        )

    mmdc = _first_on_path(["mmdc"])
    if mmdc:
        checks.append(DoctorCheck("Mermaid renderer", "ok", mmdc))
    elif shutil.which("npx"):
        checks.append(DoctorCheck("Mermaid renderer", "ok", "npx can run mmdc"))
    else:
        checks.append(
            DoctorCheck(
                "Mermaid renderer",
                "warn",
                "mmdc/npx not found",
                "install Node and `npm install -g @mermaid-js/mermaid-cli`",
            )
        )

    alloy_jar = os.environ.get("YUHO_ALLOY_JAR") or os.environ.get("ALLOY_JAR")
    if alloy_jar and Path(alloy_jar).exists():
        checks.append(DoctorCheck("Alloy", "ok", alloy_jar))
    elif shutil.which("java"):
        checks.append(
            DoctorCheck(
                "Alloy",
                "warn",
                "Java found, Alloy jar not configured",
                "pass `--alloy-jar PATH` to `yuho verify`",
            )
        )
    else:
        checks.append(
            DoctorCheck(
                "Alloy",
                "warn",
                "Java/Alloy jar not found",
                "Z3 still works with `yuho verify --engine z3`",
            )
        )
    return checks


def _first_on_path(candidates: list[Optional[str]]) -> Optional[str]:
    for candidate in candidates:
        if candidate:
            found = shutil.which(candidate)
            if found:
                return found
    return None


def _next_steps(counts: dict[str, int], strict: bool) -> list[str]:
    if counts["fail"]:
        return ["fix FAIL checks, then rerun `yuho doctor`"]
    if strict and counts["warn"]:
        return ["install optional WARN dependencies or rerun without `--strict`"]
    if counts["warn"]:
        return [
            "core CLI is ready; WARN checks are optional renderers/backends",
            "run `yuho init yuho-starter` for a local starter workspace",
        ]
    return ["run `yuho init yuho-starter` for a local starter workspace"]
