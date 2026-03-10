"""
PDF generation pipeline: LaTeX transpiler -> pdflatex/latexmk -> PDF.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from yuho.ast.nodes import ModuleNode
from yuho.transpile.registry import TranspilerRegistry
from yuho.transpile.base import TranspileTarget


class PDFGenerationError(Exception):
    """Raised when PDF generation fails."""


def generate_pdf(
    ast: ModuleNode,
    output_path: str,
    *,
    latex_engine: Optional[str] = None,
    keep_tex: bool = False,
) -> str:
    """
    Generate PDF from a Yuho AST via LaTeX transpilation.

    Tries latexmk first, falls back to pdflatex, then xelatex.

    Args:
        ast: parsed ModuleNode
        output_path: destination PDF file path
        latex_engine: override engine ("pdflatex", "xelatex", "latexmk")
        keep_tex: if True, keep the intermediate .tex file alongside the PDF

    Returns:
        absolute path to the generated PDF

    Raises:
        PDFGenerationError: if no LaTeX engine is found or compilation fails
    """
    registry = TranspilerRegistry.instance()
    latex_transpiler = registry.get(TranspileTarget.LATEX)
    tex_source = latex_transpiler.transpile(ast)
    engine = latex_engine or _find_latex_engine()
    if engine is None:
        raise PDFGenerationError(
            "No LaTeX engine found. Install one of:\n"
            "  brew install --cask mactex-no-gui\n"
            "  brew install basictex\n"
            "  apt-get install texlive-latex-base"
        )
    output = Path(output_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="yuho_pdf_") as tmpdir:
        tex_file = Path(tmpdir) / "statute.tex"
        tex_file.write_text(tex_source, encoding="utf-8")
        _compile_latex(engine, tex_file, tmpdir)
        pdf_file = tex_file.with_suffix(".pdf")
        if not pdf_file.exists():
            raise PDFGenerationError(
                f"LaTeX compilation succeeded but no PDF produced at {pdf_file}"
            )
        shutil.copy2(pdf_file, output)
        if keep_tex:
            tex_dest = output.with_suffix(".tex")
            shutil.copy2(tex_file, tex_dest)
    return str(output)


def _find_latex_engine() -> Optional[str]:
    """Find an available LaTeX engine."""
    for engine in ("latexmk", "pdflatex", "xelatex", "lualatex"):
        if shutil.which(engine):
            return engine
    return None


def _compile_latex(engine: str, tex_file: Path, work_dir: str) -> None:
    """Run the LaTeX engine to produce PDF."""
    if engine == "latexmk":
        cmd = [
            engine, "-pdf", "-interaction=nonstopmode",
            "-output-directory=" + work_dir,
            str(tex_file),
        ]
    else:
        cmd = [
            engine, "-interaction=nonstopmode",
            "-output-directory=" + work_dir,
            str(tex_file),
        ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
        cwd=work_dir,
    )
    if result.returncode != 0:
        log_file = tex_file.with_suffix(".log")
        log_tail = ""
        if log_file.exists():
            lines = log_file.read_text(errors="replace").splitlines()
            log_tail = "\n".join(lines[-30:])
        raise PDFGenerationError(
            f"LaTeX compilation failed (exit {result.returncode}).\n"
            f"Log tail:\n{log_tail}"
        )
