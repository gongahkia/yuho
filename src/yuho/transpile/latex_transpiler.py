"""
LaTeX transpiler - legal document generation.

Converts Yuho AST to LaTeX documents with professional legal document
formatting including:
- Article class with proper legal document preamble
- Section formatting with statute numbers
- Margin notes and cross-references
- Penalty tables with imprisonment/fine columns
- Illustration blocks with gray background and italic text
"""

from typing import List, Optional
import subprocess
import os
import shutil

from yuho.ast import nodes
from yuho.ast.visitor import Visitor
from yuho.transpile.base import TranspileTarget, TranspilerBase
from yuho.transpile.latex_preamble import generate_preamble
from yuho.transpile.latex_utils import (
    escape_latex,
    operator_to_latex,
    duration_to_latex,
    money_to_latex,
    type_to_latex,
    expr_to_latex,
    pattern_to_latex,
    statement_to_latex,
)


class LaTeXTranspiler(TranspilerBase, Visitor):
    """
    Transpile Yuho AST to LaTeX documents.

    Generates professional legal documents with proper typographic
    conventions for statutes, penalties, and illustrations.
    """

    def __init__(
        self,
        document_title: str = "Legal Statutes",
        author: str = "",
        include_toc: bool = True,
        use_margins: bool = True,
    ):
        """
        Initialize LaTeX transpiler.

        Args:
            document_title: Title for the generated document
            author: Document author
            include_toc: Whether to include table of contents
            use_margins: Whether to use margin notes for annotations
        """
        self._output: List[str] = []
        self._indent_level = 0
        self.document_title = document_title
        self.author = author
        self.include_toc = include_toc
        self.use_margins = use_margins
        self._section_refs: dict = {}  # For cross-references

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.LATEX

    def transpile(self, ast: nodes.ModuleNode) -> str:
        """Transpile AST to LaTeX document."""
        self._output = []
        self._indent_level = 0
        self._section_refs = {}

        # Emit preamble from module
        preamble_lines = generate_preamble(
            document_title=self.document_title,
            author=self.author,
            use_margins=self.use_margins,
        )
        for line in preamble_lines:
            self._emit(line)

        # Begin document
        self._emit(r"\begin{document}")
        self._emit("")

        # Title
        self._emit(r"\maketitle")
        self._emit("")

        # Table of contents
        if self.include_toc:
            self._emit(r"\tableofcontents")
            self._emit(r"\newpage")
            self._emit("")

        # Visit module content
        self._visit_module(ast)

        # End document
        self._emit("")
        self._emit(r"\end{document}")

        return "\n".join(self._output)

    def _emit(self, text: str) -> None:
        """Add a line to output with current indentation."""
        indent = "  " * self._indent_level
        self._output.append(f"{indent}{text}")

    def _emit_blank(self) -> None:
        """Add a blank line."""
        self._output.append("")

    # =========================================================================
    # Module and imports
    # =========================================================================

    def _visit_module(self, node: nodes.ModuleNode) -> None:
        """Generate LaTeX for entire module."""
        # Imports (as references)
        if node.imports:
            self._emit(r"\section*{References}")
            self._emit(r"\begin{itemize}")
            for imp in node.imports:
                self._visit_import(imp)
            self._emit(r"\end{itemize}")
            self._emit_blank()

        # Type definitions
        if node.type_defs:
            self._emit(r"\section{Type Definitions}")
            for struct in node.type_defs:
                self._visit_struct_def(struct)
                self._emit_blank()

        # Functions
        if node.function_defs:
            self._emit(r"\section{Functions}")
            for func in node.function_defs:
                self._visit_function_def(func)
                self._emit_blank()

        # Statutes (main content)
        if node.statutes:
            self._emit(r"\section{Statutes}")
            for statute in node.statutes:
                self._visit_statute(statute)
                self._emit_blank()

    def _visit_import(self, node: nodes.ImportNode) -> None:
        """Generate LaTeX for import."""
        path = escape_latex(node.path)
        if node.is_wildcard:
            self._emit(rf"  \item All definitions from \texttt{{{path}}}")
        elif node.imported_names:
            names = ", ".join(rf"\texttt{{{escape_latex(n)}}}" for n in node.imported_names)
            self._emit(rf"  \item {names} from \texttt{{{path}}}")
        else:
            self._emit(rf"  \item \texttt{{{path}}}")

    # =========================================================================
    # Statute blocks
    # =========================================================================

    def _visit_statute(self, node: nodes.StatuteNode) -> None:
        """Generate LaTeX for statute."""
        section_num = escape_latex(node.section_number)
        title = escape_latex(node.title.value if node.title else "Untitled")

        # Store reference
        self._section_refs[node.section_number] = title

        # Statute header
        self._emit(rf"\statute{{{section_num}}}{{{title}}}")
        self._emit_blank()

        # Margin note with section number
        if self.use_margins:
            self._emit(rf"\marginnote{{S. {section_num}}}")

        # Definitions
        if node.definitions:
            self._emit(r"\paragraph{Definitions}")
            self._emit(r"\begin{legaldefs}")
            for defn in node.definitions:
                term = escape_latex(defn.term)
                definition = escape_latex(defn.definition.value)
                self._emit(rf"  \item[\textbf{{{term}}}] {definition}")
            self._emit(r"\end{legaldefs}")
            self._emit_blank()

        # Elements
        if node.elements:
            self._emit(r"\paragraph{Elements of the Offence}")
            self._emit(r"\begin{enumerate}")
            for elem in node.elements:
                self._visit_element(elem)
            self._emit(r"\end{enumerate}")
            self._emit_blank()

        # Penalty
        if node.penalty:
            self._emit(r"\paragraph{Penalty}")
            self._visit_penalty(node.penalty)
            self._emit_blank()

        # Illustrations
        if node.illustrations:
            self._emit(r"\paragraph{Illustrations}")
            self._emit_blank()
            for i, illus in enumerate(node.illustrations, 1):
                self._visit_illustration(illus, i)

    def _visit_element(self, node: nodes.ElementNode) -> None:
        """Generate LaTeX for element."""
        type_labels = {
            "actus_reus": "Actus Reus",
            "mens_rea": "Mens Rea",
            "circumstance": "Circumstance",
        }
        label = type_labels.get(node.element_type, node.element_type.replace("_", " ").title())

        # Margin annotation for element type
        if self.use_margins:
            margin = rf"\marginnote{{\scriptsize {label}}}"
        else:
            margin = ""

        # Handle description
        if isinstance(node.description, nodes.StringLit):
            desc = escape_latex(node.description.value)
            self._emit(rf"  \item{margin} \element{{{label}}}{{{desc}}}")
        elif isinstance(node.description, nodes.MatchExprNode):
            name = escape_latex(node.name)
            self._emit(rf"  \item{margin} \element{{{label}}}{{{name}:}}")
            self._emit(r"  \begin{itemize}")
            self._visit_match_expr_latex(node.description)
            self._emit(r"  \end{itemize}")
        else:
            desc = expr_to_latex(node.description)
            self._emit(rf"  \item{margin} \element{{{label}}}{{{desc}}}")

    def _visit_penalty(self, node: nodes.PenaltyNode) -> None:
        """Generate LaTeX penalty table."""
        self._emit(r"\begin{center}")
        self._emit(r"\begin{tabular}{@{}lll@{}}")
        self._emit(r"\toprule")
        self._emit(r"\textbf{Type} & \textbf{Minimum} & \textbf{Maximum} \\")
        self._emit(r"\midrule")

        # Imprisonment row
        if node.imprisonment_max:
            min_str = duration_to_latex(node.imprisonment_min) if node.imprisonment_min else "---"
            max_str = duration_to_latex(node.imprisonment_max)
            self._emit(rf"Imprisonment & {min_str} & {max_str} \\")

        # Fine row
        if node.fine_max:
            min_str = money_to_latex(node.fine_min) if node.fine_min else "---"
            max_str = money_to_latex(node.fine_max)
            self._emit(rf"Fine & {min_str} & {max_str} \\")

        self._emit(r"\bottomrule")
        self._emit(r"\end{tabular}")
        self._emit(r"\end{center}")

        # Supplementary information
        if node.supplementary:
            self._emit_blank()
            supp = escape_latex(node.supplementary.value)
            self._emit(rf"\textit{{Additional: {supp}}}")

    def _visit_illustration(self, node: nodes.IllustrationNode, index: int) -> None:
        """Generate LaTeX for illustration with gray background and italic text."""
        label = node.label or f"({chr(ord('a') + index - 1)})"
        desc = escape_latex(node.description.value)

        self._emit(r"\begin{illustrationbox}")
        self._emit(rf"\textbf{{{label}}} {desc}")
        self._emit(r"\end{illustrationbox}")
        self._emit_blank()

    # =========================================================================
    # Match expressions
    # =========================================================================

    def _visit_match_expr_latex(self, node: nodes.MatchExprNode) -> None:
        """Generate LaTeX for match expression."""
        if node.scrutinee:
            scrutinee = expr_to_latex(node.scrutinee)
            self._emit(rf"    \item[] \textit{{Based on {scrutinee}:}}")

        for i, arm in enumerate(node.arms):
            self._visit_match_arm_latex(arm, i, len(node.arms))

    def _visit_match_arm_latex(self, node: nodes.MatchArm, index: int, total: int) -> None:
        """Generate LaTeX for match arm."""
        pattern = pattern_to_latex(node.pattern)
        body = expr_to_latex(node.body)

        # Guard
        guard_str = ""
        if node.guard:
            guard = expr_to_latex(node.guard)
            guard_str = f", provided that {guard}"

        # Connector
        if isinstance(node.pattern, nodes.WildcardPattern):
            self._emit(rf"    \item \textit{{Otherwise{guard_str}:}} {body}")
        else:
            self._emit(rf"    \item If {pattern}{guard_str}: {body}")

    # =========================================================================
    # Struct definitions
    # =========================================================================

    def _visit_struct_def(self, node: nodes.StructDefNode) -> None:
        """Generate LaTeX for struct definition."""
        name = escape_latex(node.name)
        self._emit(rf"\paragraph{{{name}}}")
        self._emit(r"\begin{description}")
        for field in node.fields:
            field_name = escape_latex(field.name)
            type_str = type_to_latex(field.type_annotation)
            self._emit(rf"  \item[\texttt{{{field_name}}}] {type_str}")
        self._emit(r"\end{description}")

    # =========================================================================
    # Function definitions
    # =========================================================================

    def _visit_function_def(self, node: nodes.FunctionDefNode) -> None:
        """Generate LaTeX for function definition."""
        name = escape_latex(node.name)
        params = ", ".join(
            rf"\texttt{{{escape_latex(p.name)}}}: {type_to_latex(p.type_annotation)}"
            for p in node.params
        )
        ret = f" $\\rightarrow$ {type_to_latex(node.return_type)}" if node.return_type else ""

        self._emit(rf"\paragraph{{\texttt{{{name}}}({params}){ret}}}")
        self._emit(r"\begin{quote}")
        for stmt in node.body.statements:
            stmt_latex = statement_to_latex(stmt)
            self._emit(stmt_latex)
        self._emit(r"\end{quote}")


