"""
TUI wizard for interactive statute creation.

Provides a step-by-step wizard interface for building Yuho statutes
using inquirer-style prompts. Generates valid .yh files from user input.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field

import click


@dataclass
class ElementData:
    """Data for a statute element."""
    element_type: str  # "actus_reus", "mens_rea", "circumstance", "obligation", "prohibition", "permission"
    name: str
    description: str
    caused_by: str = "" # optional causal link
    burden: str = "" # "prosecution" or "defence"


@dataclass
class DefinitionData:
    """Data for a definition entry."""
    term: str
    definition: str


@dataclass
class IllustrationData:
    """Data for an illustration."""
    label: str
    description: str


@dataclass
class ExceptionData:
    """Data for a statute exception."""
    label: str
    condition: str
    effect: str = ""
    guard: str = "" # optional when guard expression


@dataclass
class CaseLawData:
    """Data for case law reference."""
    case_name: str
    citation: str = ""
    holding: str = ""
    element_ref: str = "" # element this case interprets


@dataclass
class PenaltyData:
    """Data for penalty specification."""
    has_imprisonment: bool = False
    imprisonment_min: str = ""
    imprisonment_max: str = ""
    has_fine: bool = False
    fine_min: str = ""
    fine_max: str = ""
    supplementary: str = ""


@dataclass
class StatuteData:
    """Complete data for a statute."""
    section_number: str = ""
    title: str = ""
    effective_date: str = "" # e.g. "1872-01-01"
    definitions: List[DefinitionData] = field(default_factory=list)
    elements: List[ElementData] = field(default_factory=list)
    penalty: Optional[PenaltyData] = None
    illustrations: List[IllustrationData] = field(default_factory=list)
    exceptions: List[ExceptionData] = field(default_factory=list)
    case_law: List[CaseLawData] = field(default_factory=list)
    element_grouping: str = "" # "", "all_of", or "any_of"
    auto_struct_name: str = ""
    auto_struct_fields: List[Tuple[str, str]] = field(default_factory=list)


def prompt_input(prompt: str, default: str = "", required: bool = False) -> str:
    """Prompt for text input."""
    while True:
        if default:
            result = click.prompt(prompt, default=default, show_default=True)
        else:
            result = click.prompt(prompt, default="", show_default=False)
        
        if required and not result.strip():
            click.echo("  This field is required.")
            continue
        
        return result.strip()


def prompt_confirm(prompt: str, default: bool = False) -> bool:
    """Prompt for yes/no confirmation."""
    return click.confirm(prompt, default=default)


def prompt_choice(prompt: str, choices: List[str], default: int = 0) -> str:
    """Prompt for choice from list."""
    click.echo(f"\n{prompt}")
    for i, choice in enumerate(choices):
        marker = ">" if i == default else " "
        click.echo(f"  {marker} [{i + 1}] {choice}")
    
    while True:
        value = click.prompt("Enter number", default=str(default + 1))
        try:
            idx = int(value) - 1
            if 0 <= idx < len(choices):
                return choices[idx]
        except ValueError:
            pass
        click.echo(f"  Please enter a number between 1 and {len(choices)}")


def wizard_header(title: str) -> None:
    """Print a wizard section header."""
    click.echo("")
    click.echo(click.style(f"═══ {title} ═══", fg="cyan", bold=True))
    click.echo("")


def collect_definitions(data: StatuteData) -> None:
    """Collect definition entries."""
    wizard_header("Definitions")
    click.echo("Define key terms used in the statute.")
    click.echo("(Press Enter with empty term to finish)")
    click.echo("")
    
    while True:
        term = prompt_input("Term to define")
        if not term:
            break
        
        definition = prompt_input(f"  Definition of '{term}'", required=True)
        data.definitions.append(DefinitionData(term=term, definition=definition))
        click.echo(click.style(f"  ✓ Added definition: {term}", fg="green"))
    
    click.echo(f"\nTotal definitions: {len(data.definitions)}")


def collect_elements(data: StatuteData) -> None:
    """Collect offense elements."""
    wizard_header("Elements of the Offense")
    click.echo("Define the elements (actus reus, mens rea, circumstances)")
    click.echo("")
    
    # Actus Reus
    if prompt_confirm("Add actus reus (physical act) element?", default=True):
        name = prompt_input("  Element name/identifier", default="act", required=True)
        desc = prompt_input("  Description of the act", required=True)
        data.elements.append(ElementData(
            element_type="actus_reus",
            name=name,
            description=desc
        ))
        click.echo(click.style(f"  ✓ Added actus_reus: {name}", fg="green"))
    
    # Mens Rea
    if prompt_confirm("Add mens rea (mental state) element?", default=True):
        name = prompt_input("  Element name/identifier", default="intent", required=True)
        desc = prompt_input("  Description of required mental state", required=True)
        data.elements.append(ElementData(
            element_type="mens_rea",
            name=name,
            description=desc
        ))
        click.echo(click.style(f"  ✓ Added mens_rea: {name}", fg="green"))
    
    # Additional elements
    while prompt_confirm("Add another element?", default=False):
        element_type = prompt_choice("Element type:", [
            "actus_reus",
            "mens_rea",
            "circumstance",
            "obligation",
            "prohibition",
            "permission",
        ])
        name = prompt_input("  Element name", required=True)
        desc = prompt_input("  Description", required=True)
        caused_by = prompt_input("  Caused by (optional, element name)")
        burden = ""
        if prompt_confirm("  Specify burden of proof?", default=False):
            burden = prompt_choice("  Burden:", ["prosecution", "defence"])
        data.elements.append(ElementData(
            element_type=element_type,
            name=name,
            description=desc,
            caused_by=caused_by,
            burden=burden,
        ))
        click.echo(click.style(f"  ✓ Added {element_type}: {name}", fg="green"))
    
    click.echo(f"\nTotal elements: {len(data.elements)}")

    # element grouping
    if len(data.elements) >= 2:
        if prompt_confirm("Group elements with all_of/any_of?", default=False):
            combinator = prompt_choice("Combinator type:", ["all_of", "any_of"])
            data.element_grouping = combinator
            click.echo(click.style(f"  ✓ Elements grouped with {combinator}", fg="green"))

    # auto-generate struct
    if data.elements:
        if prompt_confirm("Auto-generate a case struct from elements?", default=False):
            default_name = f"Case{data.section_number}" if data.section_number else "CaseStruct"
            struct_name = prompt_input("Struct name", default=default_name, required=True)
            data.auto_struct_name = struct_name
            for elem in data.elements:
                data.auto_struct_fields.append(("bool", elem.name))
            click.echo(click.style(f"  ✓ Struct '{struct_name}' will be generated with {len(data.auto_struct_fields)} fields", fg="green"))


def collect_penalty(data: StatuteData) -> None:
    """Collect penalty specification."""
    wizard_header("Penalty")
    
    if not prompt_confirm("Does this statute have a penalty clause?", default=True):
        return
    
    penalty = PenaltyData()
    
    # Imprisonment
    if prompt_confirm("Include imprisonment?", default=True):
        penalty.has_imprisonment = True
        penalty.imprisonment_max = prompt_input(
            "  Maximum imprisonment (e.g., '10 years', '3Y')",
            required=True
        )
        if prompt_confirm("  Specify minimum imprisonment?", default=False):
            penalty.imprisonment_min = prompt_input("  Minimum imprisonment")
    
    # Fine
    if prompt_confirm("Include fine?", default=True):
        penalty.has_fine = True
        penalty.fine_max = prompt_input(
            "  Maximum fine (e.g., 'SGD 10000', '$5000')",
            required=True
        )
        if prompt_confirm("  Specify minimum fine?", default=False):
            penalty.fine_min = prompt_input("  Minimum fine")
    
    # Supplementary
    if prompt_confirm("Add supplementary penalty info?", default=False):
        penalty.supplementary = prompt_input("  Supplementary information")
    
    data.penalty = penalty
    click.echo(click.style("  ✓ Penalty configured", fg="green"))


def collect_illustrations(data: StatuteData) -> None:
    """Collect illustration examples."""
    wizard_header("Illustrations")
    click.echo("Add examples to illustrate the statute's application.")
    click.echo("(Press Enter with empty label to finish)")
    click.echo("")
    
    label_counter = ord('a')
    
    while True:
        default_label = f"({chr(label_counter)})"
        label = prompt_input(f"Illustration label", default=default_label)
        
        if not label or label == default_label:
            # Check if user wants to add with default label
            if not label:
                break
        
        desc = prompt_input("  Illustration text", required=True)
        data.illustrations.append(IllustrationData(label=label, description=desc))
        click.echo(click.style(f"  ✓ Added illustration {label}", fg="green"))
        label_counter += 1
        
        if not prompt_confirm("Add another illustration?", default=False):
            break
    
    click.echo(f"\nTotal illustrations: {len(data.illustrations)}")


def collect_exceptions(data: StatuteData) -> None:
    """Collect exception / defence entries."""
    wizard_header("Exceptions / Defences")
    click.echo("Define exceptions or defences that negate liability.")
    click.echo("(Press Enter with empty label to finish)")
    click.echo("")

    while True:
        label = prompt_input("Exception label")
        if not label:
            break

        condition = prompt_input(f"  Condition for '{label}'", required=True)
        effect = prompt_input(f"  Effect (consequence when exception applies)")
        guard = prompt_input(f"  Guard expression (optional 'when' condition)")
        data.exceptions.append(ExceptionData(
            label=label,
            condition=condition,
            effect=effect,
            guard=guard,
        ))
        click.echo(click.style(f"  ✓ Added exception: {label}", fg="green"))

    click.echo(f"\nTotal exceptions: {len(data.exceptions)}")


def collect_caselaw(data: StatuteData) -> None:
    """Collect case law references."""
    wizard_header("Case Law References")
    click.echo("Add case law that interprets this statute.")
    click.echo("(Press Enter with empty name to finish)")
    click.echo("")

    while True:
        case_name = prompt_input("Case name")
        if not case_name:
            break

        citation = prompt_input(f"  Citation for '{case_name}'")
        holding = prompt_input(f"  Holding / ratio decidendi")
        element_ref = prompt_input(f"  Element this case interprets (optional)")
        data.case_law.append(CaseLawData(
            case_name=case_name,
            citation=citation,
            holding=holding,
            element_ref=element_ref,
        ))
        click.echo(click.style(f"  ✓ Added case: {case_name}", fg="green"))

    click.echo(f"\nTotal case law references: {len(data.case_law)}")


def _element_suffix(elem: ElementData) -> str:
    """Build optional caused_by/burden suffix for an element."""
    parts = []
    if elem.caused_by:
        parts.append(f" caused_by {elem.caused_by}")
    if elem.burden:
        parts.append(f" burden {elem.burden}")
    return "".join(parts)


def generate_yuho_code(data: StatuteData) -> str:
    """Generate Yuho source code from collected data."""
    lines: List[str] = []

    # Auto-generated struct (emitted before statute block)
    if data.auto_struct_name and data.auto_struct_fields:
        lines.append(f"struct {data.auto_struct_name} {{")
        for ftype, fname in data.auto_struct_fields:
            lines.append(f"    {ftype} {fname};")
        lines.append("}")
        lines.append("")

    # Statute header
    eff = f" effective {data.effective_date}" if data.effective_date else ""
    lines.append(f'statute {data.section_number} "{data.title}"{eff} {{')

    # Definitions
    if data.definitions:
        lines.append("")
        lines.append("    definitions {")
        for defn in data.definitions:
            escaped_def = defn.definition.replace('"', '\\"')
            lines.append(f'        {defn.term} := "{escaped_def}";')
        lines.append("    }")

    # Elements
    if data.elements:
        lines.append("")
        lines.append("    elements {")
        if data.element_grouping:
            lines.append(f"        {data.element_grouping} {{")
            for elem in data.elements:
                escaped_desc = elem.description.replace('"', '\\"')
                suffix = _element_suffix(elem)
                lines.append(f'            {elem.element_type} {elem.name} := "{escaped_desc}"{suffix};')
            lines.append("        }")
        else:
            for elem in data.elements:
                escaped_desc = elem.description.replace('"', '\\"')
                suffix = _element_suffix(elem)
                lines.append(f'        {elem.element_type} {elem.name} := "{escaped_desc}"{suffix};')
        lines.append("    }")

    # Penalty
    if data.penalty:
        lines.append("")
        lines.append("    penalty {")
        if data.penalty.has_imprisonment:
            if data.penalty.imprisonment_min:
                lines.append(f"        imprisonment := {data.penalty.imprisonment_min} to {data.penalty.imprisonment_max};")
            else:
                lines.append(f"        imprisonment := {data.penalty.imprisonment_max};")
        if data.penalty.has_fine:
            if data.penalty.fine_min:
                lines.append(f"        fine := {data.penalty.fine_min} to {data.penalty.fine_max};")
            else:
                lines.append(f"        fine := {data.penalty.fine_max};")
        if data.penalty.supplementary:
            escaped = data.penalty.supplementary.replace('"', '\\"')
            lines.append(f'        supplementary := "{escaped}";')
        lines.append("    }")

    # Illustrations
    if data.illustrations:
        lines.append("")
        lines.append("    illustrations {")
        for illus in data.illustrations:
            escaped = illus.description.replace('"', '\\"')
            lines.append(f'        {illus.label} "{escaped}";')
        lines.append("    }")

    # Exceptions
    for exc in data.exceptions:
        lines.append("")
        escaped_cond = exc.condition.replace('"', '\\"')
        lines.append(f"    exception {exc.label} {{")
        lines.append(f'        "{escaped_cond}"')
        if exc.effect:
            escaped_eff = exc.effect.replace('"', '\\"')
            lines.append(f'        "{escaped_eff}"')
        if exc.guard:
            lines.append(f"        when {exc.guard}")
        lines.append("    }")

    # Case law
    for cl in data.case_law:
        lines.append("")
        escaped_name = cl.case_name.replace('"', '\\"')
        cite_part = ""
        if cl.citation:
            escaped_cite = cl.citation.replace('"', '\\"')
            cite_part = f' "{escaped_cite}"'
        lines.append(f'    caselaw "{escaped_name}"{cite_part} {{')
        if cl.holding:
            escaped_hold = cl.holding.replace('"', '\\"')
            lines.append(f'        "{escaped_hold}"')
        if cl.element_ref:
            lines.append(f"        element {cl.element_ref}")
        lines.append("    }")

    lines.append("}")

    return "\n".join(lines)


def run_wizard(
    output: Optional[str] = None,
    section: Optional[str] = None,
    title: Optional[str] = None,
    verbose: bool = False,
    color: bool = True,
) -> None:
    """
    Run the interactive statute creation wizard.
    
    Args:
        output: Output file path (None = stdout)
        section: Pre-set section number
        title: Pre-set title
        verbose: Enable verbose output
        color: Use colored output
    """
    w = 59
    box_lines = [
        "╔" + "═" * w + "╗",
        "║" + "YUHO STATUTE CREATION WIZARD".center(w) + "║",
        "║" + " " * w + "║",
        "║" + "  This wizard will guide you through creating a new".ljust(w) + "║",
        "║" + "  Yuho statute definition step by step.".ljust(w) + "║",
        "╚" + "═" * w + "╝",
    ]
    click.echo(click.style("\n".join(box_lines), fg="cyan"))
    
    data = StatuteData()
    
    # Basic info
    wizard_header("Basic Information")
    
    data.section_number = section or prompt_input(
        "Section number (e.g., 299, 300A)",
        required=True
    )
    
    data.title = title or prompt_input(
        "Statute title (e.g., 'Culpable Homicide')",
        required=True
    )
    
    if prompt_confirm("Specify effective date?", default=False):
        data.effective_date = prompt_input("  Effective date (YYYY-MM-DD)", required=True)

    click.echo(click.style(f"\n✓ Creating statute: Section {data.section_number} - {data.title}", fg="green"))

    # Collect sections
    collect_definitions(data)
    collect_elements(data)
    collect_penalty(data)
    collect_illustrations(data)
    collect_exceptions(data)
    collect_caselaw(data)
    
    # Generate code
    wizard_header("Generated Code")
    code = generate_yuho_code(data)
    
    click.echo(click.style("```yuho", fg="yellow"))
    click.echo(code)
    click.echo(click.style("```", fg="yellow"))
    
    # Save or output
    if output:
        path = Path(output)
        if path.exists() and not prompt_confirm(f"\nOverwrite existing file {path}?", default=False):
            click.echo("Cancelled.")
            return
        
        path.write_text(code + "\n")
        click.echo(click.style(f"\n✓ Saved to {path}", fg="green"))
    else:
        if prompt_confirm("\nSave to file?", default=True):
            default_name = f"s{data.section_number.lower()}.yh"
            filename = prompt_input("Filename", default=default_name)
            path = Path(filename)
            path.write_text(code + "\n")
            click.echo(click.style(f"✓ Saved to {path}", fg="green"))
    
    click.echo(click.style("\n✓ Wizard complete!", fg="green", bold=True))
