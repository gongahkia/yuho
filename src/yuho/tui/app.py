"""Yuho TUI Application - Terminal User Interface powered by Textual."""

from __future__ import annotations
import io
import os
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from typing import Optional, Tuple

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Static, Button, Input, TextArea,
    Select, Label, RichLog, OptionList,
    ContentSwitcher, Rule,
)
from textual import on, work

from yuho import __version__
from yuho.tui.ascii_art import YUHO_MASCOT, YUHO_LOGO_SMALL

TRANSPILE_TARGETS = [
    ("JSON", "json"),
    ("JSON-LD", "jsonld"),
    ("English", "english"),
    ("LaTeX", "latex"),
    ("Mermaid", "mermaid"),
    ("Alloy", "alloy"),
    ("GraphQL", "graphql"),
    ("Blocks", "blocks"),
]
NAV_ITEMS = [
    "  Home",
    "  Check",
    "  Transpile",
    "  Wizard",
    "  REPL",
    "  Lint",
    "  Test",
    "  Settings",
    "  About",
]
NAV_IDS = ["home", "check", "transpile", "wizard", "repl", "lint", "test", "settings", "about"]


def capture_cli(func, *args, **kwargs) -> Tuple[str, str]:
    """Run a function capturing stdout/stderr."""
    out, err = io.StringIO(), io.StringIO()
    try:
        with redirect_stdout(out), redirect_stderr(err):
            func(*args, **kwargs)
    except SystemExit:
        pass
    except Exception as e:
        err.write(str(e))
    return out.getvalue(), err.getvalue()


# ─── Panels ─────────────────────────────────────────────────────────────────


class HomePanel(ScrollableContainer):
    """Home dashboard with mascot and quick actions."""
    def compose(self) -> ComposeResult:
        yield Static(YUHO_MASCOT, id="mascot")
        yield Static(
            f"[bold]Welcome to Yuho[/bold] [dim]v{__version__}[/dim]\n\n"
            "[dim]A domain-specific language for encoding legal statutes.[/dim]\n"
            "[dim]Encode Singapore Penal Code sections as machine-readable models.[/dim]\n",
            id="welcome-text",
        )
        yield Rule()
        yield Static(
            "[bold]Quick Start[/bold]\n\n"
            "  [bold magenta]1[/] Check     — Parse and validate a .yh file\n"
            "  [bold magenta]2[/] Transpile — Convert to JSON, English, Mermaid, LaTeX...\n"
            "  [bold magenta]3[/] Wizard    — Create a statute step-by-step\n"
            "  [bold magenta]4[/] REPL      — Interactive experimentation\n"
            "  [bold magenta]5[/] Lint      — Style and best practice checks\n"
            "  [bold magenta]6[/] Test      — Run .yh test files\n"
            "  [bold magenta]7[/] Settings  — Configure Yuho\n"
            "  [bold magenta]8[/] About     — Version, links, attribution\n",
        )
        yield Rule()
        yield Static(
            "[dim]Use the sidebar or press [bold]1-9[/bold] to navigate. "
            "Press [bold]q[/bold] to quit. Press [bold]F1[/bold] for help.[/dim]"
        )
        with Horizontal(classes="quick-actions"):
            yield Button("Open File", id="btn-open", variant="primary")
            yield Button("New Statute", id="btn-wizard", variant="default")


