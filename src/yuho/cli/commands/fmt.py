"""
Format command - canonical formatting for Yuho files.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from yuho.parser import get_parser
from yuho.ast import ASTBuilder
from yuho.cli.error_formatter import Colors, colorize


def run_fmt(file: str, in_place: bool = False, check: bool = False, verbose: bool = False) -> None:
    """
    Format a Yuho source file.

    Args:
        file: Path to the .yh file
        in_place: Format file in place
        check: Check if formatted (exit 1 if not)
        verbose: Enable verbose output
    """
    file_path = Path(file)

    # Parse file
    parser = get_parser()
    try:
        result = parser.parse_file(file_path)
    except FileNotFoundError:
        click.echo(colorize(f"error: File not found: {file}", Colors.RED), err=True)
        sys.exit(1)

    if result.errors:
        click.echo(colorize(f"error: Cannot format file with parse errors", Colors.RED), err=True)
        sys.exit(1)

    # Build AST
    builder = ASTBuilder(result.source, str(file_path))
    ast = builder.build(result.root_node)

    # Format using canonical printer
    formatted = _format_module(ast)

    # Compare with original
    original = result.source
    is_formatted = original.strip() == formatted.strip()

    if check:
        if is_formatted:
            if verbose:
                click.echo(f"OK: {file_path} is formatted")
            sys.exit(0)
        else:
            click.echo(colorize(f"FAIL: {file_path} needs formatting", Colors.RED))
            sys.exit(1)

    if in_place:
        if is_formatted:
            if verbose:
                click.echo(f"No changes: {file_path}")
        else:
            file_path.write_text(formatted, encoding="utf-8")
            click.echo(f"Formatted: {file_path}")
    else:
        print(formatted)


def _format_module(ast) -> str:
    """Format a module AST to canonical string representation."""
    from yuho.ast import nodes

    lines = []

    # Imports
    for imp in ast.imports:
        if imp.is_wildcard:
            lines.append(f'import * from "{imp.path}"')
        elif imp.imported_names:
            names = ", ".join(imp.imported_names)
            lines.append(f'import {{ {names} }} from "{imp.path}"')
        else:
            lines.append(f'import "{imp.path}"')

    if ast.imports:
        lines.append("")

    # Struct definitions
    for struct in ast.type_defs:
        lines.append(f"struct {struct.name} {{")
        for field in struct.fields:
            type_str = _format_type(field.type_annotation)
            lines.append(f"    {type_str} {field.name},")
        lines.append("}")
        lines.append("")

    # Function definitions
    for func in ast.function_defs:
        params = ", ".join(
            f"{_format_type(p.type_annotation)} {p.name}"
            for p in func.params
        )
        ret = f": {_format_type(func.return_type)}" if func.return_type else ""
        lines.append(f"fn {func.name}({params}){ret} {{")
        for stmt in func.body.statements:
            lines.append(f"    {_format_statement(stmt)}")
        lines.append("}")
        lines.append("")

    # Statutes
    for statute in ast.statutes:
        title = f' "{statute.title.value}"' if statute.title else ""
        lines.append(f"statute {statute.section_number}{title} {{")

        if statute.definitions:
            lines.append("    definitions {")
            for defn in statute.definitions:
                lines.append(f'        {defn.term} := "{defn.definition.value}";')
            lines.append("    }")
            lines.append("")

        if statute.elements:
            lines.append("    elements {")
            for elem in statute.elements:
                desc = _format_expr(elem.description)
                lines.append(f"        {elem.element_type} {elem.name} := {desc};")
            lines.append("    }")
            lines.append("")

        if statute.penalty:
            lines.append("    penalty {")
            if statute.penalty.imprisonment_max:
                dur = _format_duration(statute.penalty.imprisonment_max)
                if statute.penalty.imprisonment_min:
                    min_dur = _format_duration(statute.penalty.imprisonment_min)
                    lines.append(f"        imprisonment := {min_dur} .. {dur};")
                else:
                    lines.append(f"        imprisonment := {dur};")
            if statute.penalty.fine_max:
                money = _format_money(statute.penalty.fine_max)
                if statute.penalty.fine_min:
                    min_money = _format_money(statute.penalty.fine_min)
                    lines.append(f"        fine := {min_money} .. {money};")
                else:
                    lines.append(f"        fine := {money};")
            if statute.penalty.supplementary:
                lines.append(f'        supplementary := "{statute.penalty.supplementary.value}";')
            lines.append("    }")
            lines.append("")

        for illus in statute.illustrations:
            label = illus.label or ""
            lines.append(f'    illustration {label} {{')
            lines.append(f'        "{illus.description.value}"')
            lines.append("    }")
            lines.append("")

        lines.append("}")
        lines.append("")

    # Variables
    for var in ast.variables:
        type_str = _format_type(var.type_annotation)
        if var.value:
            val = _format_expr(var.value)
            lines.append(f"{type_str} {var.name} := {val};")
        else:
            lines.append(f"{type_str} {var.name};")

    return "\n".join(lines)


def _format_type(typ) -> str:
    """Format a type node."""
    from yuho.ast import nodes

    if isinstance(typ, nodes.BuiltinType):
        return typ.name
    elif isinstance(typ, nodes.NamedType):
        return typ.name
    elif isinstance(typ, nodes.OptionalType):
        return f"{_format_type(typ.inner)}?"
    elif isinstance(typ, nodes.ArrayType):
        return f"[{_format_type(typ.element_type)}]"
    elif isinstance(typ, nodes.GenericType):
        args = ", ".join(_format_type(a) for a in typ.type_args)
        return f"{typ.base}<{args}>"
    return "?"


def _format_expr(expr) -> str:
    """Format an expression node."""
    from yuho.ast import nodes

    if isinstance(expr, nodes.IntLit):
        return str(expr.value)
    elif isinstance(expr, nodes.FloatLit):
        return str(expr.value)
    elif isinstance(expr, nodes.BoolLit):
        return "TRUE" if expr.value else "FALSE"
    elif isinstance(expr, nodes.StringLit):
        return f'"{expr.value}"'
    elif isinstance(expr, nodes.MoneyNode):
        return _format_money(expr)
    elif isinstance(expr, nodes.PercentNode):
        return f"{expr.value}%"
    elif isinstance(expr, nodes.DateNode):
        return expr.value.isoformat()
    elif isinstance(expr, nodes.DurationNode):
        return _format_duration(expr)
    elif isinstance(expr, nodes.IdentifierNode):
        return expr.name
    elif isinstance(expr, nodes.FieldAccessNode):
        return f"{_format_expr(expr.base)}.{expr.field_name}"
    elif isinstance(expr, nodes.BinaryExprNode):
        return f"{_format_expr(expr.left)} {expr.operator} {_format_expr(expr.right)}"
    elif isinstance(expr, nodes.PassExprNode):
        return "pass"
    return "?"


def _format_statement(stmt) -> str:
    """Format a statement."""
    from yuho.ast import nodes

    if isinstance(stmt, nodes.ReturnStmt):
        if stmt.value:
            return f"return {_format_expr(stmt.value)};"
        return "return;"
    elif isinstance(stmt, nodes.PassStmt):
        return "pass;"
    elif isinstance(stmt, nodes.ExpressionStmt):
        return f"{_format_expr(stmt.expression)};"
    return "?"


def _format_duration(dur) -> str:
    """Format a duration."""
    parts = []
    if dur.years:
        parts.append(f"{dur.years} year{'s' if dur.years != 1 else ''}")
    if dur.months:
        parts.append(f"{dur.months} month{'s' if dur.months != 1 else ''}")
    if dur.days:
        parts.append(f"{dur.days} day{'s' if dur.days != 1 else ''}")
    return ", ".join(parts) if parts else "0 days"


def _format_money(money) -> str:
    """Format a money value."""
    return f"${money.amount}"
