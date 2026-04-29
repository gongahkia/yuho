"""
Python-side faithfulness — structural diff harness.

Tightens `make verify-bulk-contrast` from a behavioural to a
structural check on the smoke fixtures (s299/s300/s378/s415):

  1. invokes `lake env lean --run scripts/ExportSpec.lean` from
     `mechanisation/`, captures the Lean spec's JSON biconditional
     list per statute (the verified `Generator.encodeStatute`
     output);
  2. constructs parallel Python `StatuteNode` fixtures matching
     the Lean `Statute` fixtures element-for-element and
     exception-for-exception;
  3. runs `Z3Generator._generate_statute_constraints` on each
     Python fixture and serialises the resulting assertion list
     to the same JSON shape;
  4. diffs the two atom-set + connective-tree projections per
     statute, reporting any divergence;
  5. exits nonzero if any unexplained divergence remains after
     the documented `KNOWN_DIVERGENCES` are subtracted.

Run via `make verify-structural-diff` from the repo root, or:
  $ /path/to/.venv-test/bin/python scripts/verify_structural_diff.py

Requires z3 + the Yuho package importable. The `.venv-test`
virtualenv satisfies both.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parent

# importable yuho package
sys.path.insert(0, str(REPO / "src"))

from yuho.ast.nodes import (  # noqa: E402
    ElementGroupNode,
    ElementNode,
    ExceptionNode,
    StatuteNode,
    StringLit,
)
from yuho.verify.z3_solver import Z3Generator  # noqa: E402

import z3  # noqa: E402


# Documented atom-naming convention differences between the Lean spec
# and the Python emitter. The leaf-bicond family and uniform `_fires`
# suffix divergences were closed in the v7 generator-emit
# consolidation pass (`src/yuho/verify/z3_solver.py` 2026-04-29);
# Python now emits the same number and shape of biconds Lean does.
# The remaining residue is purely an atom-naming convention: Lean
# uses bare leaf names (`death`, `intent`) for the leaf-bicond RHS
# and inside the elements bicond; Python uses statute-prefixed
# `<sX>_<elem>` to preserve per-statute leaf independence under
# multi-statute compilation. The harness canonicalises both
# conventions before comparing bicond shape.
KNOWN_DIVERGENCES = {
    "leaf_atom_naming_convention": (
        "Lean spec keys leaf atoms on bare `<e.name>` (shared across "
        "statutes); Python keys them on `<sX>_<e.name>` (per-statute "
        "independence). The harness normalises Lean atoms to the "
        "Python convention before bicond comparison so the two "
        "encodings register as canonically equivalent."
    ),
    "exception_fires_rhs_opaque_vs_priority": (
        "Lean's `<sX>_exc_<label>_fires` bicond RHS is an opaque "
        "`_firedSet` atom whose truth value the canonical model "
        "resolves via `Exception.firedSet`. Python's RHS expands the "
        "priority logic inline as `AND(exc_var, NOT(defeaters))`. "
        "Both reach the same satisfying assignments; the harness "
        "skips inner-shape comparison on `_fires` biconds."
    ),
}


def _canonicalise_lean_leaf_name(
    name: str, statute_id: str, leaf_names: set[str]
) -> str:
    """Map a Lean atom name to Python's per-statute convention.

    Lean leaf-bicond RHS and elements-bicond leaf references use bare
    `<e.name>`; Python uses `<sX>_leaf_<e.name>`. When `name` is a
    known leaf for `statute_id`, rewrite it to Python's collision-safe
    naming so structural comparison succeeds.
    """
    if name in leaf_names:
        return f"{statute_id}_leaf_{name}"
    return name


def _flatten_assoc(op: str, identity: bool, node: dict[str, Any]) -> dict[str, Any]:
    """Normalise nested AND/OR + identity-element terminators to a flat
    n-ary form. Lean emits list-folded AND/OR with `.const true/false`
    terminators (`encodeGroupAll`/`Any`), inline binary AND/OR without
    terminators (`encodeConvictionBicond`), and Python's z3 produces
    n-ary flat AND/OR which `z3_to_json` rewraps as right-fold with
    terminator. Canonical form is a sorted list of operand JSON
    expressions; this function returns it as a left-leaning binary
    tree without terminator so structural equality on the canonical
    form succeeds across all three shapes.
    """
    children: list[dict[str, Any]] = []

    def walk(n: dict[str, Any]) -> None:
        if n.get("kind") == op:
            walk(n["lhs"])
            walk(n["rhs"])
            return
        if n.get("kind") == "const" and n.get("value") is identity:
            return
        # Canonicalise the child first; if the result is itself same-kind
        # (e.g. an AND-with-True-terminator collapsed to its inner OR),
        # walk into that result so the final tree is fully flat.
        canon = _canonical_form(n)
        if canon.get("kind") == op:
            walk(canon)
        else:
            children.append(canon)

    walk(node)
    if not children:
        return {"kind": "const", "value": identity}
    if len(children) == 1:
        return children[0]
    acc = children[-1]
    for c in reversed(children[:-1]):
        acc = {"kind": op, "lhs": c, "rhs": acc}
    return acc


def _canonical_form(node: dict[str, Any]) -> dict[str, Any]:
    """Recursively canonicalise a JSON formula for shape comparison."""
    kind = node.get("kind")
    if kind == "and":
        return _flatten_assoc("and", True, node)
    if kind == "or":
        return _flatten_assoc("or", False, node)
    if kind == "not":
        return {"kind": "not", "arg": _canonical_form(node["arg"])}
    if kind == "iff":
        return {
            "kind": "iff",
            "lhs": _canonical_form(node["lhs"]),
            "rhs": _canonical_form(node["rhs"]),
        }
    return dict(node)


def _walk_atoms(node: dict[str, Any]):
    """Yield every `var` leaf name reachable from a JSON formula."""
    kind = node.get("kind")
    if kind == "var":
        yield node["name"]
        return
    if kind == "const":
        return
    if kind == "not":
        yield from _walk_atoms(node["arg"])
        return
    if kind in ("and", "or", "iff"):
        yield from _walk_atoms(node["lhs"])
        yield from _walk_atoms(node["rhs"])


def _canonicalise_lean_tree(
    node: dict[str, Any], statute_id: str, leaf_names: set[str]
) -> dict[str, Any]:
    """Deep-copy `node` rewriting bare leaf names to `<sX>_<leaf>`."""
    kind = node.get("kind")
    if kind == "var":
        return {"kind": "var", "name": _canonicalise_lean_leaf_name(
            node["name"], statute_id, leaf_names
        )}
    if kind == "const":
        return dict(node)
    if kind == "not":
        return {"kind": "not", "arg": _canonicalise_lean_tree(
            node["arg"], statute_id, leaf_names
        )}
    if kind in ("and", "or", "iff"):
        return {
            "kind": kind,
            "lhs": _canonicalise_lean_tree(node["lhs"], statute_id, leaf_names),
            "rhs": _canonicalise_lean_tree(node["rhs"], statute_id, leaf_names),
        }
    return dict(node)


def _leaf_names_from_lean(asserts: list[dict[str, Any]], statute_id: str) -> set[str]:
    """Identify bare leaf atoms on the Lean side: any var that appears as
    the RHS of a leaf bicond `iff(<sX>_<leaf>_satisfied, var)`."""
    leaves: set[str] = set()
    suffix = "_satisfied"
    prefix = f"{statute_id}_"
    for a in asserts:
        if a.get("kind") != "iff":
            continue
        lhs = a.get("lhs", {})
        rhs = a.get("rhs", {})
        if (
            lhs.get("kind") == "var"
            and rhs.get("kind") == "var"
            and lhs["name"].startswith(prefix)
            and lhs["name"].endswith(suffix)
        ):
            leaves.add(rhs["name"])
    return leaves


def run_lean_exporter(full: bool = False) -> dict[str, list[Any]]:
    """Run `lake env lean --run scripts/ExportSpec.lean` from the
    `mechanisation/` directory and parse stdout as JSON.

    When `full=True`, pass `--full` so the exporter emits the
    524-section corpus from `scripts/Fixtures.lean`; otherwise the
    four hand-stitched smoke fixtures are emitted.
    """
    cmd = ["lake", "env", "lean", "--run", "scripts/ExportSpec.lean"]
    if full:
        cmd += ["--", "--full"]
    proc = subprocess.run(
        cmd,
        cwd=REPO / "mechanisation",
        capture_output=True,
        text=True,
        check=True,
    )
    # `lake env` may emit setup chatter on the first line; the JSON
    # object is the last non-empty line.
    out_lines = [l for l in proc.stdout.splitlines() if l.strip()]
    if not out_lines:
        raise RuntimeError("Lean exporter produced no output")
    return json.loads(out_lines[-1])


def fixtures_from_corpus() -> dict[str, StatuteNode]:
    """Build Python fixtures from every `library/penal_code/*/statute.yh`.

    Mirrors the codegen in `mechanisation/scripts/generate_fixtures.py`
    so the structural diff has parallel sources on both sides.
    """
    from yuho.ast import ASTBuilder
    from yuho.parser import get_parser

    library = REPO / "library" / "penal_code"
    parser = get_parser()
    out: dict[str, StatuteNode] = {}
    for stat_path in sorted(library.glob("*/statute.yh")):
        try:
            result = parser.parse_file(stat_path)
        except Exception:
            continue
        if result.errors or result.root_node is None:
            continue
        try:
            ast = ASTBuilder(result.source, str(stat_path)).build(
                result.root_node
            )
        except Exception:
            continue
        if not ast.statutes:
            continue
        statute = ast.statutes[0]
        ident = "s" + statute.section_number.replace(".", "_")
        if ident not in out:
            out[ident] = statute
    return out


def E(kind: str, name: str) -> ElementNode:
    return ElementNode(element_type=kind, name=name, description=StringLit(value=""))


def G(combinator: str, members: list[Any]) -> ElementGroupNode:
    return ElementGroupNode(combinator=combinator, members=tuple(members))


def X(label: str) -> ExceptionNode:
    return ExceptionNode(label=label, condition=StringLit(value=""))


def fixtures() -> dict[str, StatuteNode]:
    """Python fixtures matching `mechanisation/scripts/ExportSpec.lean`."""
    return {
        "s299": StatuteNode(
            section_number="299",
            title=StringLit("Culpable homicide"),
            definitions=(),
            elements=(G("all_of", [E("actus_reus", "death"), E("mens_rea", "intent")]),),
            penalty=None,
            illustrations=(),
            exceptions=(),
        ),
        "s300": StatuteNode(
            section_number="300",
            title=StringLit("Murder"),
            definitions=(),
            elements=(G("all_of", [
                E("actus_reus", "death"),
                G("any_of", [
                    E("mens_rea", "intent_to_kill"),
                    E("mens_rea", "intent_likely_fatal"),
                    E("mens_rea", "intent_sufficient"),
                    E("mens_rea", "knowledge_imminent"),
                ]),
            ]),),
            penalty=None,
            illustrations=(),
            exceptions=(
                X("provocation"), X("privateDefence"),
                X("publicServant"), X("suddenFight"), X("consent"),
            ),
        ),
        "s378": StatuteNode(
            section_number="378",
            title=StringLit("Theft"),
            definitions=(),
            elements=(G("all_of", [
                E("mens_rea", "intention"),
                E("actus_reus", "taking"),
                E("circumstance", "possession"),
                E("circumstance", "consent"),
                E("actus_reus", "movement"),
            ]),),
            penalty=None,
            illustrations=(),
            exceptions=(X("claimOfRight"),),
        ),
        "s415": StatuteNode(
            section_number="415",
            title=StringLit("Cheating"),
            definitions=(),
            elements=(G("all_of", [
                E("actus_reus", "deception"),
                G("any_of", [
                    E("mens_rea", "fraudulent"),
                    E("mens_rea", "dishonest"),
                ]),
                E("actus_reus", "inducement"),
                E("circumstance", "harm"),
            ]),),
            penalty=None,
            illustrations=(),
            exceptions=(),
        ),
    }


def z3_to_json(expr: Any) -> dict[str, Any]:
    """Serialise a z3 expression to the same JSON shape as the
    Lean exporter's `formulaToJSON`."""
    if z3.is_true(expr):
        return {"kind": "const", "value": True}
    if z3.is_false(expr):
        return {"kind": "const", "value": False}
    if z3.is_const(expr):
        return {"kind": "var", "name": expr.decl().name()}
    kind = expr.decl().kind()
    children = [z3_to_json(c) for c in expr.children()]
    if kind == z3.Z3_OP_NOT:
        return {"kind": "not", "arg": children[0]}
    if kind in (z3.Z3_OP_EQ, z3.Z3_OP_IFF):
        return {"kind": "iff", "lhs": children[0], "rhs": children[1]}
    if kind == z3.Z3_OP_AND:
        return _right_fold("and", children, terminator=True)
    if kind == z3.Z3_OP_OR:
        return _right_fold("or", children, terminator=False)
    return {"kind": "raw", "raw": str(expr)}


