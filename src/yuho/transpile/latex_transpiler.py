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

        # Emit preamble
        self._emit_preamble()

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
    # LaTeX Preamble
    # =========================================================================

    def _emit_preamble(self) -> None:
        """Emit LaTeX preamble for legal documents."""
        # Document class
        self._emit(r"\documentclass[11pt,a4paper]{article}")
        self._emit("")

        # Essential packages
        self._emit(r"% Essential packages")
        self._emit(r"\usepackage[utf8]{inputenc}")
        self._emit(r"\usepackage[T1]{fontenc}")
        self._emit(r"\usepackage{lmodern}")
        self._emit("")

        # Page geometry
        self._emit(r"% Page layout")
        if self.use_margins:
            self._emit(r"\usepackage[a4paper,left=3cm,right=4cm,top=2.5cm,bottom=2.5cm,marginparwidth=3cm]{geometry}")
        else:
            self._emit(r"\usepackage[a4paper,margin=2.5cm]{geometry}")
        self._emit("")

        # Typography
        self._emit(r"% Typography")
        self._emit(r"\usepackage{microtype}")
        self._emit(r"\usepackage{parskip}")
        self._emit(r"\setlength{\parindent}{0pt}")
        self._emit("")

        # Colors and boxes
        self._emit(r"% Colors and boxes for illustrations")
        self._emit(r"\usepackage{xcolor}")
        self._emit(r"\usepackage{tcolorbox}")
        self._emit(r"\tcbuselibrary{skins}")
        self._emit("")

        # Define illustration box style
        self._emit(r"% Illustration box style")
        self._emit(r"\newtcolorbox{illustrationbox}[1][]{")
        self._emit(r"  enhanced,")
        self._emit(r"  colback=gray!10,")
        self._emit(r"  colframe=gray!50,")
        self._emit(r"  fontupper=\itshape,")
        self._emit(r"  boxrule=0.5pt,")
        self._emit(r"  left=10pt,")
        self._emit(r"  right=10pt,")
        self._emit(r"  top=8pt,")
        self._emit(r"  bottom=8pt,")
        self._emit(r"  #1")
        self._emit(r"}")
        self._emit("")

        # Tables
        self._emit(r"% Tables for penalties")
        self._emit(r"\usepackage{booktabs}")
        self._emit(r"\usepackage{array}")
        self._emit(r"\usepackage{longtable}")
        self._emit("")

        # Margin notes
        if self.use_margins:
            self._emit(r"% Margin notes")
            self._emit(r"\usepackage{marginnote}")
            self._emit(r"\renewcommand*{\marginfont}{\footnotesize\sffamily}")
            self._emit("")

        # Hyperlinks and cross-references
        self._emit(r"% Hyperlinks")
        self._emit(r"\usepackage{hyperref}")
        self._emit(r"\hypersetup{")
        self._emit(r"  colorlinks=true,")
        self._emit(r"  linkcolor=blue!60!black,")
        self._emit(r"  urlcolor=blue!60!black,")
        self._emit(r"  pdftitle={" + self._escape_latex(self.document_title) + "},")
        if self.author:
            self._emit(r"  pdfauthor={" + self._escape_latex(self.author) + "},")
        self._emit(r"}")
        self._emit("")

        # Section formatting for statutes
        self._emit(r"% Statute section formatting")
        self._emit(r"\usepackage{titlesec}")
        self._emit(r"\titleformat{\section}")
        self._emit(r"  {\normalfont\Large\bfseries}")
        self._emit(r"  {Section \thesection}")
        self._emit(r"  {1em}")
        self._emit(r"  {}")
        self._emit("")

        # Custom commands for legal formatting
        self._emit(r"% Custom commands for legal formatting")
        self._emit(r"\newcommand{\statute}[2]{%")
        self._emit(r"  \subsection[Section #1 --- #2]{Section #1 --- #2}%")
        self._emit(r"  \label{sec:#1}%")
        self._emit(r"}")
        self._emit("")

        self._emit(r"\newcommand{\sectionref}[1]{Section~\ref{sec:#1}}")
        self._emit("")

        self._emit(r"\newcommand{\element}[2]{%")
        self._emit(r"  \textbf{#1:} #2%")
        self._emit(r"}")
        self._emit("")

        # Definition list environment
        self._emit(r"% Definition list for legal definitions")
        self._emit(r"\newenvironment{legaldefs}{%")
        self._emit(r"  \begin{description}[leftmargin=2em,style=nextline]")
        self._emit(r"}{%")
        self._emit(r"  \end{description}")
        self._emit(r"}")
        self._emit(r"\usepackage{enumitem}")
        self._emit("")

        # Document metadata
        self._emit(r"% Document metadata")
        self._emit(r"\title{" + self._escape_latex(self.document_title) + "}")
        if self.author:
            self._emit(r"\author{" + self._escape_latex(self.author) + "}")
        else:
            self._emit(r"\author{}")
        self._emit(r"\date{\today}")
        self._emit("")

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
        path = self._escape_latex(node.path)
        if node.is_wildcard:
            self._emit(rf"  \item All definitions from \texttt{{{path}}}")
        elif node.imported_names:
            names = ", ".join(rf"\texttt{{{self._escape_latex(n)}}}" for n in node.imported_names)
            self._emit(rf"  \item {names} from \texttt{{{path}}}")
        else:
            self._emit(rf"  \item \texttt{{{path}}}")

    # =========================================================================
    # Statute blocks
    # =========================================================================

    def _visit_statute(self, node: nodes.StatuteNode) -> None:
        """Generate LaTeX for statute."""
        section_num = self._escape_latex(node.section_number)
        title = self._escape_latex(node.title.value if node.title else "Untitled")

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
                term = self._escape_latex(defn.term)
                definition = self._escape_latex(defn.definition.value)
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
            desc = self._escape_latex(node.description.value)
            self._emit(rf"  \item{margin} \element{{{label}}}{{{desc}}}")
        elif isinstance(node.description, nodes.MatchExprNode):
            name = self._escape_latex(node.name)
            self._emit(rf"  \item{margin} \element{{{label}}}{{{name}:}}")
            self._emit(r"  \begin{itemize}")
            self._visit_match_expr_latex(node.description)
            self._emit(r"  \end{itemize}")
        else:
            desc = self._expr_to_latex(node.description)
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
            min_str = self._duration_to_latex(node.imprisonment_min) if node.imprisonment_min else "---"
            max_str = self._duration_to_latex(node.imprisonment_max)
            self._emit(rf"Imprisonment & {min_str} & {max_str} \\")

        # Fine row
        if node.fine_max:
            min_str = self._money_to_latex(node.fine_min) if node.fine_min else "---"
            max_str = self._money_to_latex(node.fine_max)
            self._emit(rf"Fine & {min_str} & {max_str} \\")

        self._emit(r"\bottomrule")
        self._emit(r"\end{tabular}")
        self._emit(r"\end{center}")

        # Supplementary information
        if node.supplementary:
            self._emit_blank()
            supp = self._escape_latex(node.supplementary.value)
            self._emit(rf"\textit{{Additional: {supp}}}")

    def _visit_illustration(self, node: nodes.IllustrationNode, index: int) -> None:
        """Generate LaTeX for illustration with gray background and italic text."""
        label = node.label or f"({chr(ord('a') + index - 1)})"
        desc = self._escape_latex(node.description.value)

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
            scrutinee = self._expr_to_latex(node.scrutinee)
            self._emit(rf"    \item[] \textit{{Based on {scrutinee}:}}")

        for i, arm in enumerate(node.arms):
            self._visit_match_arm_latex(arm, i, len(node.arms))

    def _visit_match_arm_latex(self, node: nodes.MatchArm, index: int, total: int) -> None:
        """Generate LaTeX for match arm."""
        pattern = self._pattern_to_latex(node.pattern)
        body = self._expr_to_latex(node.body)

        # Guard
        guard_str = ""
        if node.guard:
            guard = self._expr_to_latex(node.guard)
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
        name = self._escape_latex(node.name)
        self._emit(rf"\paragraph{{{name}}}")
        self._emit(r"\begin{description}")
        for field in node.fields:
            field_name = self._escape_latex(field.name)
            type_str = self._type_to_latex(field.type_annotation)
            self._emit(rf"  \item[\texttt{{{field_name}}}] {type_str}")
        self._emit(r"\end{description}")

    # =========================================================================
    # Function definitions
    # =========================================================================

    def _visit_function_def(self, node: nodes.FunctionDefNode) -> None:
        """Generate LaTeX for function definition."""
        name = self._escape_latex(node.name)
        params = ", ".join(
            rf"\texttt{{{self._escape_latex(p.name)}}}: {self._type_to_latex(p.type_annotation)}"
            for p in node.params
        )
        ret = f" $\\rightarrow$ {self._type_to_latex(node.return_type)}" if node.return_type else ""

        self._emit(rf"\paragraph{{\texttt{{{name}}}({params}){ret}}}")
        self._emit(r"\begin{quote}")
        for stmt in node.body.statements:
            stmt_latex = self._statement_to_latex(stmt)
            self._emit(stmt_latex)
        self._emit(r"\end{quote}")

    # =========================================================================
    # Helper methods
    # =========================================================================

    def _escape_latex(self, text: str) -> str:
        """Escape special LaTeX characters."""
        replacements = [
            ("\\", r"\textbackslash{}"),
            ("{", r"\{"),
            ("}", r"\}"),
            ("$", r"\$"),
            ("%", r"\%"),
            ("&", r"\&"),
            ("#", r"\#"),
            ("_", r"\_"),
            ("^", r"\textasciicircum{}"),
            ("~", r"\textasciitilde{}"),
        ]
        for old, new in replacements:
            text = text.replace(old, new)
        return text

    def _expr_to_latex(self, node: nodes.ASTNode) -> str:
        """Convert expression to LaTeX string."""
        if isinstance(node, nodes.IntLit):
            return str(node.value)
        elif isinstance(node, nodes.FloatLit):
            return str(node.value)
        elif isinstance(node, nodes.BoolLit):
            return r"\texttt{TRUE}" if node.value else r"\texttt{FALSE}"
        elif isinstance(node, nodes.StringLit):
            return f"``{self._escape_latex(node.value)}''"
        elif isinstance(node, nodes.MoneyNode):
            return self._money_to_latex(node)
        elif isinstance(node, nodes.PercentNode):
            return f"{node.value}\\%"
        elif isinstance(node, nodes.DateNode):
            return node.value.strftime("%d %B %Y")
        elif isinstance(node, nodes.DurationNode):
            return self._duration_to_latex(node)
        elif isinstance(node, nodes.IdentifierNode):
            return rf"\textit{{{self._escape_latex(node.name)}}}"
        elif isinstance(node, nodes.FieldAccessNode):
            base = self._expr_to_latex(node.base)
            field = self._escape_latex(node.field_name)
            return f"{base}.{field}"
        elif isinstance(node, nodes.BinaryExprNode):
            left = self._expr_to_latex(node.left)
            right = self._expr_to_latex(node.right)
            op = self._operator_to_latex(node.operator)
            return f"{left} {op} {right}"
        elif isinstance(node, nodes.UnaryExprNode):
            operand = self._expr_to_latex(node.operand)
            if node.operator == "!":
                return rf"\textit{{not}} {operand}"
            return f"{node.operator}{operand}"
        elif isinstance(node, nodes.PassExprNode):
            return r"\textit{(none)}"
        else:
            return str(node)

    def _pattern_to_latex(self, node: nodes.PatternNode) -> str:
        """Convert pattern to LaTeX string."""
        if isinstance(node, nodes.WildcardPattern):
            return r"\textit{otherwise}"
        elif isinstance(node, nodes.LiteralPattern):
            return f"the value is {self._expr_to_latex(node.literal)}"
        elif isinstance(node, nodes.BindingPattern):
            name = self._escape_latex(node.name)
            return rf"the value (call it ``{name}'')"
        elif isinstance(node, nodes.StructPattern):
            type_name = self._escape_latex(node.type_name)
            fields = ", ".join(self._escape_latex(fp.name) for fp in node.fields)
            return rf"it matches \texttt{{{type_name}}} with {{{fields}}}"
        return r"\textit{(condition met)}"

    def _type_to_latex(self, node: nodes.TypeNode) -> str:
        """Convert type to LaTeX string."""
        if isinstance(node, nodes.BuiltinType):
            type_names = {
                "int": "integer",
                "float": "decimal",
                "bool": "boolean",
                "string": "text",
                "money": "monetary amount",
                "percent": "percentage",
                "date": "date",
                "duration": "duration",
                "void": "void",
            }
            return rf"\texttt{{{type_names.get(node.name, node.name)}}}"
        elif isinstance(node, nodes.NamedType):
            return rf"\texttt{{{self._escape_latex(node.name)}}}"
        elif isinstance(node, nodes.OptionalType):
            inner = self._type_to_latex(node.inner)
            return f"{inner}?"
        elif isinstance(node, nodes.ArrayType):
            elem = self._type_to_latex(node.element_type)
            return f"[{elem}]"
        return r"\texttt{unknown}"

    def _operator_to_latex(self, op: str) -> str:
        """Convert operator to LaTeX symbol."""
        operators = {
            "+": "+",
            "-": "--",
            "*": r"$\times$",
            "/": r"$\div$",
            "%": r"\%",
            "==": "=",
            "!=": r"$\neq$",
            "<": r"$<$",
            ">": r"$>$",
            "<=": r"$\leq$",
            ">=": r"$\geq$",
            "&&": r"\textbf{and}",
            "||": r"\textbf{or}",
        }
        return operators.get(op, op)

    def _duration_to_latex(self, node: nodes.DurationNode) -> str:
        """Convert duration to LaTeX string."""
        parts: List[str] = []
        if node.years:
            parts.append(f"{node.years} year{'s' if node.years != 1 else ''}")
        if node.months:
            parts.append(f"{node.months} month{'s' if node.months != 1 else ''}")
        if node.days:
            parts.append(f"{node.days} day{'s' if node.days != 1 else ''}")
        if node.hours:
            parts.append(f"{node.hours} hour{'s' if node.hours != 1 else ''}")
        if node.minutes:
            parts.append(f"{node.minutes} minute{'s' if node.minutes != 1 else ''}")
        if node.seconds:
            parts.append(f"{node.seconds} second{'s' if node.seconds != 1 else ''}")

        if not parts:
            return "---"
        return ", ".join(parts)

    def _money_to_latex(self, node: nodes.MoneyNode) -> str:
        """Convert money to LaTeX string."""
        currency_symbols = {
            nodes.Currency.SGD: r"S\$",
            nodes.Currency.USD: r"US\$",
            nodes.Currency.EUR: r"\euro{}",
            nodes.Currency.GBP: r"\pounds{}",
            nodes.Currency.JPY: r"\textyen{}",
            nodes.Currency.CNY: r"\textyen{}",
            nodes.Currency.INR: r"\rupee{}",
            nodes.Currency.AUD: r"A\$",
            nodes.Currency.CAD: r"C\$",
            nodes.Currency.CHF: "CHF~",
        }
        symbol = currency_symbols.get(node.currency, r"\$")
        # Format with thousands separator
        amount_str = f"{node.amount:,.2f}"
        return f"{symbol}{amount_str}"

    def _statement_to_latex(self, node: nodes.ASTNode) -> str:
        """Convert statement to LaTeX string."""
        if isinstance(node, nodes.VariableDecl):
            type_str = self._type_to_latex(node.type_annotation)
            name = self._escape_latex(node.name)
            if node.value:
                value = self._expr_to_latex(node.value)
                return rf"Let \texttt{{{name}}} be {type_str} = {value}."
            return rf"Let \texttt{{{name}}} be {type_str}."
        elif isinstance(node, nodes.ReturnStmt):
            if node.value:
                value = self._expr_to_latex(node.value)
                return rf"Return {value}."
            return "Return."
        elif isinstance(node, nodes.AssignmentStmt):
            target = self._expr_to_latex(node.target)
            value = self._expr_to_latex(node.value)
            return rf"Set {target} $\leftarrow$ {value}."
        return str(node)


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
