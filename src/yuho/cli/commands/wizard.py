"""
TUI wizard for interactive statute creation.

Provides a step-by-step wizard interface for building Yuho statutes
using inquirer-style prompts. Generates valid .yh files from user input.
"""

import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

import click


@dataclass
class ElementData:
    """Data for a statute element."""
    element_type: str  # "actus_reus", "mens_rea", "circumstance"
    name: str
    description: str


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
    definitions: List[DefinitionData] = field(default_factory=list)
    elements: List[ElementData] = field(default_factory=list)
    penalty: Optional[PenaltyData] = None
    illustrations: List[IllustrationData] = field(default_factory=list)


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
            "circumstance"
        ])
        name = prompt_input("  Element name", required=True)
        desc = prompt_input("  Description", required=True)
        data.elements.append(ElementData(
            element_type=element_type,
            name=name,
            description=desc
        ))
        click.echo(click.style(f"  ✓ Added {element_type}: {name}", fg="green"))
    
    click.echo(f"\nTotal elements: {len(data.elements)}")


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


def generate_yuho_code(data: StatuteData) -> str:
    """Generate Yuho source code from collected data."""
    lines: List[str] = []
    
    # Statute header
    lines.append(f'statute "{data.section_number}" "{data.title}" {{')
    
    # Definitions
    if data.definitions:
        lines.append("")
        lines.append("    definitions {")
        for defn in data.definitions:
            escaped_def = defn.definition.replace('"', '\\"')
            lines.append(f'        "{defn.term}" := "{escaped_def}";')
        lines.append("    }")
    
    # Elements
    if data.elements:
        lines.append("")
        lines.append("    elements {")
        for elem in data.elements:
            escaped_desc = elem.description.replace('"', '\\"')
            lines.append(f'        {elem.element_type} {elem.name} := "{escaped_desc}";')
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
    click.echo(click.style("""
╔═══════════════════════════════════════════════════════════╗
║           YUHO STATUTE CREATION WIZARD                     ║
║                                                            ║
║  This wizard will guide you through creating a new         ║
║  Yuho statute definition step by step.                     ║
╚═══════════════════════════════════════════════════════════╝
    """, fg="cyan"))
    
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
    
    click.echo(click.style(f"\n✓ Creating statute: Section {data.section_number} - {data.title}", fg="green"))
    
    # Collect sections
    collect_definitions(data)
    collect_elements(data)
    collect_penalty(data)
    collect_illustrations(data)
    
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