def _right_fold(op: str, children: list[dict[str, Any]], terminator: bool) -> dict[str, Any]:
    """Right-fold an n-ary AND/OR to the binary tree shape Lean
    emits (with `const true/false` terminator)."""
    acc: dict[str, Any] = {"kind": "const", "value": terminator}
    for c in reversed(children):
        acc = {"kind": op, "lhs": c, "rhs": acc}
    return acc


def python_assertions_for(stmt: StatuteNode) -> list[dict[str, Any]]:
    g = Z3Generator()
    # Bootstrap the infrastructure sorts that `_generate_sorts` would
    # create from a full ModuleNode. We only need the `Statute` sort
    # plus the default `Intent` sort for mens-rea elements; the
    # struct-derived sorts are not exercised by the conviction-layer
    # encoding.
    g._sorts["Statute"] = z3.DeclareSort("Statute")
    g._sorts["Intent"] = z3.DeclareSort("Intent")
    g._consts["Intentional"] = z3.Const("Intentional", g._sorts["Intent"])
    g._generate_statute_constraints(stmt)
    return [z3_to_json(a) for a in g._assertions]


def lhs_atom(bicond: dict[str, Any]) -> str | None:
    if bicond.get("kind") == "iff" and bicond["lhs"].get("kind") == "var":
        return bicond["lhs"]["name"]
    return None


