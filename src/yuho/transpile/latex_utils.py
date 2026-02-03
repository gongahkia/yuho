"""
LaTeX utility functions for transpilation.

Contains helper functions for:
- Escaping special LaTeX characters
- Converting AST nodes to LaTeX strings
- Duration and money formatting
"""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from yuho.ast import nodes


def escape_latex(text: str) -> str:
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


def operator_to_latex(op: str) -> str:
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


def duration_to_latex(node: "nodes.DurationNode") -> str:
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


def money_to_latex(node: "nodes.MoneyNode") -> str:
    """Convert money to LaTeX string."""
    from yuho.ast.nodes import Currency
    
    currency_symbols = {
        Currency.SGD: r"S\$",
        Currency.USD: r"US\$",
        Currency.EUR: r"\euro{}",
        Currency.GBP: r"\pounds{}",
        Currency.JPY: r"\textyen{}",
        Currency.CNY: r"\textyen{}",
        Currency.INR: r"\rupee{}",
        Currency.AUD: r"A\$",
        Currency.CAD: r"C\$",
        Currency.CHF: "CHF~",
    }
    symbol = currency_symbols.get(node.currency, r"\$")
    # Format with thousands separator
    amount_str = f"{node.amount:,.2f}"
    return f"{symbol}{amount_str}"


def type_to_latex(node: "nodes.TypeNode") -> str:
    """Convert type to LaTeX string."""
    from yuho.ast import nodes
    
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
        return rf"\texttt{{{escape_latex(node.name)}}}"
    elif isinstance(node, nodes.OptionalType):
        inner = type_to_latex(node.inner)
        return f"{inner}?"
    elif isinstance(node, nodes.ArrayType):
        elem = type_to_latex(node.element_type)
        return f"[{elem}]"
    return r"\texttt{unknown}"


def expr_to_latex(node: "nodes.ASTNode") -> str:
    """Convert expression to LaTeX string."""
    from yuho.ast import nodes
    
    if isinstance(node, nodes.IntLit):
        return str(node.value)
    elif isinstance(node, nodes.FloatLit):
        return str(node.value)
    elif isinstance(node, nodes.BoolLit):
        return r"\texttt{TRUE}" if node.value else r"\texttt{FALSE}"
    elif isinstance(node, nodes.StringLit):
        return f"``{escape_latex(node.value)}''"
    elif isinstance(node, nodes.MoneyNode):
        return money_to_latex(node)
    elif isinstance(node, nodes.PercentNode):
        return f"{node.value}\\%"
    elif isinstance(node, nodes.DateNode):
        return node.value.strftime("%d %B %Y")
    elif isinstance(node, nodes.DurationNode):
        return duration_to_latex(node)
    elif isinstance(node, nodes.IdentifierNode):
        return rf"\textit{{{escape_latex(node.name)}}}"
    elif isinstance(node, nodes.FieldAccessNode):
        base = expr_to_latex(node.base)
        field = escape_latex(node.field_name)
        return f"{base}.{field}"
    elif isinstance(node, nodes.BinaryExprNode):
        left = expr_to_latex(node.left)
        right = expr_to_latex(node.right)
        op = operator_to_latex(node.operator)
        return f"{left} {op} {right}"
    elif isinstance(node, nodes.UnaryExprNode):
        operand = expr_to_latex(node.operand)
        if node.operator == "!":
            return rf"\textit{{not}} {operand}"
        return f"{node.operator}{operand}"
    elif isinstance(node, nodes.PassExprNode):
        return r"\textit{(none)}"
    else:
        return str(node)


def pattern_to_latex(node: "nodes.PatternNode") -> str:
    """Convert pattern to LaTeX string."""
    from yuho.ast import nodes
    
    if isinstance(node, nodes.WildcardPattern):
        return r"\textit{otherwise}"
    elif isinstance(node, nodes.LiteralPattern):
        return f"the value is {expr_to_latex(node.literal)}"
    elif isinstance(node, nodes.BindingPattern):
        name = escape_latex(node.name)
        return rf"the value (call it ``{name}'')"
    elif isinstance(node, nodes.StructPattern):
        type_name = escape_latex(node.type_name)
        fields = ", ".join(escape_latex(fp.name) for fp in node.fields)
        return rf"it matches \texttt{{{type_name}}} with {{{fields}}}"
    return r"\textit{(condition met)}"


def statement_to_latex(node: "nodes.ASTNode") -> str:
    """Convert statement to LaTeX string."""
    from yuho.ast import nodes
    
    if isinstance(node, nodes.VariableDecl):
        type_str = type_to_latex(node.type_annotation)
        name = escape_latex(node.name)
        if node.value:
            value = expr_to_latex(node.value)
            return rf"Let \texttt{{{name}}} be {type_str} = {value}."
        return rf"Let \texttt{{{name}}} be {type_str}."
    elif isinstance(node, nodes.ReturnStmt):
        if node.value:
            value = expr_to_latex(node.value)
            return rf"Return {value}."
        return "Return."
    elif isinstance(node, nodes.AssignmentStmt):
        target = expr_to_latex(node.target)
        value = expr_to_latex(node.value)
        return rf"Set {target} $\leftarrow$ {value}."
    return str(node)
