"""
Explain command - LLM-powered explanations of Yuho files.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from yuho.parser import Parser
from yuho.ast import ASTBuilder
from yuho.transpile import EnglishTranspiler
from yuho.cli.error_formatter import Colors, colorize


def run_explain(
    file: str,
    section: Optional[str] = None,
    interactive: bool = False,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    verbose: bool = False,
    stream: bool = True,
) -> None:
    """
    Generate natural language explanation of a Yuho file.

    Args:
        file: Path to the .yh file
        section: Specific section to explain
        interactive: Enable interactive REPL mode
        provider: LLM provider (ollama, huggingface, openai, anthropic)
        model: Model name
        verbose: Enable verbose output
        stream: Enable streaming output for real-time response
    """
    file_path = Path(file)

    # Parse and build AST
    parser = Parser()
    try:
        result = parser.parse_file(file_path)
    except FileNotFoundError:
        click.echo(colorize(f"error: File not found: {file}", Colors.RED), err=True)
        sys.exit(1)

    if result.errors:
        click.echo(colorize(f"error: Parse errors in {file}", Colors.RED), err=True)
        sys.exit(1)

    builder = ASTBuilder(result.source, str(file_path))
    ast = builder.build(result.root_node)

    # Filter to specific section if requested
    if section:
        matching = [s for s in ast.statutes if section in s.section_number]
        if not matching:
            click.echo(colorize(f"error: Section {section} not found", Colors.RED), err=True)
            sys.exit(1)

        # Create filtered module
        from yuho.ast.nodes import ModuleNode
        ast = ModuleNode(
            imports=ast.imports,
            type_defs=ast.type_defs,
            function_defs=ast.function_defs,
            statutes=tuple(matching),
            variables=ast.variables,
            source_location=ast.source_location,
        )

    # Generate base English explanation
    english = EnglishTranspiler()
    base_explanation = english.transpile(ast)

    if interactive:
        _run_interactive(base_explanation, ast, provider, model, stream)
    else:
        # Try to use LLM for enhanced explanation
        try:
            if stream:
                _enhance_with_llm_stream(base_explanation, provider, model, verbose)
            else:
                enhanced = _enhance_with_llm(base_explanation, provider, model, verbose)
                click.echo(enhanced)
        except Exception as e:
            if verbose:
                click.echo(colorize(f"LLM unavailable: {e}", Colors.YELLOW), err=True)
            # Fall back to basic English transpilation
            click.echo(base_explanation)


def _enhance_with_llm(text: str, provider: Optional[str], model: Optional[str], verbose: bool) -> str:
    """Use LLM to enhance the explanation."""
    try:
        from yuho.llm import get_provider, LLMConfig
    except ImportError:
        return text  # LLM module not available

    try:
        # Build config
        config = LLMConfig(
            provider=provider or "ollama",
            model_name=model or "llama3",
        )
        llm = get_provider(config)

        prompt = f"""You are a legal expert explaining statute provisions to a general audience.
Given the following structured explanation of a legal statute, rewrite it in clear,
accessible language that a non-lawyer could understand. Keep the legal accuracy but
make it readable.

Structured explanation:
{text}

Clear explanation:"""

        return llm.generate(prompt, max_tokens=2000)

    except Exception as e:
        if verbose:
            click.echo(colorize(f"LLM error: {e}", Colors.YELLOW), err=True)
        return text


def _enhance_with_llm_stream(text: str, provider: Optional[str], model: Optional[str], verbose: bool) -> None:
    """Use LLM to enhance the explanation with streaming output."""
    try:
        from yuho.llm import get_provider, LLMConfig
    except ImportError:
        click.echo(text)  # LLM module not available
        return

    try:
        # Build config
        config = LLMConfig(
            provider=provider or "ollama",
            model_name=model or "llama3",
        )
        llm = get_provider(config)

        prompt = f"""You are a legal expert explaining statute provisions to a general audience.
Given the following structured explanation of a legal statute, rewrite it in clear,
accessible language that a non-lawyer could understand. Keep the legal accuracy but
make it readable.

Structured explanation:
{text}

Clear explanation:"""

        # Check if provider supports streaming
        if hasattr(llm, 'stream'):
            # Stream tokens to stdout
            for token in llm.stream(prompt, max_tokens=2000):
                click.echo(token, nl=False)
                sys.stdout.flush()
            click.echo()  # Final newline
        else:
            # Fall back to non-streaming
            response = llm.generate(prompt, max_tokens=2000)
            click.echo(response)

    except Exception as e:
        if verbose:
            click.echo(colorize(f"LLM streaming error: {e}", Colors.YELLOW), err=True)
        # Fall back to basic explanation
        click.echo(text)


def _run_interactive(
    base_explanation: str,
    ast,
    provider: Optional[str],
    model: Optional[str],
    stream: bool = True,
) -> None:
    """Run interactive REPL for follow-up questions."""
    click.echo(colorize("Yuho Explain - Interactive Mode", Colors.CYAN + Colors.BOLD))
    click.echo(colorize("Type 'quit' or 'exit' to leave. Type 'show' to see the statute.\n", Colors.DIM))

    # Show initial explanation
    click.echo(base_explanation)
    click.echo()

    try:
        from yuho.llm import get_provider, LLMConfig
        config = LLMConfig(provider=provider or "ollama", model_name=model or "llama3")
        llm = get_provider(config)
        has_llm = True
        can_stream = stream and hasattr(llm, 'stream')
    except Exception:
        has_llm = False
        can_stream = False
        click.echo(colorize("(LLM not available - limited to basic queries)", Colors.YELLOW))

    context = base_explanation

    while True:
        try:
            query = click.prompt(colorize("?", Colors.CYAN), default="", show_default=False)
        except (EOFError, KeyboardInterrupt):
            click.echo("\nGoodbye!")
            break

        query = query.strip()
        if not query:
            continue

        if query.lower() in ("quit", "exit", "q"):
            click.echo("Goodbye!")
            break

        if query.lower() == "show":
            click.echo(base_explanation)
            continue

        if has_llm:
            prompt = f"""Context about the statute:
{context}

User question: {query}

Provide a helpful, accurate answer:"""

            try:
                if can_stream:
                    click.echo()  # Start on new line
                    for token in llm.stream(prompt, max_tokens=1000):
                        click.echo(token, nl=False)
                        sys.stdout.flush()
                    click.echo("\n")  # End with newlines
                else:
                    response = llm.generate(prompt, max_tokens=1000)
                    click.echo(f"\n{response}\n")
            except Exception as e:
                click.echo(colorize(f"Error: {e}", Colors.RED))
        else:
            click.echo(colorize("Cannot answer - LLM not available", Colors.YELLOW))