class CheckPanel(Container):
    """Parse and validate .yh files."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Check[/bold magenta] — Parse and validate a Yuho file\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="check-path")
            yield Button("Check", id="btn-check", variant="primary")
        yield RichLog(id="check-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-check")
    def handle_check(self) -> None:
        path_input = self.query_one("#check-path", Input)
        output = self.query_one("#check-output", RichLog)
        output.clear()
        file_path = path_input.value.strip()
        if not file_path:
            output.write("[bold red]Error:[/] Please enter a file path.")
            return
        path = Path(file_path).expanduser()
        if not path.exists():
            output.write(f"[bold red]Error:[/] File not found: {path}")
            return
        if not path.is_file():
            output.write(f"[bold red]Error:[/] Not a file: {path}")
            return
        self._run_check(str(path))

    @on(Input.Submitted, "#check-path")
    def handle_check_enter(self) -> None:
        self.handle_check()

    @work(thread=True)
    def _run_check(self, file_path: str) -> None:
        output = self.query_one("#check-output", RichLog)
        try:
            from yuho.parser.wrapper import get_parser
            parser = get_parser()
            result = parser.parse_file(file_path)
            if result.is_valid:
                self.app.call_from_thread(output.write, f"[bold green]OK:[/] {file_path}")
                self.app.call_from_thread(output.write, "")
                try:
                    from yuho.ast.builder import ASTBuilder
                    builder = ASTBuilder(result.source, file=file_path)
                    ast = builder.build(result.root_node)
                    self.app.call_from_thread(
                        output.write,
                        f"  Imports:    {len(ast.imports)}\n"
                        f"  Structs:    {len(ast.type_defs)}\n"
                        f"  Functions:  {len(ast.function_defs)}\n"
                        f"  Statutes:   {len(ast.statutes)}\n"
                        f"  Variables:  {len(ast.variables)}"
                    )
                except Exception as e:
                    self.app.call_from_thread(output.write, f"[yellow]AST warning:[/] {e}")
            else:
                self.app.call_from_thread(
                    output.write,
                    f"[bold red]Found {len(result.errors)} error(s) in {file_path}:[/]"
                )
                for err in result.errors:
                    self.app.call_from_thread(
                        output.write,
                        f"  [red]error[/] line {err.location.line}, col {err.location.col}: {err.message}"
                    )
                    lines = result.source.splitlines()
                    if 1 <= err.location.line <= len(lines):
                        line = lines[err.location.line - 1]
                        self.app.call_from_thread(output.write, f"    [dim]{err.location.line:>4}[/] | {line}")
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


class TranspilePanel(Container):
    """Transpile .yh files to various formats."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Transpile[/bold magenta] — Convert to another format\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="transpile-path")
            yield Select(options=TRANSPILE_TARGETS, value="json", id="transpile-target")
            yield Button("Transpile", id="btn-transpile", variant="primary")
        with Horizontal(classes="split-view"):
            yield TextArea(id="transpile-source", read_only=True)
            yield TextArea(id="transpile-output", read_only=True)
        with Horizontal(classes="action-row"):
            yield Button("Copy Output", id="btn-copy-output")
            yield Button("Save Output", id="btn-save-output")

    @on(Button.Pressed, "#btn-transpile")
    def handle_transpile(self) -> None:
        path_input = self.query_one("#transpile-path", Input)
        file_path = path_input.value.strip()
        if not file_path:
            self.query_one("#transpile-output", TextArea).load_text("Error: enter a file path.")
            return
        path = Path(file_path).expanduser()
        if not path.exists():
            self.query_one("#transpile-output", TextArea).load_text(f"Error: not found: {path}")
            return
        target_select = self.query_one("#transpile-target", Select)
        target = str(target_select.value) if target_select.value != Select.BLANK else "json"
        try:
            self.query_one("#transpile-source", TextArea).load_text(path.read_text(encoding="utf-8"))
        except Exception as e:
            self.query_one("#transpile-output", TextArea).load_text(f"Error reading file: {e}")
            return
        self._run_transpile(str(path), target)

    @on(Input.Submitted, "#transpile-path")
    def handle_transpile_enter(self) -> None:
        self.handle_transpile()

    @work(thread=True)
    def _run_transpile(self, file_path: str, target: str) -> None:
        output_area = self.query_one("#transpile-output", TextArea)
        try:
            from yuho.cli.commands.transpile import run_transpile
            stdout, stderr = capture_cli(run_transpile, file_path, target=target, verbose=False)
            result = stdout.strip() or stderr.strip() or "(no output)"
            self.app.call_from_thread(output_area.load_text, result)
        except Exception as e:
            self.app.call_from_thread(output_area.load_text, f"Error: {e}")


