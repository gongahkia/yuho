"""
Init command - scaffold new Yuho project.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from yuho.cli.error_formatter import Colors, colorize


TEMPLATE_STATUTE = '''// {name} - Yuho statute definition
// Section: S{section}

statute {section} "{name}" {{
    definitions {{
        // Define key terms here
        // term := "definition";
    }}

    elements {{
        // Define the elements of the offense
        // actus_reus physical_act := "description";
        // mens_rea mental_state := "description";
    }}

    penalty {{
        // imprisonment := 0 years .. 1 year;
        // fine := $0 .. $10,000;
    }}

    illustration A {{
        "Example scenario illustrating the statute."
    }}
}}
'''

TEMPLATE_METADATA = '''# Metadata for {name}

[statute]
section_number = "{section}"
title = "{name}"
jurisdiction = "SG"  # Singapore

[contributor]
name = ""
email = ""

[version]
current = "1.0.0"
'''

TEMPLATE_TEST = '''// Tests for {name}
// Run with: yuho test {filename}

// Test case 1: Basic scenario
// TODO: Add test cases
'''


def run_init(name: Optional[str] = None, directory: Optional[str] = None, verbose: bool = False) -> None:
    """
    Initialize a new Yuho statute project.

    Args:
        name: Project name
        directory: Directory to create project in
        verbose: Enable verbose output
    """
    # Get project name
    if not name:
        name = click.prompt("Statute name", default="MyStatute")

    # Clean name for filenames
    safe_name = "".join(c if c.isalnum() else "_" for c in name)
    section = click.prompt("Section number", default="000")

    # Determine directory
    if directory:
        project_dir = Path(directory)
    else:
        project_dir = Path.cwd() / safe_name.lower()

    # Check if exists
    if project_dir.exists():
        if not click.confirm(f"Directory {project_dir} exists. Continue?"):
            sys.exit(0)
    else:
        project_dir.mkdir(parents=True)

    # Create files
    statute_file = project_dir / f"{safe_name.lower()}.yh"
    metadata_file = project_dir / "metadata.toml"
    test_dir = project_dir / "tests"
    test_file = test_dir / f"test_{safe_name.lower()}.yh"

    # Write statute template
    statute_content = TEMPLATE_STATUTE.format(name=name, section=section)
    statute_file.write_text(statute_content, encoding="utf-8")

    # Write metadata template
    metadata_content = TEMPLATE_METADATA.format(name=name, section=section)
    metadata_file.write_text(metadata_content, encoding="utf-8")

    # Write test template
    test_dir.mkdir(exist_ok=True)
    test_content = TEMPLATE_TEST.format(name=name, filename=statute_file.name)
    test_file.write_text(test_content, encoding="utf-8")

    click.echo(colorize(f"Created Yuho project: {project_dir}", Colors.CYAN + Colors.BOLD))
    click.echo(f"  {statute_file.name}")
    click.echo(f"  metadata.toml")
    click.echo(f"  tests/test_{safe_name.lower()}.yh")
    click.echo()
    click.echo("Next steps:")
    click.echo(f"  1. Edit {statute_file.name} to define your statute")
    click.echo(f"  2. Run 'yuho check {statute_file}' to validate")
    click.echo(f"  3. Run 'yuho transpile {statute_file} -t english' to see English version")
