"""``yuho narrow-defence`` — smallest fact pattern where a defence
section's elements fire alongside an offence section's.

The Singapore Penal Code's general defences (Chapter IV: ss76–106)
live as standalone statutes, not as exceptions inside each offence.
That means structural reasoning about "when can defence X be raised
against offence Y?" is best modelled as: *find a fact pattern where
both sections' element conjunctions are simultaneously satisfied*.
The answer is the structural floor for the defence's availability
against that offence.

Builds on the Z3 backend the same way ``yuho contrast`` does:

    yuho narrow-defence s302 s79     # murder vs private-defence-of-body
    yuho narrow-defence s378 s95     # theft vs trifling-harm
    yuho narrow-defence s302 s84 --minimal   # smallest fact-set

Returned model lists the leaf elements of both sections that must
hold for the structural overlap. NOT a doctrinal claim that the
defence will succeed — that's evidentiary. The contract here is
the structural-availability floor.
"""

from __future__ import annotations

import json as _json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _section_id_from_path(path: Path) -> str:
    """Extract the bare section id (e.g. ``425`` or ``363A``) from a
    library path of the form ``library/penal_code/sNNN[A-Z]*_…``.
    Mirrors the canonical form ``Z3Generator`` uses to key its
    constants table."""
    name = path.parent.name
    m = re.match(r"^s(\d+[A-Z]*)_", name)
    return m.group(1) if m else name

import click

from yuho.cli.commands.contrast import (
    _build_combined_module,
    _read_model_facts,
    _resolve_offence_paths,
    _statute_yh_for,
)


def run_narrow_defence(
    offence_section: str,
    defence_section: str,
    *,
    library: Optional[str] = None,
    json_output: bool = False,
    minimal: bool = False,
    timeout_ms: int = 30000,
) -> None:
    """Shell entrypoint for ``yuho narrow-defence``."""
    try:
        import z3
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

    o_path = _statute_yh_for(lib_root, offence_section)
    if o_path is None:
        raise click.ClickException(
            f"could not locate encoded section {offence_section} under {lib_root}"
        )
    d_path = _statute_yh_for(lib_root, defence_section)
    if d_path is None:
        raise click.ClickException(
            f"could not locate encoded section {defence_section} under {lib_root}"
        )

    # Punishment-only sections (s417 / s419 / s426 / s447 / s448 /
    # s500 / s363A) declare a ``referencing penal_code/sN_…`` directive
    # at the top of statute.yh; we lift the host's element block by
    # parsing it alongside in the combined module so
    # `<host_id>_elements_satisfied` is materialised, and fall through
    # to it as the offence's elements predicate when the bare offence
    # carries no own elements.
    offence_paths = _resolve_offence_paths(lib_root, offence_section, o_path)
    module = _build_combined_module(offence_paths + [d_path])

    from yuho.verify.z3_solver import Z3Generator
    gen = Z3Generator()
    gen.generate(module)

    o_id = offence_section.lstrip("sS").replace(".", "_")
    d_id = defence_section.lstrip("sS").replace(".", "_")
    o_elements_sat = gen._consts.get(f"{o_id}_elements_satisfied")
    d_elements_sat = gen._consts.get(f"{d_id}_elements_satisfied")

    # Referencing-host fallback: if the offence section's own
    # `_elements_satisfied` exists but is empty (BoolVal(True) — see
    # z3_solver.py around line 1170, emitted for interpretation-only
    # / punishment-only shapes), prefer the referenced host's
    # elements predicate. This fixes the s426 / s447 / etc. encoder
    # gap classified in `evals/case_law/results-defeats-coverage-classification.json`.
    o_id_used = o_id
    if len(offence_paths) > 1:
        for host_path in offence_paths[1:]:
            host_id = _section_id_from_path(host_path)
            host_sat = gen._consts.get(f"{host_id}_elements_satisfied")
            if host_sat is not None:
                o_elements_sat = host_sat
                o_id_used = host_id
                break

    missing = []
    if o_elements_sat is None:
        missing.append(offence_section)
    if d_elements_sat is None:
        missing.append(defence_section)
    if missing:
        raise click.ClickException(
            "no elements declared for: " + ", ".join(missing)
            + ". The section likely declares its elements inside a "
              "subsection that this command does not yet flatten, or "
              "the section is interpretation-only with no element "
              "structure to query."
        )

    if minimal:
        solver = z3.Optimize()
        solver.set("timeout", timeout_ms)
        for assertion in gen._assertions:
            solver.add(assertion)
        solver.add(o_elements_sat)
        solver.add(d_elements_sat)
        weight_terms = [
            z3.If(var, 1, 0)
            for name, var in gen._consts.items()
            if name.endswith("_satisfied")
            and name not in (f"{o_id}_elements_satisfied",
                             f"{d_id}_elements_satisfied")
        ]
        if weight_terms:
            solver.minimize(z3.Sum(*weight_terms))
    else:
        solver = z3.Solver()
        solver.set("timeout", timeout_ms)
        for assertion in gen._assertions:
            solver.add(assertion)
        solver.add(o_elements_sat)
        solver.add(d_elements_sat)

    result = solver.check()
    if result != z3.sat:
        msg = (
            f"no structural overlap: no fact pattern simultaneously "
            f"satisfies the elements of {offence_section} and "
            f"{defence_section} (status: {result}). The defence may not "
            f"be structurally available against this offence in the "
            f"encoded model."
        )
        if json_output:
            click.echo(_json.dumps({"overlap": False, "reason": msg}, indent=2))
        else:
            click.echo(msg)
        sys.exit(1)

    model = solver.model()
    o_facts = _read_model_facts(model, gen._consts, o_id_used)
    d_facts = _read_model_facts(model, gen._consts, d_id)
    shared = sorted(
        n for n, v in o_facts.items()
        if v and d_facts.get(n) is True
    )

    payload = {
        "overlap": True,
        "offence": offence_section,
        "defence": defence_section,
        "minimal": minimal,
        "fact_pattern": {
            f"{offence_section}_elements": o_facts,
            f"{defence_section}_elements": d_facts,
        },
        "shared_satisfied_names": shared,
        "not_legal_advice": True,
        "disclaimer": (
            "Z3-derived structural-availability floor for the defence "
            "against the offence; not a doctrinal claim about whether "
            "the defence would succeed evidentially."
        ),
    }

    if json_output:
        click.echo(_json.dumps(payload, indent=2, ensure_ascii=False))
        sys.exit(0)

    # Human-readable rendering.
    click.echo(
        f"structural overlap: {offence_section} elements + "
        f"{defence_section} elements both satisfied"
        + (" (minimised)" if minimal else "")
        + "\n"
    )
    click.echo(f"{offence_section} elements:")
    if not o_facts:
        click.echo("  (no leaf elements)")
    for name, val in sorted(o_facts.items()):
        click.echo(f"  {'✓' if val else '✗'} {name}")
    click.echo(f"\n{defence_section} elements:")
    if not d_facts:
        click.echo("  (no leaf elements)")
    for name, val in sorted(d_facts.items()):
        click.echo(f"  {'✓' if val else '✗'} {name}")
    if shared:
        click.echo(
            f"\nshared element names that fire on both sides: "
            f"{', '.join(shared)}"
        )
    click.echo(
        "\nNot legal advice — structural-availability floor only. "
        "Whether the defence will succeed turns on evidence."
    )
    sys.exit(0)