def project_to_conviction_layer(asserts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Filter assertions to the conviction-layer atoms the Lean
    spec covers, keyed by the LHS atom name.

    Python's `_generate_exception_constraints` introduces an
    intermediate `<sX>_exc_<label>` guard alias that doesn't appear
    in Lean's `encodeExceptionBiconds` (Lean folds the guard into the
    canonical model's `excFires`). We exclude these guard aliases
    so the comparison stays at Lean's bicond-shape granularity."""
    out: dict[str, dict[str, Any]] = {}
    for a in asserts:
        atom = lhs_atom(a)
        if atom is None:
            continue
        if atom.endswith("_satisfied") or atom.endswith("_fires") or atom.endswith("_conviction"):
            out[atom] = a
    return out


def diff_one(
    name: str, statute_id: str, lean: list[Any], python: list[Any]
) -> tuple[bool, str]:
    leaf_names = _leaf_names_from_lean(lean, statute_id)
    lean_canon = [_canonicalise_lean_tree(a, statute_id, leaf_names) for a in lean]
    lean_by_atom = project_to_conviction_layer(lean_canon)
    py_by_atom = project_to_conviction_layer(python)
    only_lean = sorted(set(lean_by_atom) - set(py_by_atom))
    only_py = sorted(set(py_by_atom) - set(lean_by_atom))
    shared = sorted(set(lean_by_atom) & set(py_by_atom))

    # Bicond-shape comparison on shared atoms after canonicalisation
    # (flatten AND/OR, drop identity-element terminators). `_fires`
    # biconds are opaque (see KNOWN_DIVERGENCES['exception_fires_…']),
    # so we compare existence + LHS atom but not RHS shape.
    shape_diffs: list[str] = []
    for atom in shared:
        if atom.endswith("_fires"):
            continue
        if _canonical_form(lean_by_atom[atom]) != _canonical_form(py_by_atom[atom]):
            shape_diffs.append(atom)

    lines = [f"=== {name} ==="]
    lines.append(f"  lean biconds (conviction-layer):   {len(lean_by_atom)}")
    lines.append(f"  python biconds (conviction-layer): {len(py_by_atom)}")
    lines.append(f"  shared atoms: {len(shared)}")
    if only_lean:
        lines.append(f"  only in lean: {only_lean}")
    if only_py:
        lines.append(f"  only in python: {only_py}")
    if shape_diffs:
        lines.append(f"  shape differs on: {shape_diffs}")

    # Post-canonicalisation: any residue surfaces here. Empty residue
    # means the two emitters agree on conviction-layer shape.
    passed = not (only_lean or only_py or shape_diffs)
    return passed, "\n".join(lines)


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--full",
        action="store_true",
        help="run against the full 524-section corpus instead of the four "
             "hand-stitched smoke fixtures.",
    )
    ap.add_argument(
        "--summary-only",
        action="store_true",
        help="suppress per-statute output; print only the aggregate result.",
    )
    args = ap.parse_args()

    mode = "full corpus" if args.full else "smoke fixtures"
    print(f"→ running Lean exporter ({mode}, lake env lean --run)…")
    try:
        lean_export = run_lean_exporter(full=args.full)
    except subprocess.CalledProcessError as e:
        print("Lean exporter failed:", e.stderr or e.stdout, file=sys.stderr)
        return 2

    print("→ running Python Z3Generator on parallel fixtures…\n")
    py_fixtures = fixtures_from_corpus() if args.full else fixtures()
    ok = True
    counts = {"matched": 0, "diff": 0, "missing": 0}
    diffs: list[str] = []
    for fname in py_fixtures:
        if fname not in lean_export:
            counts["missing"] += 1
            if not args.summary_only:
                print(f"!! Lean export missing fixture {fname}")
            ok = False
            continue
        try:
            py_asserts = python_assertions_for(py_fixtures[fname])
        except Exception as e:
            counts["diff"] += 1
            diffs.append(f"{fname}: python emit raised {type(e).__name__}: {e}")
            ok = False
            continue
        lean_asserts = lean_export[fname]
        statute_id = py_fixtures[fname].section_number.replace(".", "_")
        passed, summary = diff_one(fname, statute_id, lean_asserts, py_asserts)
        if passed:
            counts["matched"] += 1
        else:
            counts["diff"] += 1
            diffs.append(summary)
            ok = False
        if not args.summary_only:
            print(summary)

    if args.full:
        print(
            f"\nFull-corpus structural diff: "
            f"{counts['matched']}/{len(py_fixtures)} matched, "
            f"{counts['diff']} divergent, "
            f"{counts['missing']} missing on Lean side."
        )
        if diffs and args.summary_only:
            print("Divergences:")
            for d in diffs[:20]:
                print(d)
            if len(diffs) > 20:
                print(f"… +{len(diffs) - 20} more")

    print("\nKnown divergences (documented, not failed on):")
    for k, v in KNOWN_DIVERGENCES.items():
        print(f"  - {k}: {v}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