class WizardPanel(ScrollableContainer):
    """Interactive statute creation wizard."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Wizard[/bold magenta] — Create a statute step-by-step\n")
        yield Static("[bold]Step 1: Basic Info[/bold]")
        with Horizontal(classes="input-row"):
            yield Label("Section:", classes="form-label")
            yield Input(placeholder="e.g. 415", id="wiz-section")
        with Horizontal(classes="input-row"):
            yield Label("Title:", classes="form-label")
            yield Input(placeholder="e.g. Cheating", id="wiz-title")
        yield Rule()
        yield Static('[bold]Step 2: Definitions[/bold] [dim](one per line: name := "description")[/dim]')
        yield TextArea(id="wiz-definitions")
        yield Rule()
        yield Static("[bold]Step 3: Elements[/bold] [dim](one per line: type name := \"desc\")[/dim]")
        yield Static("[dim]  Types: actus_reus, mens_rea, circumstance[/dim]")
        yield TextArea(id="wiz-elements")
        yield Rule()
        yield Static("[bold]Step 4: Penalty[/bold]")
        with Horizontal(classes="input-row"):
            yield Label("Imprisonment:", classes="form-label")
            yield Input(placeholder="e.g. 1 year .. 7 years", id="wiz-imprisonment")
        with Horizontal(classes="input-row"):
            yield Label("Fine:", classes="form-label")
            yield Input(placeholder="e.g. $0.00 .. $50,000.00", id="wiz-fine")
        yield Rule()
        yield Static("[bold]Step 5: Illustrations[/bold] [dim](one per line)[/dim]")
        yield TextArea(id="wiz-illustrations")
        yield Rule()
        with Horizontal(classes="action-row"):
            yield Button("Generate", id="btn-wiz-generate", variant="primary")
            yield Button("Copy", id="btn-wiz-copy")
            yield Button("Save As...", id="btn-wiz-save")
        yield Static("[bold]Generated Output:[/bold]")
        yield TextArea(id="wiz-output", read_only=True)

    @on(Button.Pressed, "#btn-wiz-generate")
    def handle_generate(self) -> None:
        section = self.query_one("#wiz-section", Input).value.strip()
        title = self.query_one("#wiz-title", Input).value.strip()
        definitions = self.query_one("#wiz-definitions", TextArea).text.strip()
        elements = self.query_one("#wiz-elements", TextArea).text.strip()
        imprisonment = self.query_one("#wiz-imprisonment", Input).value.strip()
        fine = self.query_one("#wiz-fine", Input).value.strip()
        illustrations = self.query_one("#wiz-illustrations", TextArea).text.strip()
        output_area = self.query_one("#wiz-output", TextArea)
        if not section or not title:
            output_area.load_text("Error: Section and Title are required.")
            return
        lines = [f'statute {section} "{title}" {{']
        if definitions:
            lines.append("    definitions {")
            for d in definitions.splitlines():
                d = d.strip()
                if d:
                    lines.append(f"        {d};") if ":=" in d else lines.append(f'        {d} := "TODO";')
            lines.append("    }")
            lines.append("")
        if elements:
            lines.append("    elements {")
            for e in elements.splitlines():
                e = e.strip()
                if e:
                    lines.append(f"        {e};")
            lines.append("    }")
            lines.append("")
        if imprisonment or fine:
            lines.append("    penalty {")
            if imprisonment:
                lines.append(f"        imprisonment := {imprisonment};")
            if fine:
                lines.append(f"        fine := {fine};")
            lines.append("    }")
            lines.append("")
        if illustrations:
            for i, ill in enumerate(illustrations.splitlines(), 1):
                ill = ill.strip()
                if ill:
                    lines.append(f"    illustration example{i} {{")
                    lines.append(f'        "{ill}"')
                    lines.append("    }")
                    lines.append("")
        lines.append("}")
        output_area.load_text("\n".join(lines))


class ReplPanel(Container):
    """Interactive REPL for Yuho experimentation."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]REPL[/bold magenta] — Interactive Yuho experimentation\n")
        yield Static("[dim]Commands: help, load <file>, transpile <target>, ast, check, targets, clear, exit[/dim]\n")
        yield RichLog(id="repl-output", highlight=True, markup=True)
        with Horizontal(classes="input-row"):
            yield Static("[bold magenta]yuho>[/bold magenta] ", classes="repl-prompt")
            yield Input(placeholder="Enter Yuho code or command...", id="repl-input")
            yield Button("Run", id="btn-repl-run", variant="primary")

    def on_mount(self) -> None:
        output = self.query_one("#repl-output", RichLog)
        output.write(f"[bold]Yuho REPL v{__version__}[/bold]")
        output.write("[dim]Type 'help' for available commands.[/dim]\n")
        self._source_buffer = ""
        self._repl_file: Optional[str] = None

    @on(Input.Submitted, "#repl-input")
    def handle_repl_submit(self) -> None:
        self._process_repl_command()

    @on(Button.Pressed, "#btn-repl-run")
    def handle_repl_run(self) -> None:
        self._process_repl_command()

    def _process_repl_command(self) -> None:
        inp = self.query_one("#repl-input", Input)
        output = self.query_one("#repl-output", RichLog)
        cmd = inp.value.strip()
        inp.value = ""
        if not cmd:
            return
        output.write(f"[bold magenta]yuho>[/bold magenta] {cmd}")
        if cmd == "help":
            output.write(
                "  [bold]help[/]          — Show this help\n"
                "  [bold]load <file>[/]   — Load a .yh file into the buffer\n"
                "  [bold]transpile <t>[/] — Transpile buffer (json, english, mermaid...)\n"
                "  [bold]ast[/]           — Show AST of buffer\n"
                "  [bold]check[/]         — Check buffer for errors\n"
                "  [bold]targets[/]       — List transpile targets\n"
                "  [bold]buffer[/]        — Show current buffer\n"
                "  [bold]clear[/]         — Clear output\n"
                "  [bold]reset[/]         — Clear buffer\n"
                "  [bold]exit[/]          — Exit REPL"
            )
        elif cmd == "clear":
            output.clear()
        elif cmd == "reset":
            self._source_buffer = ""
            self._repl_file = None
            output.write("[dim](buffer cleared)[/dim]")
        elif cmd == "exit":
            self.app.exit()
        elif cmd == "targets":
            output.write("  " + ", ".join(t[1] for t in TRANSPILE_TARGETS))
        elif cmd == "buffer":
            if self._source_buffer:
                output.write(f"[dim]{self._source_buffer}[/dim]")
            else:
                output.write("[dim](empty buffer)[/dim]")
        elif cmd.startswith("load "):
            file_path = cmd[5:].strip()
            try:
                path = Path(file_path).expanduser()
                self._source_buffer = path.read_text(encoding="utf-8")
                self._repl_file = str(path)
                output.write(f"[green]Loaded {path} ({len(self._source_buffer)} chars)[/green]")
            except Exception as e:
                output.write(f"[red]Error: {e}[/red]")
        elif cmd == "check":
            if not self._source_buffer:
                output.write("[yellow]Buffer is empty. Load a file first.[/yellow]")
                return
            self._repl_check()
        elif cmd.startswith("transpile"):
            parts = cmd.split()
            target = parts[1] if len(parts) > 1 else "json"
            if not self._source_buffer:
                output.write("[yellow]Buffer is empty. Load a file first.[/yellow]")
                return
            self._repl_transpile(target)
        elif cmd == "ast":
            if not self._source_buffer:
                output.write("[yellow]Buffer is empty. Load a file first.[/yellow]")
                return
            self._repl_ast()
        else:
            self._source_buffer += cmd + "\n"
            output.write("[dim](added to buffer)[/dim]")

    @work(thread=True)
    def _repl_check(self) -> None:
        output = self.query_one("#repl-output", RichLog)
        try:
            from yuho.parser.wrapper import get_parser
            parser = get_parser()
            result = parser.parse(self._source_buffer, file=self._repl_file or "<repl>")
            if result.is_valid:
                self.app.call_from_thread(output.write, "[green]Valid[/green]")
            else:
                for err in result.errors:
                    self.app.call_from_thread(output.write, f"  [red]error[/] line {err.location.line}: {err.message}")
        except Exception as e:
            self.app.call_from_thread(output.write, f"[red]Error: {e}[/red]")

    @work(thread=True)
    def _repl_transpile(self, target: str) -> None:
        output = self.query_one("#repl-output", RichLog)
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".yh", mode="w", delete=False, encoding="utf-8") as f:
                f.write(self._source_buffer)
                tmp_path = f.name
            try:
                from yuho.cli.commands.transpile import run_transpile
                stdout, stderr = capture_cli(run_transpile, tmp_path, target=target, verbose=False)
                result = stdout.strip() or stderr.strip() or "(no output)"
                self.app.call_from_thread(output.write, result)
            finally:
                os.unlink(tmp_path)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[red]Error: {e}[/red]")

    @work(thread=True)
    def _repl_ast(self) -> None:
        output = self.query_one("#repl-output", RichLog)
        try:
            from yuho.parser.wrapper import get_parser
            from yuho.ast.builder import ASTBuilder
            parser = get_parser()
            result = parser.parse(self._source_buffer, file=self._repl_file or "<repl>")
            if not result.is_valid:
                for err in result.errors:
                    self.app.call_from_thread(output.write, f"[red]{err}[/red]")
                return
            builder = ASTBuilder(result.source, file=self._repl_file or "<repl>")
            ast = builder.build(result.root_node)
            self.app.call_from_thread(
                output.write,
                f"  Imports:   {len(ast.imports)}\n"
                f"  Structs:   {len(ast.type_defs)}\n"
                f"  Functions: {len(ast.function_defs)}\n"
                f"  Statutes:  {len(ast.statutes)}\n"
                f"  Variables: {len(ast.variables)}"
            )
        except Exception as e:
            self.app.call_from_thread(output.write, f"[red]Error: {e}[/red]")


