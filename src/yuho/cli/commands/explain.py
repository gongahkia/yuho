"""
Explain command - LLM-powered explanations of Yuho files.
"""

import sys
from pathlib import Path
from typing import Optional

import click

from yuho.transpile import EnglishTranspiler
from yuho.cli.error_formatter import Colors, colorize
from yuho.services.analysis import analyze_file


def run_explain(
    file: str,
    section: Optional[str] = None,
    interactive: bool = False,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    offline: bool = False,
    no_llm: bool = False,
    verbose: bool = False,
    stream: bool = True,
) -> None:
    """
    Generate natural language explanation of a Yuho file.

    Args:
        file: Path to the .yh file
        section: Specific section to explain
        interactive: Enable interactive REPL mode
        provider: LLM provider (ollama, huggingface, openai, anthropic, gemini, plex, keymeet)
        model: Model name
        api_key: API key for cloud providers (overrides config)
        offline: Disallow cloud providers
        no_llm: Skip LLM, use built-in English transpilation only
        verbose: Enable verbose output
        stream: Enable streaming output for real-time response
    """
    from yuho.config.loader import get_config
    from yuho.parser.wrapper import validate_file_path
    try:
        validate_file_path(file)
    except (ValueError, FileNotFoundError) as e:
        click.echo(f"error: {e}", err=True)
        sys.exit(1)

    llm_config = get_config().llm
    resolved_provider = provider or llm_config.provider
    resolved_model = model or llm_config.model
    resolved_api_key = api_key # cli --api-key takes highest priority
    if not resolved_api_key:
        _key_map = {
            "openai": llm_config.openai_api_key,
            "anthropic": llm_config.anthropic_api_key,
            "gemini": getattr(llm_config, "gemini_api_key", None),
            "plex": getattr(llm_config, "plex_api_key", None),
            "keymeet": getattr(llm_config, "keymeet_api_key", None),
        }
        resolved_api_key = _key_map.get(resolved_provider)

    CLOUD_PROVIDERS = {"openai", "anthropic", "gemini", "plex", "keymeet"}
    if offline and resolved_provider in CLOUD_PROVIDERS:
        click.echo(
            colorize("error: --offline mode does not allow cloud providers", Colors.RED),
            err=True,
        )
        sys.exit(1)

    file_path = Path(file)

    # Parse + AST via shared analysis service
    analysis = analyze_file(file_path, run_semantic=False)

    if analysis.parse_errors:
        click.echo(colorize(f"error: Parse errors in {file}", Colors.RED), err=True)
        sys.exit(1)

    if analysis.errors and not analysis.parse_errors:
        click.echo(colorize(f"error: {analysis.errors[0].message}", Colors.RED), err=True)
        sys.exit(1)

    ast = analysis.ast
    if ast is None:
        click.echo(colorize("error: Failed to build AST", Colors.RED), err=True)
        sys.exit(1)

    # Filter to specific section if requested
    sub_section_filter = None
    sub_sections = {"elements", "definitions", "penalty", "illustrations", "exceptions", "caselaw"}
    if section:
        if section.lower() in sub_sections:
            sub_section_filter = section.lower()
        else:
            matching = [s for s in ast.statutes if section in s.section_number]
            if not matching:
                click.echo(colorize(f"error: Section {section} not found", Colors.RED), err=True)
                sys.exit(1)
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

    # Extract sub-section if requested
    if sub_section_filter:
        lines = base_explanation.split("\n")
        filtered_lines = []
        capturing = False
        for line in lines:
            line_lower = line.strip().lower()
            if sub_section_filter in line_lower and (":" in line or line_lower.startswith(sub_section_filter)):
                capturing = True
            elif capturing and line.strip() and not line.startswith(" ") and not line.startswith("\t"):
                if any(k in line_lower for k in sub_sections if k != sub_section_filter):
                    capturing = False
            if capturing:
                filtered_lines.append(line)
        if filtered_lines:
            base_explanation = "\n".join(filtered_lines)

    if no_llm:
        click.echo(base_explanation)
        return

    if interactive:
        _run_interactive(base_explanation, ast, resolved_provider, resolved_model, stream, resolved_api_key)
    else:
        # Try to use LLM for enhanced explanation
        try:
            if stream:
                _enhance_with_llm_stream(
                    base_explanation,
                    resolved_provider,
                    resolved_model,
                    verbose,
                    api_key=resolved_api_key,
                )
            else:
                enhanced = _enhance_with_llm(
                    base_explanation,
                    resolved_provider,
                    resolved_model,
                    verbose,
                    api_key=resolved_api_key,
                )
                click.echo(enhanced)
        except Exception as e:
            if verbose:
                click.echo(colorize(f"LLM unavailable: {e}", Colors.YELLOW), err=True)
            else:
                click.echo(
                    colorize(
                        "LLM not configured. Showing basic English transpilation.\n"
                        "For enhanced AI explanations, see: yuho config --help\n"
                        "  or pass --provider <name> --api-key <key> directly.\n",
                        Colors.YELLOW,
                    ),
                    err=True,
                )
            # Fall back to basic English transpilation
            click.echo(base_explanation)


def _enhance_with_llm(text: str, provider: Optional[str], model: Optional[str], verbose: bool, api_key: Optional[str] = None) -> str:
    """Use LLM to enhance the explanation."""
    try:
        from yuho.llm import get_provider, LLMConfig
    except ImportError:
        return text  # LLM module not available

    try:
        config = LLMConfig(
            provider=provider or "ollama",
            model_name=model or "llama3",
            api_key=api_key,
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


def _enhance_with_llm_stream(text: str, provider: Optional[str], model: Optional[str], verbose: bool, api_key: Optional[str] = None) -> None:
    """Use LLM to enhance the explanation with streaming output."""
    try:
        from yuho.llm import get_provider, LLMConfig
    except ImportError:
        click.echo(text)  # LLM module not available
        return

    try:
        config = LLMConfig(
            provider=provider or "ollama",
            model_name=model or "llama3",
            api_key=api_key,
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
    api_key: Optional[str] = None,
) -> None:
    """Run interactive REPL for follow-up questions."""
    click.echo(colorize("Yuho Explain - Interactive Mode", Colors.CYAN + Colors.BOLD))
    click.echo(colorize("Type 'quit' or 'exit' to leave. Type 'show' to see the statute.\n", Colors.DIM))

    # Show initial explanation
    click.echo(base_explanation)
    click.echo()

    try:
        from yuho.llm import get_provider, LLMConfig
        config = LLMConfig(provider=provider or "ollama", model_name=model or "llama3", api_key=api_key)
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
