"""Create a runnable Yuho starter workspace."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import click

from yuho.explain import DatalogExplainer
from yuho.services.analysis import analyze_file
from yuho.transpile.english_transpiler import EnglishTranspiler


STARTER_STATUTE = """statute 1 "Starter Theft" {
    definitions {
        property := "Movable property capable of being taken";
        dishonest := "Intent to cause wrongful gain or wrongful loss";
    }

    elements {
        all_of {
            actus_reus taking := "Taking movable property";
            mens_rea dishonest := "Acting with dishonest intent";
            circumstance without_consent := "Without the possessor's consent";
        }
    }

    penalty {
        imprisonment := 1 year .. 3 years;
        fine := unlimited;
    }

    illustration example1 {
        "A takes B's phone from B's desk without consent and intends to keep it."
    }
}
"""

STARTER_FACTS = {
    "taking": True,
    "dishonest": True,
    "without_consent": True,
}

LITERATE_STATUTE = """statute 1 "Literate Starter Misrepresentation" {
    definitions {
        representation := "A statement or conduct presented to another person";
        falsehood := "A representation that is untrue in a material respect";
    }

    elements {
        all_of {
            // source: legal-text.md#p1
            actus_reus representation := facts.representation.made && facts.representation.falsehood;
            // source: legal-text.md#p2
            mens_rea knowledge := facts.accused.knows_falsehood;
            // source: legal-text.md#p3
            circumstance reliance := facts.victim.relied;
        }
    }

    penalty {
        imprisonment := 1 day .. 1 year;
        fine := unlimited;
    }

    illustration example1 {
        "A states a material falsehood to B, knows it is false, and B relies on it."
    }
}
"""

LITERATE_FACTS = {
    "representation": {
        "made": True,
        "falsehood": True,
    },
    "accused": {
        "knows_falsehood": True,
    },
    "victim": {
        "relied": True,
    },
}

LITERATE_LEGAL_TEXT = """# Legal Text

<a id="p1"></a>
1. The accused makes a representation of fact to another person, and that
   representation is false in a material respect.

<a id="p2"></a>
2. At the time of making the representation, the accused knows that the
   representation is false.

<a id="p3"></a>
3. The other person relies on the representation.
"""


def run_init(
    *,
    directory: str,
    force: bool = False,
    run_smoke: bool = True,
    template: str = "basic",
    json_output: bool = False,
) -> None:
    """Create starter files and optionally validate them."""
    root = Path(directory)
    if root.exists() and any(root.iterdir()) and not force:
        click.echo(
            f"error: {root} already exists and is not empty; pass --force to overwrite",
            err=True,
        )
        sys.exit(2)

    statute_path = root / "statute.yh"
    facts_path = root / "facts.json"
    readme_path = root / "README.md"
    legal_text_path = root / "legal-text.md"
    out_dir = root / "out"
    out_path = out_dir / "starter.txt"
    starter = _template(template)

    root.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    statute_path.write_text(starter["statute"], encoding="utf-8")
    facts_path.write_text(json.dumps(starter["facts"], indent=2) + "\n", encoding="utf-8")
    readme_path.write_text(_starter_readme(template), encoding="utf-8")
    if starter["legal_text"] is not None:
        legal_text_path.write_text(starter["legal_text"], encoding="utf-8")

    smoke: dict[str, Any] = {"ran": run_smoke, "valid": None, "explains": None}
    if run_smoke:
        smoke = _run_smoke(statute_path, facts_path, out_path)

    commands = _next_commands(root)
    if json_output:
        click.echo(
            json.dumps(
                {
                    "created": {
                        "directory": str(root),
                        "template": template,
                        "statute": str(statute_path),
                        "facts": str(facts_path),
                        "readme": str(readme_path),
                        "legal_text": (
                            str(legal_text_path) if starter["legal_text"] is not None else None
                        ),
                        "english": str(out_path) if run_smoke else None,
                    },
                    "smoke": smoke,
                    "commands": commands,
                },
                indent=2,
            )
        )
        return

    click.echo(f"Created Yuho starter workspace: {root}")
    click.echo(f"  statute: {statute_path}")
    click.echo(f"  facts:   {facts_path}")
    click.echo(f"  readme:  {readme_path}")
    if starter["legal_text"] is not None:
        click.echo(f"  source:  {legal_text_path}")
    if run_smoke:
        click.echo(f"  smoke:   check=OK explain=OK english={out_path}")
    click.echo("")
    click.echo("Try:")
    for command in commands:
        click.echo(f"  {command}")


def _run_smoke(statute_path: Path, facts_path: Path, out_path: Path) -> dict[str, Any]:
    analysis = analyze_file(statute_path, run_semantic=True)
    valid = not analysis.parse_errors and analysis.ast is not None and not analysis.errors
    if not valid or analysis.ast is None:
        click.echo(f"error: generated starter failed validation: {statute_path}", err=True)
        sys.exit(1)

    statute = analysis.ast.statutes[0]
    facts = json.loads(facts_path.read_text(encoding="utf-8"))
    statutes = {st.section_number: st for st in analysis.ast.statutes}
    trace = DatalogExplainer().explain(statute, facts, statutes)
    english = EnglishTranspiler().transpile(analysis.ast).output
    out_path.write_text(english, encoding="utf-8")
    return {
        "ran": True,
        "valid": valid,
        "explains": trace.overall_satisfied,
        "english": str(out_path),
    }


def _next_commands(root: Path) -> list[str]:
    return [
        f"cd {root}",
        "yuho check statute.yh",
        "yuho transpile -t english statute.yh -o out/starter.txt",
        "yuho explain statute.yh --facts facts.json",
        "yuho irac statute.yh --facts facts.json",
        "yuho debug facts.json statute.yh --break-on element",
        "yuho verify --engine z3 statute.yh",
    ]


def _template(name: str) -> dict[str, Any]:
    if name == "statute-literate":
        return {
            "statute": LITERATE_STATUTE,
            "facts": LITERATE_FACTS,
            "legal_text": LITERATE_LEGAL_TEXT,
        }
    return {
        "statute": STARTER_STATUTE,
        "facts": STARTER_FACTS,
        "legal_text": None,
    }


def _starter_readme(template: str) -> str:
    source_note = (
        "\n`statute.yh` includes `source: legal-text.md#...` anchors next to executable predicates.\n"
        if template == "statute-literate"
        else ""
    )
    return f"""# Yuho starter

This directory was generated by `yuho init`.
{source_note}

```sh
yuho check statute.yh
yuho transpile -t english statute.yh -o out/starter.txt
yuho explain statute.yh --facts facts.json
yuho irac statute.yh --facts facts.json
yuho debug facts.json statute.yh --break-on element
yuho verify --engine z3 statute.yh
```
"""
