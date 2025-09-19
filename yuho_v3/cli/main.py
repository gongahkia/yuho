#!/usr/bin/env python3
"""
Yuho v3.0 CLI - Main entry point for all Yuho tools
"""

import click
import sys
import os
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser import YuhoParser
from semantic_analyzer import SemanticAnalyzer
from transpilers.mermaid_transpiler import MermaidTranspiler
from transpilers.alloy_transpiler import AlloyTranspiler

@click.group()
@click.version_option(version='3.0.0')
def cli():
    """Yuho v3.0 - Legal Domain-Specific Language Tools"""
    pass

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed output')
def check(file_path, verbose):
    """Check Yuho file for syntax and semantic errors"""
    try:
        click.echo(f"{Fore.BLUE}Checking {file_path}...{Style.RESET_ALL}")

        # Parse the file
        parser = YuhoParser()
        ast = parser.parse_file(file_path)

        click.echo(f"{Fore.GREEN}✓ Syntax check passed{Style.RESET_ALL}")

        # Semantic analysis
        analyzer = SemanticAnalyzer()
        errors = analyzer.analyze(ast)

        if errors:
            click.echo(f"{Fore.RED}✗ Semantic errors found:{Style.RESET_ALL}")
            for error in errors:
                click.echo(f"  {Fore.RED}ERROR: {error}{Style.RESET_ALL}")
            sys.exit(1)
        else:
            click.echo(f"{Fore.GREEN}✓ Semantic check passed{Style.RESET_ALL}")
            click.echo(f"{Fore.GREEN}✓ {file_path} looks good! Have confidence your Yuho file is correct{Style.RESET_ALL}")

        if verbose:
            click.echo(f"{Fore.CYAN}AST Structure:{Style.RESET_ALL}")
            click.echo(f"  Statements: {len(ast.statements)}")

    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
@click.option('--format', '-f', type=click.Choice(['flowchart', 'mindmap']), default='flowchart', help='Diagram format')
def draw(file_path, output, format):
    """Generate Mermaid diagrams from Yuho file"""
    try:
        click.echo(f"{Fore.BLUE}Generating {format} from {file_path}...{Style.RESET_ALL}")

        # Parse the file
        parser = YuhoParser()
        ast = parser.parse_file(file_path)

        # Generate Mermaid
        transpiler = MermaidTranspiler()
        if format == 'flowchart':
            mermaid_code = transpiler.transpile_to_flowchart(ast)
        else:
            mermaid_code = transpiler.transpile_to_mindmap(ast)

        # Output
        if output:
            with open(output, 'w') as f:
                f.write(mermaid_code)
            click.echo(f"{Fore.GREEN}✓ Diagram saved to {output}{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.CYAN}Generated {format}:{Style.RESET_ALL}")
            click.echo(mermaid_code)

    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='Output file path')
def alloy(file_path, output):
    """Generate Alloy specification from Yuho file"""
    try:
        click.echo(f"{Fore.BLUE}Generating Alloy specification from {file_path}...{Style.RESET_ALL}")

        # Parse the file
        parser = YuhoParser()
        ast = parser.parse_file(file_path)

        # Generate Alloy
        transpiler = AlloyTranspiler()
        alloy_code = transpiler.transpile(ast)

        # Output
        if output:
            with open(output, 'w') as f:
                f.write(alloy_code)
            click.echo(f"{Fore.GREEN}✓ Alloy specification saved to {output}{Style.RESET_ALL}")
        else:
            click.echo(f"{Fore.CYAN}Generated Alloy specification:{Style.RESET_ALL}")
            click.echo(alloy_code)

    except Exception as e:
        click.echo(f"{Fore.RED}✗ Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

@cli.command()
@click.argument('struct_name')
@click.option('--output', '-o', help='Output file path')
def draft(struct_name, output):
    """Create a new Yuho file template with basic struct"""
    template = f"""// Yuho v3.0 - Generated template for {struct_name}

struct {struct_name} {{
    // Add your fields here
    // Example:
    // accused: string,
    // action: string,
    // victim: string,
    // consequence: ConsequenceType,
}}

// Add match-case logic here
// Example:
// match {{
//     case condition := consequence result;
//     case _ := consequence pass;
// }}
"""

    if output:
        with open(output, 'w') as f:
            f.write(template)
        click.echo(f"{Fore.GREEN}✓ Template saved to {output}{Style.RESET_ALL}")
    else:
        output_file = f"{struct_name.lower()}.yh"
        with open(output_file, 'w') as f:
            f.write(template)
        click.echo(f"{Fore.GREEN}✓ Template saved to {output_file}{Style.RESET_ALL}")

@cli.command()
def how():
    """Show help and usage examples"""
    help_text = f"""
{Fore.CYAN}Yuho v3.0 - Legal Domain-Specific Language{Style.RESET_ALL}

{Fore.YELLOW}Common Usage Examples:{Style.RESET_ALL}

1. Check a Yuho file for errors:
   {Fore.GREEN}yuho check example.yh{Style.RESET_ALL}

2. Generate a flowchart diagram:
   {Fore.GREEN}yuho draw example.yh --format flowchart -o diagram.mmd{Style.RESET_ALL}

3. Generate a mindmap:
   {Fore.GREEN}yuho draw example.yh --format mindmap{Style.RESET_ALL}

4. Generate Alloy specification:
   {Fore.GREEN}yuho alloy example.yh -o verification.als{Style.RESET_ALL}

5. Create a new template:
   {Fore.GREEN}yuho draft Cheating -o cheating.yh{Style.RESET_ALL}

{Fore.YELLOW}File Structure:{Style.RESET_ALL}
- Use .yh extension for Yuho files
- Start with struct definitions for legal concepts
- Add match-case blocks for conditional logic
- Use referencing/from for importing other modules

{Fore.YELLOW}Available Types:{Style.RESET_ALL}
- int, float, bool, string
- percent, money, date, duration
- Custom struct types

{Fore.YELLOW}For more information:{Style.RESET_ALL}
- See documentation in doc/ directory
- Check examples in example/ directory
"""
    click.echo(help_text)

if __name__ == '__main__':
    cli()