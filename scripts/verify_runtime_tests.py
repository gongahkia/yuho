"""Run `yuho test` across behavioural-test fixtures and diff them
against the Z3 assertion backend when z3-solver is importable.

Companion to `tests/test_library_statutes.py` (which only enforces
parse + lint validity, not runtime assertion truth). This script
closes the contract gap surfaced 2026-04-29: with the comment-strip
sweep applied, every rich test's `assert` lines are evaluable
end-to-end by the interpreter, and the runtime sweep becomes a
load-bearing CI claim.

Exit codes:
  0 - all rich tests pass and Z3 agrees when available
  1 - at least one fixture fails, errors, or disagrees with Z3
  2 - internal error (file-system / yuho CLI not importable)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
LIBRARY = REPO / "library" / "penal_code"
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@dataclass(frozen=True)
class Z3Failure:
    fixture: str
    assertion_index: int
    message: str


@dataclass(frozen=True)
class Z3Summary:
    checked: int
    assertions: int
    failures: tuple[Z3Failure, ...]
    errors: tuple[tuple[str, str], ...]


class UnsupportedZ3RuntimeExpr(Exception):
    pass


def _load_resolved_ast(test_file: Path):
    from yuho.ast import ASTBuilder
    from yuho.ast.nodes import ModuleNode
    from yuho.parser import get_parser

    parser = get_parser()
    parse_result = parser.parse_file(test_file)
    if parse_result.errors:
        errors = "; ".join(f"{e.location}: {e.message}" for e in parse_result.errors)
        raise RuntimeError(errors)

    ast = ASTBuilder(parse_result.source, str(test_file)).build(parse_result.root_node)
    if not ast.references:
        return ast

    from yuho.resolver import ModuleResolver

    resolver = ModuleResolver(search_paths=[test_file.parent, REPO, REPO / "library"])
    type_defs = list(ast.type_defs)
    function_defs = list(ast.function_defs)
    statutes = list(ast.statutes)
    variables = list(ast.variables)
    enum_defs = list(getattr(ast, "enum_defs", ()))
    type_aliases = list(getattr(ast, "type_aliases", ()))
    fact_events = list(getattr(ast, "fact_events", ()))

    for ref in ast.references:
        ref_module = resolver.resolve_reference(ref, test_file)
        type_defs.extend(ref_module.type_defs)
        function_defs.extend(ref_module.function_defs)
        statutes.extend(ref_module.statutes)
        variables.extend(ref_module.variables)
        enum_defs.extend(getattr(ref_module, "enum_defs", ()))
        type_aliases.extend(getattr(ref_module, "type_aliases", ()))
        fact_events.extend(getattr(ref_module, "fact_events", ()))

    return ModuleNode(
        imports=ast.imports,
        type_defs=tuple(type_defs),
        function_defs=tuple(function_defs),
        statutes=tuple(statutes),
        variables=tuple(variables),
        references=ast.references,
        assertions=ast.assertions,
        enum_defs=tuple(enum_defs),
        type_aliases=tuple(type_aliases),
        legal_tests=getattr(ast, "legal_tests", ()),
        conflict_checks=getattr(ast, "conflict_checks", ()),
        fact_events=tuple(fact_events),
        source_location=ast.source_location,
    )


def _runtime_interpreter(ast):
    from yuho.eval.interpreter import Interpreter, Value

    interp = Interpreter()
    for sd in ast.type_defs:
        interp.env.struct_defs[sd.name] = sd
    for ed in getattr(ast, "enum_defs", ()):
        interp.env.enum_defs[ed.name] = ed
        for variant in ed.variants:
            interp.env.set(variant.name, Value(variant.name, "enum"))
    for ta in getattr(ast, "type_aliases", ()):
        interp.env.type_aliases[ta.name] = ta
    for fd in ast.function_defs:
        interp.env.function_defs[fd.name] = fd
    for st in ast.statutes:
        interp.env.statutes[st.section_number] = st
    for var in ast.variables:
        interp.visit(var)
    return interp


def _value_to_z3(value):
    import z3

    if value.type_tag == "bool":
        return z3.BoolVal(bool(value.raw))
    if value.type_tag == "int":
        return z3.IntVal(int(value.raw))
    if value.type_tag == "float":
        return z3.RealVal(str(value.raw))
    if value.type_tag in ("money", "percent"):
        return z3.RealVal(str(Decimal(value.raw)))
    if value.type_tag in ("string", "enum"):
        return z3.StringVal(str(value.raw))
    if value.type_tag == "date":
        return z3.StringVal(value.raw.isoformat())
    if value.type_tag == "duration":
        return z3.IntVal(value.raw.total_days())
    if value.type_tag == "none":
        return z3.StringVal("none")
    raise UnsupportedZ3RuntimeExpr(f"unsupported value type: {value.type_tag}")


def _z3_expr_bool(expr: Any, interp):
    import z3

    term = _z3_expr(expr, interp)
    if z3.is_bool(term):
        return term
    return z3.BoolVal(interp.visit(expr).is_truthy())


def _z3_expr(expr, interp):
    import z3
    from yuho.ast import nodes

    if isinstance(
        expr,
        (
            nodes.IntLit,
            nodes.FloatLit,
            nodes.BoolLit,
            nodes.StringLit,
            nodes.MoneyNode,
            nodes.PercentNode,
            nodes.DateNode,
            nodes.DurationNode,
            nodes.PassExprNode,
        ),
    ):
        return _value_to_z3(interp.visit(expr))

    if isinstance(expr, (nodes.IdentifierNode, nodes.FieldAccessNode)):
        return _value_to_z3(interp.visit(expr))

    if isinstance(expr, nodes.UnaryExprNode):
        term = _z3_expr(expr.operand, interp)
        if expr.operator == "!":
            return z3.Not(_z3_expr_bool(expr.operand, interp))
        if expr.operator == "-":
            return -term

    if isinstance(expr, nodes.BinaryExprNode):
        op = expr.operator
        if op == "&&":
            return z3.And(_z3_expr_bool(expr.left, interp), _z3_expr_bool(expr.right, interp))
        if op == "||":
            return z3.Or(_z3_expr_bool(expr.left, interp), _z3_expr_bool(expr.right, interp))

        left = _z3_expr(expr.left, interp)
        right = _z3_expr(expr.right, interp)
        if op == "==":
            return left == right
        if op == "!=":
            return left != right
        if op == "<":
            return left < right
        if op == ">":
            return left > right
        if op == "<=":
            return left <= right
        if op == ">=":
            return left >= right
        if op == "+":
            return left + right
        if op == "-":
            return left - right
        if op == "*":
            return left * right
        if op == "/":
            return left / right

    return _value_to_z3(interp.visit(expr))


def _z3_assertion_truth(ast, assertion):
    import z3

    runtime = _runtime_interpreter(ast)
    runtime_truth = runtime.visit(assertion.condition).is_truthy()

    z3_interp = _runtime_interpreter(ast)
    z3_term = _z3_expr_bool(assertion.condition, z3_interp)
    solver = z3.Solver()
    solver.add(z3_term != z3.BoolVal(runtime_truth))
    verdict = solver.check()
    if verdict == z3.unsat:
        return runtime_truth
    if verdict == z3.sat:
        return not runtime_truth
    raise RuntimeError(f"Z3 returned {verdict}")


def run_z3_differential(rich: list[Path]) -> Z3Summary | None:
    from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE

    if not Z3_AVAILABLE:
        return None

    import z3

    failures: list[Z3Failure] = []
    errors: list[tuple[str, str]] = []
    assertions = 0
    for test_file in rich:
        try:
            ast = _load_resolved_ast(test_file)
            solver, _ = Z3Generator().generate(ast)
            if solver is not None:
                verdict = solver.check()
                if verdict != z3.sat:
                    errors.append((test_file.parent.name, f"Z3 constraints returned {verdict}"))
                    continue
            for idx, assertion in enumerate(ast.assertions, start=1):
                assertions += 1
                runtime_truth = _runtime_interpreter(ast).visit(assertion.condition).is_truthy()
                z3_truth = _z3_assertion_truth(ast, assertion)
                if runtime_truth != z3_truth:
                    failures.append(
                        Z3Failure(
                            fixture=test_file.parent.name,
                            assertion_index=idx,
                            message=f"runtime={runtime_truth} z3={z3_truth}",
                        )
                    )
        except Exception as e:
            errors.append((test_file.parent.name, str(e)[:160]))
    return Z3Summary(
        checked=len(rich),
        assertions=assertions,
        failures=tuple(failures),
        errors=tuple(errors),
    )


def main() -> int:
    if not LIBRARY.is_dir():
        print(f"library not found: {LIBRARY}", file=sys.stderr)
        return 2

    files = sorted(LIBRARY.glob("*/test_statute.yh"))
    rich = [p for p in files if "assert" in p.read_text(encoding="utf-8")]

    print(f"runtime-sweeping {len(rich)} rich test_statute.yh files...")

    passed = 0
    failed: list[tuple[str, str]] = []
    errored: list[tuple[str, str]] = []
    for p in rich:
        statute_path = p.parent / "statute.yh"
        result = subprocess.run(
            [sys.executable, "-m", "yuho.cli.main", "test", str(statute_path)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=REPO,
        )
        out = (result.stdout + result.stderr).strip()
        if result.returncode == 0 and ("PASS" in out or "All" in out):
            passed += 1
            continue
        last_line = out.splitlines()[-1] if out else "<no output>"
        if "Assertion failed" in out or "FAIL" in out:
            failed.append((p.parent.name, last_line[:160]))
        else:
            errored.append((p.parent.name, last_line[:160]))

    z3_summary = run_z3_differential(rich)

    print(f"runtime sweep: PASS={passed}/{len(rich)}  FAIL={len(failed)}  ERR={len(errored)}")
    if z3_summary is None:
        print("z3 differential: SKIP (z3-solver not installed)")
    else:
        print(
            "z3 differential: "
            f"CHECKED={z3_summary.checked} ASSERT={z3_summary.assertions} "
            f"DISAGREE={len(z3_summary.failures)} ERR={len(z3_summary.errors)}"
        )
    if failed:
        print("Assertion failures:", file=sys.stderr)
        for name, msg in failed:
            print(f"  {name}: {msg}", file=sys.stderr)
    if errored:
        print("Errors:", file=sys.stderr)
        for name, msg in errored:
            print(f"  {name}: {msg}", file=sys.stderr)
    if z3_summary is not None and z3_summary.failures:
        print("Z3 disagreements:", file=sys.stderr)
        for failure in z3_summary.failures:
            print(
                f"  {failure.fixture} assert#{failure.assertion_index}: {failure.message}",
                file=sys.stderr,
            )
    if z3_summary is not None and z3_summary.errors:
        print("Z3 errors:", file=sys.stderr)
        for name, msg in z3_summary.errors:
            print(f"  {name}: {msg}", file=sys.stderr)

    z3_failed = z3_summary is not None and (z3_summary.failures or z3_summary.errors)
    return 0 if not (failed or errored or z3_failed) else 1


if __name__ == "__main__":
    sys.exit(main())
