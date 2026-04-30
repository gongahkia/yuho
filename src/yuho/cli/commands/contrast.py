"""``yuho contrast`` — Z3-driven counter-factual edge-case explorer.

Given two encoded sections, asks Z3 for a fact pattern that satisfies
section A's conviction predicate (elements all hold AND no defeating
exception fires) while *failing* section B's conviction predicate.
The result is the structural boundary between the two offences,
machine-derived rather than hand-constructed.

Built directly on the apply_scope / is_infringed Z3 hookup: the
generator already declares ``<sX>_conviction`` Bools and asserts
the per-statute element + exception constraints. We add
``s_A_conviction AND NOT s_B_conviction`` and read off the
satisfying assignment of leaf-element ``*_satisfied`` Bools.

Example::

    yuho contrast s299 s300            # what makes culpable homicide *not* murder?
    yuho contrast s302 s79             # what makes private-defence override murder?

Output is a structured fact pattern; users can copy it into a
simulator fixture or feed it to ``yuho recommend`` to verify the
recommender ranks A above B for that fact pattern.

Caveats:

* ``yuho contrast`` reports *some* satisfying fact pattern, not
  necessarily the *minimum-distance* one. The minimum-distance
  variant requires Z3's :class:`Optimize` interface and a cardinality
  objective; punted to a follow-up.
* Sections that share the same elements (subsumes-only difference,
  e.g. s302 vs s304) won't yield a contrast model — by construction.
* Cross-section ``apply_scope`` / ``is_infringed`` references resolve
  cleanly because the generator declares conviction Bools lazily and
  the solver picks consistent values.
"""

from __future__ import annotations

import json as _json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from yuho.services.analysis import analyze_file


def _statute_yh_for(library: Path, section: str) -> Optional[Path]:
    """Find the encoded `.yh` for the given section under `library`."""
    section = section.lstrip("sS")
    # Convention: `library/penal_code/sNNN_<slug>/statute.yh`.
    candidates = list(library.glob(f"s{section}_*/statute.yh"))
    if candidates:
        return candidates[0]
    # Fallback: any directory whose statute parses to the matching number.
    for stat_path in library.glob("*/statute.yh"):
        try:
            r = analyze_file(stat_path, run_semantic=False)
        except Exception:
            continue
        if r.ast and r.ast.statutes and r.ast.statutes[0].section_number == section:
            return stat_path
    return None


_REFERENCING_LINE = re.compile(
    r"^referencing\s+penal_code/(s\d+[A-Z]*)_", re.MULTILINE
)


def _resolve_offence_paths(
    library: Path, section: str, offence_path: Path
) -> List[Path]:
    """Return the set of ``.yh`` paths to feed into a combined module so
    that ``<sX>_elements_satisfied`` is materialised for the offence
    section.

    Punishment-only sections (s417 / s419 / s426 / s447 / s448 / s500 /
    s363A) carry a ``referencing penal_code/sN_<slug>`` directive that
    points at the host offence whose elements they punish. The Z3
    backend never sees the host's elements unless its statute file is
    parsed alongside, so the bare offence path returns no
    ``_elements_satisfied`` constant. This helper detects the
    directive and prepends every host path to the module-build input.

    Returns a list with the offence path first (preserving the
    existing semantics for sections that *do* declare their own
    elements) and the referenced hosts appended."""
    paths: List[Path] = [offence_path]
    try:
        text = offence_path.read_text(encoding="utf-8")
    except OSError:
        return paths
    for m in _REFERENCING_LINE.finditer(text):
        host = m.group(1)
        host_path = _statute_yh_for(library, host)
        if host_path is not None and host_path not in paths:
            paths.append(host_path)
    return paths


def _build_combined_module(paths: List[Path]):
    """Parse each .yh file and return a single ModuleNode with all statutes."""
    from yuho.ast import nodes
    sources = []
    statutes = []
    for p in paths:
        r = analyze_file(p, run_semantic=False)
        if r.ast is None:
            raise click.ClickException(
                f"failed to parse {p}: {[str(e) for e in r.parse_errors]}"
            )
        sources.append(r.ast)
        statutes.extend(r.ast.statutes)
    # Synthesise a combined module so Z3Generator sees both statutes at once.
    # Reuse the first AST as the carrier and replace its `statutes` tuple.
    base = sources[0]
    return nodes.ModuleNode(
        imports=tuple(getattr(base, "imports", ()) or ()),
        type_defs=tuple(base.type_defs),
        function_defs=tuple(base.function_defs),
        statutes=tuple(statutes),
        variables=tuple(base.variables),
        assertions=tuple(getattr(base, "assertions", ()) or ()),
        enum_defs=tuple(getattr(base, "enum_defs", ()) or ()),
        type_aliases=tuple(getattr(base, "type_aliases", ()) or ()),
    )


def _read_model_facts(model, consts: Dict[str, Any], statute_id: str) -> Dict[str, bool]:
    """Walk the Z3 model for every `<statute_id>_<elem>_satisfied` Bool
    and return the {element_name: bool} map."""
    out: Dict[str, bool] = {}
    prefix = f"{statute_id}_"
    suffix = "_satisfied"
    for name, var in consts.items():
        if not name.startswith(prefix) or not name.endswith(suffix):
            continue
        if name == f"{statute_id}_elements_satisfied":
            continue
        elem_name = name[len(prefix): -len(suffix)]
        try:
            v = model.evaluate(var, model_completion=True)
        except Exception:
            continue
        out[elem_name] = bool(v)
    return out