class LintPanel(Container):
    """Lint .yh files for style issues."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Lint[/bold magenta] — Check for style and best practices\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="lint-path")
            yield Button("Lint", id="btn-lint", variant="primary")
            yield Button("Auto-fix", id="btn-lint-fix", variant="warning")
        yield RichLog(id="lint-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-lint")
    def handle_lint(self) -> None:
        self._do_lint(fix=False)

    @on(Button.Pressed, "#btn-lint-fix")
    def handle_lint_fix(self) -> None:
        self._do_lint(fix=True)

    @on(Input.Submitted, "#lint-path")
    def handle_lint_enter(self) -> None:
        self._do_lint(fix=False)

    def _do_lint(self, fix: bool) -> None:
        output = self.query_one("#lint-output", RichLog)
        output.clear()
        file_path = self.query_one("#lint-path", Input).value.strip()
        if not file_path:
            output.write("[bold red]Error:[/] Please enter a file path.")
            return
        self._run_lint(file_path, fix)

    @work(thread=True)
    def _run_lint(self, file_path: str, fix: bool) -> None:
        output = self.query_one("#lint-output", RichLog)
        try:
            from yuho.cli.commands.lint import run_lint
            stdout, stderr = capture_cli(run_lint, [file_path], verbose=False, color=False, fix=fix)
            result = stdout.strip() or stderr.strip() or "[green]No issues found.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


class TestPanel(Container):
    """Run .yh test files."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Test[/bold magenta] — Run Yuho test files\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to test file or directory...", id="test-path")
            yield Button("Run Tests", id="btn-test", variant="primary")
            yield Button("Run All", id="btn-test-all")
        yield RichLog(id="test-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-test")
    def handle_test(self) -> None:
        output = self.query_one("#test-output", RichLog)
        output.clear()
        file_path = self.query_one("#test-path", Input).value.strip()
        if not file_path:
            output.write("[bold red]Error:[/] Please enter a file path.")
            return
        self._run_test(file_path, False)

    @on(Button.Pressed, "#btn-test-all")
    def handle_test_all(self) -> None:
        self.query_one("#test-output", RichLog).clear()
        self._run_test(None, True)

    @on(Input.Submitted, "#test-path")
    def handle_test_enter(self) -> None:
        self.handle_test()

    @work(thread=True)
    def _run_test(self, file_path: Optional[str], run_all: bool) -> None:
        output = self.query_one("#test-output", RichLog)
        try:
            from yuho.cli.commands.test import run_test
            stdout, stderr = capture_cli(run_test, file_path, run_all=run_all, verbose=False)
            result = stdout.strip() or stderr.strip() or "[green]All tests passed.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