def compile_to_pdf(
    latex_file: str,
    output_dir: Optional[str] = None,
    compiler: str = "pdflatex",
) -> Optional[str]:
    """
    Compile LaTeX file to PDF using pdflatex or xelatex.

    Args:
        latex_file: Path to the .tex file
        output_dir: Output directory (defaults to same as input)
        compiler: LaTeX compiler to use ('pdflatex' or 'xelatex')

    Returns:
        Path to generated PDF, or None if compilation failed
    """
    if not os.path.exists(latex_file):
        raise FileNotFoundError(f"LaTeX file not found: {latex_file}")

    # Find compiler
    compiler_path = shutil.which(compiler)
    if not compiler_path:
        raise RuntimeError(f"Compiler not found: {compiler}")

    # Prepare output directory
    if output_dir is None:
        output_dir = os.path.dirname(latex_file) or "."

    # Run compiler (twice for cross-references)
    cmd = [
        compiler_path,
        "-interaction=nonstopmode",
        f"-output-directory={output_dir}",
        latex_file,
    ]

    try:
        # First pass
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)
        # Second pass for cross-references
        subprocess.run(cmd, check=True, capture_output=True, timeout=60)

        # Determine output path
        base_name = os.path.splitext(os.path.basename(latex_file))[0]
        pdf_path = os.path.join(output_dir, f"{base_name}.pdf")

        if os.path.exists(pdf_path):
            return pdf_path
        return None

    except subprocess.CalledProcessError as e:
        # Log error but don't crash
        return None
    except subprocess.TimeoutExpired:
        return None