def run_contrast(
    section_a: str,
    section_b: str,
    *,
    library: Optional[str] = None,
    json_output: bool = False,
    minimal: bool = False,
    timeout_ms: int = 30000,
) -> None:
    """Shell entrypoint for ``yuho contrast``.

    When ``minimal`` is True, uses Z3's ``Optimize`` interface to find
    a satisfying assignment that minimises the count of leaf-element
    ``*_satisfied`` Bools that are True — i.e. the smallest fact-set
    (by hamming weight) that distinguishes A from B. Slower than the
    default any-model search; honour the timeout knob accordingly.
    """
    try:
        import z3  # noqa: F401
    except ImportError:
        raise click.ClickException(
            "z3-solver is not installed. Install with: pip install -e '.[verify]'"
        )

    lib_root = Path(library) if library else Path("library/penal_code")
    if not lib_root.exists():
        raise click.ClickException(
            f"library directory not found: {lib_root} "
            f"(pass --library if your encoded library is elsewhere)"
        )

    a_path = _statute_yh_for(lib_root, section_a)
    if a_path is None:
        raise click.ClickException(f"could not locate encoded section {section_a} under {lib_root}")
    b_path = _statute_yh_for(lib_root, section_b)
    if b_path is None:
        raise click.ClickException(f"could not locate encoded section {section_b} under {lib_root}")

    module = _build_combined_module([a_path, b_path])

    from yuho.verify.z3_solver import Z3Generator
    gen = Z3Generator()
    gen.generate(module)

    a_id = section_a.lstrip("sS").replace(".", "_")
    b_id = section_b.lstrip("sS").replace(".", "_")
    a_conviction = gen._consts.get(f"{a_id}_conviction")
    b_conviction = gen._consts.get(f"{b_id}_conviction")
    missing = []
    if a_conviction is None:
        missing.append(section_a)
    if b_conviction is None:
        missing.append(section_b)
    if missing:
        raise click.ClickException(
            "no elements declared for: " + ", ".join(missing)
            + ". The section is likely interpretation-only "
              "(definitions / penalty / illustrations only) and has "
              "no conviction predicate to contrast against."
        )

    import z3
    if minimal:
        solver = z3.Optimize()
        solver.set("timeout", timeout_ms)
        for assertion in gen._assertions:
            solver.add(assertion)
        solver.add(a_conviction)
        solver.add(z3.Not(b_conviction))
        # Minimise the number of `*_satisfied` Bools that are True across
        # both statutes — the smallest fact-set (by count) that still
        # distinguishes A from B. `If(b, 1, 0)` lifts each Bool to an Int
        # so `Sum` is well-typed.
        weight_terms = [
            z3.If(var, 1, 0)
            for name, var in gen._consts.items()
            if name.endswith("_satisfied")
            and name not in (f"{a_id}_elements_satisfied",
                             f"{b_id}_elements_satisfied")
        ]
        if weight_terms:
            solver.minimize(z3.Sum(*weight_terms))
    else:
        solver = z3.Solver()
        solver.set("timeout", timeout_ms)
        for assertion in gen._assertions:
            solver.add(assertion)
        solver.add(a_conviction)
        solver.add(z3.Not(b_conviction))

    result = solver.check()
    if result != z3.sat:
        msg = (
            f"no contrast: every fact pattern satisfying {section_a} also "
            f"satisfies {section_b} (status: {result}). The two sections "
            f"may share their full element set, or one subsumes the other "
            f"with no distinguishing structural feature."
        )
        if json_output:
            click.echo(_json.dumps({"contrast": False, "reason": msg}, indent=2))
        else:
            click.echo(msg)
        sys.exit(1)

    model = solver.model()
    a_facts = _read_model_facts(model, gen._consts, a_id)
    b_facts = _read_model_facts(model, gen._consts, b_id)

    payload = {
        "contrast": True,
        "section_a": section_a,
        "section_b": section_b,
        "fact_pattern": {
            f"{section_a}_elements": a_facts,
            f"{section_b}_elements": b_facts,
        },
        "a_conviction": True,
        "b_conviction": False,
        "not_legal_advice": True,
        "disclaimer": (
            "Z3-derived structural fact pattern, not legal advice. "
            "Real cases turn on evidence, not encoded element shape."
        ),
    }

    if json_output:
        click.echo(_json.dumps(payload, indent=2, ensure_ascii=False))
        sys.exit(0)

    # Human-readable rendering.
    click.echo(f"contrast: {section_a} satisfied, {section_b} not satisfied\n")
    click.echo(f"{section_a} elements:")
    if not a_facts:
        click.echo("  (no leaf elements)")
    for name, val in sorted(a_facts.items()):
        click.echo(f"  {'✓' if val else '✗'} {name}")
    click.echo(f"\n{section_b} elements:")
    if not b_facts:
        click.echo("  (no leaf elements)")
    for name, val in sorted(b_facts.items()):
        click.echo(f"  {'✓' if val else '✗'} {name}")
    distinguishing = sorted(
        n for n, v_a in a_facts.items()
        if v_a and not b_facts.get(n, False) and n in b_facts
    )
    if distinguishing:
        click.echo(f"\ndistinguishing elements (true in {section_a}, false in {section_b}):")
        for n in distinguishing:
            click.echo(f"  • {n}")
    click.echo(
        "\nNot legal advice — Z3-derived structural boundary. "
        "Real cases turn on evidence."
    )
    sys.exit(0)