class SettingsPanel(ScrollableContainer):
    """Configuration management."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Settings[/bold magenta] — Configure Yuho\n")
        yield Static("[bold]LLM Provider[/bold]")
        yield Select(
            options=[
                ("Ollama (local)", "ollama"),
                ("HuggingFace", "huggingface"),
                ("OpenAI", "openai"),
                ("Anthropic", "anthropic"),
            ],
            value="ollama",
            id="settings-llm-provider",
        )
        yield Static("")
        yield Static("[bold]LLM Model[/bold]")
        yield Input(placeholder="e.g. llama3, gpt-4, claude-3", id="settings-llm-model", value="llama3")
        yield Static("")
        yield Static("[bold]Default Transpile Target[/bold]")
        yield Select(options=TRANSPILE_TARGETS, value="json", id="settings-default-target")
        yield Static("")
        yield Static("[bold]Offline Mode[/bold]")
        yield Select(options=[("Enabled", "true"), ("Disabled", "false")], value="false", id="settings-offline")
        yield Rule()
        with Horizontal(classes="action-row"):
            yield Button("Save Settings", id="btn-settings-save", variant="primary")
            yield Button("Reset Defaults", id="btn-settings-reset")
        yield Static("", id="settings-status")

    @on(Button.Pressed, "#btn-settings-save")
    def handle_save(self) -> None:
        status = self.query_one("#settings-status", Static)
        try:
            from yuho.cli.commands.config import run_config_set
            provider = self.query_one("#settings-llm-provider", Select).value
            model = self.query_one("#settings-llm-model", Input).value.strip()
            target = self.query_one("#settings-default-target", Select).value
            if provider and provider != Select.BLANK:
                capture_cli(run_config_set, "llm.provider", str(provider), verbose=False)
            if model:
                capture_cli(run_config_set, "llm.model", model, verbose=False)
            if target and target != Select.BLANK:
                capture_cli(run_config_set, "transpile.default_target", str(target), verbose=False)
            status.update("[green]Settings saved.[/green]")
        except Exception as e:
            status.update(f"[red]Error: {e}[/red]")

    @on(Button.Pressed, "#btn-settings-reset")
    def handle_reset(self) -> None:
        self.query_one("#settings-llm-provider", Select).value = "ollama"
        self.query_one("#settings-llm-model", Input).value = "llama3"
        self.query_one("#settings-default-target", Select).value = "json"
        self.query_one("#settings-offline", Select).value = "false"
        self.query_one("#settings-status", Static).update("[dim]Defaults restored.[/dim]")


class AboutPanel(ScrollableContainer):
    """About, attribution, and links."""
    def compose(self) -> ComposeResult:
        yield Static(YUHO_MASCOT, id="about-mascot")
        yield Rule()
        yield Static(
            f"[bold magenta]Yuho[/bold magenta] [dim]v{__version__}[/dim]\n"
            "[bold]A domain-specific language for encoding legal statutes[/bold]\n"
        )
        yield Static(
            "[bold]Project Info[/bold]\n"
            f"  Version:    {__version__}\n"
            "  License:    MIT\n"
            "  Author:     gongahkia\n"
            "  Language:   Python 3.10+\n"
            "  Parser:     Tree-sitter\n"
        )
        yield Static(
            "[bold]Links[/bold]\n"
            "  Repository:     github.com/gongahkia/yuho\n"
            "  Documentation:  github.com/gongahkia/yuho/tree/main/doc\n"
            "  Issues:         github.com/gongahkia/yuho/issues\n"
        )
        yield Static(
            "[bold]Transpile Targets[/bold]\n"
            "  JSON, JSON-LD, English, LaTeX, Mermaid, Alloy, GraphQL, Blocks\n"
        )
        yield Static(
            "[bold]Scope[/bold]\n"
            "  Primary focus: Singapore Penal Code (1871)\n"
            "  Covered: ss. 299, 300, 319, 378, 383, 415, 420, 463, 499, 503\n"
            "  Extensible to any jurisdiction's statutory provisions\n"
        )
        yield Rule()
        yield Static(
            "[dim]Built for legal education and legal tech development.\n"
            "Encode complex legalese into machine-readable, verifiable models.[/dim]\n"
        )


# ─── Main Application ───────────────────────────────────────────────────────


class YuhoApp(App):
    """Yuho Terminal User Interface."""
    TITLE = "Yuho"
    SUB_TITLE = f"Legal Statute DSL v{__version__}"
    CSS = """
