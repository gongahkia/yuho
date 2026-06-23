"""Create a runnable Yuho starter workspace."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import click

from yuho.explain import DatalogExplainer
from yuho.services.analysis import analyze_file, analyze_source
from yuho.transpile.english_transpiler import EnglishTranspiler


TEMPLATE_CHOICES = (
    "basic",
    "statute-literate",
    "statute-exceptions",
    "statute-cross-reference",
)

ELEMENT_LINE_RE = re.compile(
    r"^(?P<indent>\s*)"
    r"(?P<kind>actus_reus|mens_rea|circumstance|obligation|prohibition|permission|"
    r"party|obligation_to|condition_precedent|breach)\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*:=\s*"
    r"(?P<expr>.*?);$",
    re.MULTILINE,
)

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

EXCEPTIONS_STATUTE = """statute 1 "Starter Offence With Defence" {
    elements {
        all_of {
            actus_reus act := facts.conduct.act;
            mens_rea intent := facts.accused.intent;
        }
    }

    exception lawful_authority {
        "The conduct is excused when lawful authority applies."
        when facts.defence.lawful_authority
    }

    penalty {
        imprisonment := 1 day .. 6 months;
        fine := unlimited;
    }
}
"""

EXCEPTIONS_FACTS = {
    "conduct": {
        "act": True,
    },
    "accused": {
        "intent": True,
    },
    "defence": {
        "lawful_authority": False,
    },
}

CROSS_REFERENCE_STATUTE = """statute 2 "Starter Aggravated Offence" {
    elements {
        all_of {
            circumstance base_offence := apply_scope(s1, facts);
            circumstance aggravation := facts.context.aggravated;
        }
    }

    penalty {
        imprisonment := 1 month .. 1 year;
        fine := unlimited;
    }
}

statute 1 "Starter Base Offence" {
    elements {
        all_of {
            actus_reus act := facts.conduct.act;
            mens_rea intent := facts.accused.intent;
        }
    }
}
"""

CROSS_REFERENCE_FACTS = {
    "conduct": {
        "act": True,
    },
    "accused": {
        "intent": True,
    },
    "context": {
        "aggravated": True,
    },
}


def run_init(
    *,
    directory: str,
    force: bool = False,
    run_smoke: bool = True,
    template: str = "basic",
    guided: bool = False,
    json_output: bool = False,
) -> None:
    """Create starter files and optionally validate them."""
    title: str | None = None
    if guided:
        if json_output:
            click.echo("error: --guided cannot be combined with --json", err=True)
            sys.exit(2)
        template, run_smoke, title = _guided_options(template, run_smoke)

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
    if title:
        starter = {**starter, "statute": _replace_primary_title(starter["statute"], title)}
    if guided:
        starter = {**starter, "statute": _guided_element_expressions(starter["statute"])}
        _validate_generated_source(starter["statute"])

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
    if guided:
        click.echo(f"  guided:  template={template}")
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


def _guided_options(template: str, run_smoke: bool) -> tuple[str, bool, str]:
    click.echo("Yuho guided init")
    selected_template = click.prompt(
        "Template",
        type=click.Choice(TEMPLATE_CHOICES),
        default=template,
        show_choices=True,
    )
    title = click.prompt("Primary statute title", default=_default_title(selected_template))
    if run_smoke:
        run_smoke = click.confirm("Run smoke checks", default=True)
    return selected_template, run_smoke, title


def _guided_element_expressions(statute_source: str) -> str:
    matches = list(ELEMENT_LINE_RE.finditer(statute_source))
    if not matches:
        return statute_source
    click.echo("Executable elements")
    current = statute_source
    offset = 0
    for match in matches:
        start = match.start("expr") + offset
        end = match.end("expr") + offset
        kind = match.group("kind")
        name = match.group("name")
        while True:
            value = click.prompt(
                f"{kind} {name} expression",
                default=current[start:end],
                show_default=True,
            )
            candidate = current[:start] + value + current[end:]
            error = _source_validation_error(candidate)
            if error is None:
                offset += len(value) - (end - start)
                current = candidate
                break
            click.echo(f"invalid element expression: {error}", err=True)
    return current


def _validate_generated_source(statute_source: str) -> None:
    error = _source_validation_error(statute_source)
    if error is not None:
        click.echo(f"error: guided starter failed validation before write: {error}", err=True)
        sys.exit(1)


def _source_validation_error(statute_source: str) -> str | None:
    analysis = analyze_source(statute_source, file="<guided-init>", run_semantic=False)
    if analysis.parse_errors:
        return str(analysis.parse_errors[0])
    if analysis.ast is None:
        return "no AST produced"
    return None


def _default_title(template: str) -> str:
    return {
        "statute-literate": "Literate Starter Misrepresentation",
        "statute-exceptions": "Starter Offence With Defence",
        "statute-cross-reference": "Starter Aggravated Offence",
    }.get(template, "Starter Theft")


def _replace_primary_title(statute_source: str, title: str) -> str:
    safe_title = title.replace('"', "'")
    return re.sub(
        r'(statute\s+\S+\s+)".*?"',
        rf'\1"{safe_title}"',
        statute_source,
        count=1,
    )


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
    if name == "statute-exceptions":
        return {
            "statute": EXCEPTIONS_STATUTE,
            "facts": EXCEPTIONS_FACTS,
            "legal_text": None,
        }
    if name == "statute-cross-reference":
        return {
            "statute": CROSS_REFERENCE_STATUTE,
            "facts": CROSS_REFERENCE_FACTS,
            "legal_text": None,
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