Screen {
    background: $surface;
}
#app-container {
    layout: horizontal;
    height: 1fr;
}
#sidebar {
    width: 26;
    background: $panel;
    border-right: thick $primary;
    padding: 1 0;
}
#sidebar-title {
    text-align: center;
    text-style: bold;
    color: $primary;
    padding: 0 1;
    margin-bottom: 1;
}
#nav-list {
    height: 1fr;
}
#content-area {
    width: 1fr;
    height: 1fr;
}
.panel {
    padding: 1 2;
    height: 1fr;
    width: 1fr;
}
.input-row {
    layout: horizontal;
    height: auto;
    margin-bottom: 1;
    align: left middle;
}
.input-row Input {
    width: 1fr;
    margin-right: 1;
}
.input-row Button {
    min-width: 14;
}
.input-row Select {
    width: 22;
    margin-right: 1;
}
.input-row Static {
    width: auto;
    padding: 0 1 0 0;
}
.form-label {
    width: 16;
    padding-top: 1;
}
.split-view {
    layout: horizontal;
    height: 1fr;
}
.split-view TextArea {
    width: 1fr;
    height: 1fr;
}
#transpile-source {
    margin-right: 1;
}
.action-row {
    layout: horizontal;
    height: auto;
    margin-top: 1;
    margin-bottom: 1;
}
.action-row Button {
    margin-right: 1;
}
.quick-actions {
    layout: horizontal;
    height: auto;
    margin-top: 1;
    align: center middle;
}
.quick-actions Button {
    margin: 0 1;
}
#mascot, #about-mascot {
    text-align: center;
    color: $primary;
    margin: 1 0;
}
#welcome-text {
    text-align: center;
}
.repl-prompt {
    width: auto;
    padding-top: 1;
}
RichLog {
    height: 1fr;
    border: solid $primary;
}
TextArea {
    height: 10;
}
#wiz-output {
    height: 16;
}
Rule {
    margin: 1 0;
}
Select {
    width: 1fr;
}
SettingsPanel Select {
    width: 1fr;
}
HomePanel, AboutPanel {
    align: center top;
}
"""
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("f1", "help_screen", "Help", show=True),
        Binding("1", "nav(0)", "Home", show=False),
        Binding("2", "nav(1)", "Check", show=False),
        Binding("3", "nav(2)", "Transpile", show=False),
        Binding("4", "nav(3)", "Wizard", show=False),
        Binding("5", "nav(4)", "REPL", show=False),
        Binding("6", "nav(5)", "Lint", show=False),
        Binding("7", "nav(6)", "Test", show=False),
        Binding("8", "nav(7)", "Settings", show=False),
        Binding("9", "nav(8)", "About", show=False),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="app-container"):
            with Vertical(id="sidebar"):
                yield Static(YUHO_LOGO_SMALL, id="sidebar-title")
                yield Rule()
                yield OptionList(*NAV_ITEMS, id="nav-list")
            with ContentSwitcher(initial="home", id="content-area"):
                yield HomePanel(id="home", classes="panel")
                yield CheckPanel(id="check", classes="panel")
                yield TranspilePanel(id="transpile", classes="panel")
                yield WizardPanel(id="wizard", classes="panel")
                yield ReplPanel(id="repl", classes="panel")
                yield LintPanel(id="lint", classes="panel")
                yield TestPanel(id="test", classes="panel")
                yield SettingsPanel(id="settings", classes="panel")
                yield AboutPanel(id="about", classes="panel")
        yield Footer()

    def action_nav(self, idx: int) -> None:
        if 0 <= idx < len(NAV_IDS):
            self.query_one("#content-area", ContentSwitcher).current = NAV_IDS[idx]
            self.query_one("#nav-list", OptionList).highlighted = idx

    @on(OptionList.OptionSelected, "#nav-list")
    def on_nav_selected(self, event: OptionList.OptionSelected) -> None:
        self.action_nav(event.option_index)

    def action_help_screen(self) -> None:
        self.notify(
            "Navigate: 1-9 keys or sidebar | Tab: cycle focus | q: quit | F1: help",
            title="Yuho TUI Help",
            timeout=8,
        )

    @on(Button.Pressed, "#btn-open")
    def handle_open_file(self) -> None:
        self.action_nav(1)
        self.query_one("#check-path", Input).focus()

    @on(Button.Pressed, "#btn-wizard")
    def handle_new_wizard(self) -> None:
        self.action_nav(3)

    @on(Button.Pressed, "#btn-copy-output")
    def handle_copy_output(self) -> None:
        text = self.query_one("#transpile-output", TextArea).text
        if not text:
            self.notify("No output to copy.", severity="warning")
            return
        import subprocess
        for cmd in [["pbcopy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"]]:
            try:
                subprocess.run(cmd, input=text.encode(), check=True)
                self.notify("Copied to clipboard.")
                return
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        self.notify("Clipboard not available. Use Save instead.", severity="warning")

    @on(Button.Pressed, "#btn-save-output")
    def handle_save_output(self) -> None:
        text = self.query_one("#transpile-output", TextArea).text
        if not text:
            self.notify("No output to save.", severity="warning")
            return
        target = self.query_one("#transpile-target", Select).value
        ext_map = {
            "json": ".json", "jsonld": ".jsonld", "english": ".txt",
            "latex": ".tex", "mermaid": ".md", "alloy": ".als",
            "graphql": ".graphql", "blocks": ".json",
        }
        ext = ext_map.get(str(target), ".txt")
        out_path = Path(f"output{ext}")
        out_path.write_text(text, encoding="utf-8")
        self.notify(f"Saved to {out_path}")

    @on(Button.Pressed, "#btn-wiz-copy")
    def handle_wiz_copy(self) -> None:
        text = self.query_one("#wiz-output", TextArea).text
        if not text:
            self.notify("Generate code first.", severity="warning")
            return
        import subprocess
        for cmd in [["pbcopy"], ["xclip", "-selection", "clipboard"]]:
            try:
                subprocess.run(cmd, input=text.encode(), check=True)
                self.notify("Copied to clipboard.")
                return
            except (FileNotFoundError, subprocess.CalledProcessError):
                continue
        self.notify("Clipboard not available.", severity="warning")

    @on(Button.Pressed, "#btn-wiz-save")
    def handle_wiz_save(self) -> None:
        text = self.query_one("#wiz-output", TextArea).text
        if not text:
            self.notify("Generate code first.", severity="warning")
            return
        section = self.query_one("#wiz-section", Input).value.strip() or "statute"
        out_path = Path(f"{section}.yh")
        out_path.write_text(text, encoding="utf-8")
        self.notify(f"Saved to {out_path}")
