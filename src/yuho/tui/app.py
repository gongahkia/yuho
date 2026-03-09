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
from textual.screen import ModalScreen
from textual.widgets import (
    Header, Footer, Static, Button, Input, TextArea,
    Select, Label, RichLog, OptionList,
    ContentSwitcher, Rule, DirectoryTree,
)
from textual import on, work
from textual.message import Message

from yuho import __version__
from yuho.tui.ascii_art import YUHO_MASCOT, YUHO_LOGO_SMALL

def _copy_to_clipboard(text: str) -> bool:
    """Cross-platform clipboard copy. Returns True on success."""
    import subprocess, platform
    if platform.system() == "Windows":
        try:
            subprocess.run(["clip"], input=text.encode("utf-16le"), check=True)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            pass
    for cmd in [
        ["pbcopy"],
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
    ]:
        try:
            subprocess.run(cmd, input=text.encode(), check=True, timeout=5)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    return False

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
    "  Eval",
    "  Wizard",
    "  REPL",
    "  Lint",
    "  Test",
    "  Format",
    "  Diff",
    "  Graph",
    "  Verify",
    "  AST View",
    "  Explain",
    "  Generate",
    "  Init",
    "  Contribute",
    "  Library",
    "  Settings",
    "  About",
]
NAV_IDS = [
    "home", "check", "transpile", "eval", "wizard", "repl", "lint", "test",
    "fmt", "diff", "graph", "verify", "ast-view", "explain", "generate",
    "init", "contribute", "library", "settings", "about",
]


import re as _re
_ANSI_RE = _re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)

def capture_cli(func, *args, strip_ansi: bool = True, **kwargs) -> Tuple[str, str]:
    """Run a function capturing stdout/stderr, including click.echo output."""
    import click as _click
    out, err = io.StringIO(), io.StringIO()
    _orig_echo = _click.echo
    def _patched_echo(message=None, file=None, nl=True, err_flag=False, color=None, **kw):
        target = err if err_flag else (file if file not in (None, sys.stdout, sys.stderr) else out)
        if message is not None:
            target.write(str(message))
        if nl:
            target.write("\n")
    try:
        _click.echo = _patched_echo
        with redirect_stdout(out), redirect_stderr(err):
            func(*args, **kwargs)
    except SystemExit:
        pass
    except Exception as e:
        err.write(str(e))
    finally:
        _click.echo = _orig_echo
    stdout_val, stderr_val = out.getvalue(), err.getvalue()
    if strip_ansi:
        stdout_val, stderr_val = _strip_ansi(stdout_val), _strip_ansi(stderr_val)
    return stdout_val, stderr_val


# ─── File Picker ─────────────────────────────────────────────────────────────


class FilePickerScreen(ModalScreen[str]):
    """Modal file picker using DirectoryTree."""
    BINDINGS = [Binding("escape", "cancel", "Cancel")]
    CSS = """
    FilePickerScreen { align: center middle; }
    #fp-container {
        width: 70;
        height: 30;
        border: thick $primary;
        background: $surface;
        padding: 1;
    }
    #fp-tree { height: 1fr; }
    #fp-selected { height: 3; margin-top: 1; }
    #fp-actions { height: auto; margin-top: 1; layout: horizontal; }
    #fp-actions Button { margin-right: 1; }
    """

    def __init__(self, start_dir: str = ".") -> None:
        super().__init__()
        self._start_dir = start_dir

    def compose(self) -> ComposeResult:
        with Container(id="fp-container"):
            yield Static("[bold magenta]Select a .yh file[/bold magenta]")
            yield DirectoryTree(self._start_dir, id="fp-tree")
            yield Input(placeholder="Selected file...", id="fp-selected", disabled=True)
            with Container(id="fp-actions"):
                yield Button("Open", id="fp-open", variant="primary")
                yield Button("Cancel", id="fp-cancel")

    @on(DirectoryTree.FileSelected, "#fp-tree")
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self.query_one("#fp-selected", Input).value = str(event.path)

    @on(Button.Pressed, "#fp-open")
    def handle_open(self) -> None:
        path = self.query_one("#fp-selected", Input).value
        if path:
            self.dismiss(path)

    @on(Button.Pressed, "#fp-cancel")
    def handle_cancel(self) -> None:
        self.dismiss("")

    def action_cancel(self) -> None:
        self.dismiss("")


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
            "  [bold magenta]1[/] Home      — This dashboard\n"
            "  [bold magenta]2[/] Check     — Parse and validate a .yh file\n"
            "  [bold magenta]3[/] Transpile — Convert to JSON, English, Mermaid, LaTeX...\n"
            "  [bold magenta]4[/] Eval      — Evaluate and interpret a .yh file\n"
            "  [bold magenta]5[/] Wizard    — Create a statute step-by-step\n"
            "  [bold magenta]6[/] REPL      — Interactive experimentation\n"
            "  [bold magenta]7[/] Lint      — Style and best practice checks\n"
            "  [bold magenta]8[/] Test      — Run .yh test files\n"
            "  [bold magenta]9[/] Format    — Apply canonical formatting\n"
            "  [dim]  + Diff, Graph, Verify, AST, Explain, Generate, Init,\n"
            "    Contribute, Library, Settings, About via sidebar[/dim]\n",
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
    """Parse and validate .yh files with real-time feedback."""
    _debounce_timer: Optional[object] = None
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Check[/bold magenta] — Parse and validate a Yuho file\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="check-path")
            yield Button("Browse", id="btn-check-browse")
            yield Button("Check", id="btn-check", variant="primary")
        yield Static("[dim]Or type/paste Yuho code below for real-time validation:[/dim]")
        yield TextArea(id="check-editor")
        yield Static("", id="check-live-status")
        yield RichLog(id="check-output", highlight=True, markup=True)

    @on(TextArea.Changed, "#check-editor")
    def handle_editor_change(self) -> None:
        if self._debounce_timer is not None:
            self._debounce_timer.stop()
        self._debounce_timer = self.set_timer(0.5, self._validate_editor_content)

    def _validate_editor_content(self) -> None:
        text = self.query_one("#check-editor", TextArea).text.strip()
        status = self.query_one("#check-live-status", Static)
        if not text:
            status.update("")
            return
        try:
            from yuho.parser import get_parser
            parser = get_parser()
            result = parser.parse(text, "<editor>")
            if result.errors:
                msgs = [f"L{e.location.line}:{e.location.col} {e.message}" for e in result.errors[:3]]
                status.update(f"[red]{len(result.errors)} error(s):[/red] " + "; ".join(msgs))
            else:
                from yuho.ast import ASTBuilder
                builder = ASTBuilder(text, "<editor>")
                ast = builder.build(result.tree.root_node)
                parts = []
                if ast.statutes: parts.append(f"{len(ast.statutes)} statute(s)")
                if ast.type_defs: parts.append(f"{len(ast.type_defs)} type(s)")
                if ast.function_defs: parts.append(f"{len(ast.function_defs)} fn(s)")
                summary = ", ".join(parts) if parts else "valid (empty)"
                status.update(f"[green]OK:[/green] {summary}")
        except Exception as e:
            status.update(f"[yellow]{e}[/yellow]")

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
            yield Button("Browse", id="btn-transpile-browse")
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


# ─── Eval Panel ──────────────────────────────────────────────────────────────


class EvalPanel(Container):
    """Evaluate and interpret a .yh file."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Eval[/bold magenta] — Evaluate and interpret a Yuho file\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="eval-path")
            yield Button("Browse", id="btn-eval-browse")
            yield Button("Eval", id="btn-eval", variant="primary")
        yield RichLog(id="eval-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-eval")
    def handle_eval(self) -> None:
        output = self.query_one("#eval-output", RichLog)
        output.clear()
        file_path = self.query_one("#eval-path", Input).value.strip()
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
        self._run_eval(str(path))

    @on(Input.Submitted, "#eval-path")
    def handle_eval_enter(self) -> None:
        self.handle_eval()

    @work(thread=True)
    def _run_eval(self, file_path: str) -> None:
        output = self.query_one("#eval-output", RichLog)
        try:
            from yuho.parser import get_parser
            from yuho.ast import ASTBuilder
            from yuho.eval.interpreter import Interpreter, AssertionError_, InterpreterError
            parser = get_parser()
            source = Path(file_path).read_text(encoding="utf-8")
            result = parser.parse(source, file_path)
            if result.errors:
                self.app.call_from_thread(
                    output.write,
                    f"[bold red]Parse errors ({len(result.errors)}):[/]"
                )
                for err in result.errors:
                    self.app.call_from_thread(
                        output.write,
                        f"  [red]L{err.location.line}:{err.location.col}[/] {err.message}"
                    )
                return
            builder = ASTBuilder(source, file_path)
            ast = builder.build(result.tree.root_node)
            self.app.call_from_thread(output.write, f"[bold green]Parsed:[/] {file_path}")
            self.app.call_from_thread(
                output.write,
                f"  Statutes:   {len(ast.statutes)}\n"
                f"  Functions:  {len(ast.function_defs)}\n"
                f"  Structs:    {len(ast.type_defs)}\n"
                f"  Variables:  {len(ast.variables)}"
            )
            self.app.call_from_thread(output.write, "")
            interp = Interpreter()
            try:
                env = interp.interpret(ast)
                self.app.call_from_thread(output.write, "[bold green]Evaluation complete.[/bold green]")
                if env.bindings:
                    self.app.call_from_thread(output.write, "\n[bold]Variables:[/bold]")
                    for name, val in env.bindings.items():
                        self.app.call_from_thread(output.write, f"  {name} = {val}")
                if env.statutes:
                    self.app.call_from_thread(output.write, f"\n[bold]Statutes registered:[/bold] {len(env.statutes)}")
                    for sec in env.statutes:
                        self.app.call_from_thread(output.write, f"  s.{sec}")
                if env.function_defs:
                    self.app.call_from_thread(output.write, f"\n[bold]Functions:[/bold] {len(env.function_defs)}")
                    for fn_name in env.function_defs:
                        self.app.call_from_thread(output.write, f"  fn {fn_name}")
                if env.struct_defs:
                    self.app.call_from_thread(output.write, f"\n[bold]Structs:[/bold] {len(env.struct_defs)}")
                    for sn in env.struct_defs:
                        self.app.call_from_thread(output.write, f"  struct {sn}")
            except AssertionError_ as ae:
                self.app.call_from_thread(output.write, f"[bold yellow]Assertion failed:[/] {ae}")
            except InterpreterError as ie:
                self.app.call_from_thread(output.write, f"[bold red]Interpreter error:[/] {ie}")
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


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
        yield Static('[bold]Step 5.5: Exceptions[/bold] [dim](one per line: label: "condition" "effect")[/dim]')
        yield TextArea(id="wiz-exceptions")
        yield Rule()
        yield Static('[bold]Step 5.6: Case Law[/bold] [dim](one per line: "case name" "citation" "holding")[/dim]')
        yield TextArea(id="wiz-caselaw")
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
        exceptions = self.query_one("#wiz-exceptions", TextArea).text.strip()
        caselaw = self.query_one("#wiz-caselaw", TextArea).text.strip()
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
        if exceptions:
            lines.append("    exceptions {")
            for ex in exceptions.splitlines():
                ex = ex.strip()
                if ex:
                    lines.append(f"        {ex};")
            lines.append("    }")
            lines.append("")
        if caselaw:
            lines.append("    case_law {")
            for cl in caselaw.splitlines():
                cl = cl.strip()
                if cl:
                    lines.append(f"        {cl};")
            lines.append("    }")
            lines.append("")
        lines.append("}")
        output_area.load_text("\n".join(lines))


class ReplPanel(Container):
    """Interactive REPL for Yuho experimentation."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]REPL[/bold magenta] — Interactive Yuho experimentation\n")
        yield Static("[dim]Commands: help, load <file>, transpile <target>, ast, check, eval, env, targets, clear, exit[/dim]\n")
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
        self._interpreter = None # lazy init
        self._env = None # lazy init

    def _ensure_interpreter(self):
        """Lazily initialize interpreter and environment."""
        if self._interpreter is None:
            from yuho.eval.interpreter import Interpreter, Environment
            self._env = Environment()
            self._interpreter = Interpreter(env=self._env)
        return self._interpreter, self._env

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
                "  [bold]eval[/]          — Evaluate buffer through interpreter\n"
                "  [bold]env[/]           — Show current environment state\n"
                "  [bold]targets[/]       — List transpile targets\n"
                "  [bold]buffer[/]        — Show current buffer\n"
                "  [bold]clear[/]         — Clear output\n"
                "  [bold]reset[/]         — Clear buffer and environment\n"
                "  [bold]exit[/]          — Exit REPL"
            )
        elif cmd == "clear":
            output.clear()
        elif cmd == "reset":
            self._source_buffer = ""
            self._repl_file = None
            self._interpreter = None
            self._env = None
            output.write("[dim](buffer and environment cleared)[/dim]")
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
        elif cmd == "eval":
            if not self._source_buffer:
                output.write("[yellow]Buffer is empty. Load a file or type code first.[/yellow]")
                return
            self._repl_eval()
        elif cmd == "env":
            self._repl_show_env()
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
            self._repl_try_eval(cmd)

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
    def _repl_eval(self) -> None:
        """Evaluate the full buffer through the interpreter."""
        output = self.query_one("#repl-output", RichLog)
        try:
            from yuho.parser.wrapper import get_parser
            from yuho.ast.builder import ASTBuilder
            from yuho.eval.interpreter import Interpreter, AssertionError_, InterpreterError
            parser = get_parser()
            result = parser.parse(self._source_buffer, file=self._repl_file or "<repl>")
            if not result.is_valid:
                for err in result.errors:
                    self.app.call_from_thread(output.write, f"  [red]error[/] line {err.location.line}: {err.message}")
                return
            builder = ASTBuilder(result.source, file=self._repl_file or "<repl>")
            ast = builder.build(result.root_node)
            interp, env = self._ensure_interpreter()
            try:
                interp.interpret(ast)
                self.app.call_from_thread(output.write, "[green]Evaluated successfully.[/green]")
                if env.bindings:
                    for name, val in env.bindings.items():
                        self.app.call_from_thread(output.write, f"  {name} = {val}")
            except AssertionError_ as ae:
                self.app.call_from_thread(output.write, f"[yellow]Assertion failed:[/] {ae}")
            except InterpreterError as ie:
                self.app.call_from_thread(output.write, f"[red]Interpreter error:[/] {ie}")
        except Exception as e:
            self.app.call_from_thread(output.write, f"[red]Error: {e}[/red]")

    def _repl_show_env(self) -> None:
        """Show current interpreter environment."""
        output = self.query_one("#repl-output", RichLog)
        if self._env is None:
            output.write("[dim](no environment yet — run eval first)[/dim]")
            return
        env = self._env
        if env.bindings:
            output.write("[bold]Variables:[/bold]")
            for name, val in env.bindings.items():
                output.write(f"  {name} = {val}")
        else:
            output.write("[dim]No variables.[/dim]")
        if env.struct_defs:
            output.write(f"[bold]Structs:[/bold] {len(env.struct_defs)}")
            for sn in env.struct_defs:
                output.write(f"  struct {sn}")
        if env.function_defs:
            output.write(f"[bold]Functions:[/bold] {len(env.function_defs)}")
            for fn_name in env.function_defs:
                output.write(f"  fn {fn_name}")
        if env.statutes:
            output.write(f"[bold]Statutes:[/bold] {len(env.statutes)}")
            for sec in env.statutes:
                output.write(f"  s.{sec}")

    @work(thread=True)
    def _repl_try_eval(self, code: str) -> None:
        """Try to parse and eval the newly entered code line."""
        output = self.query_one("#repl-output", RichLog)
        try:
            from yuho.parser.wrapper import get_parser
            from yuho.ast.builder import ASTBuilder
            from yuho.eval.interpreter import AssertionError_, InterpreterError
            parser = get_parser()
            result = parser.parse(self._source_buffer, file="<repl>")
            if not result.is_valid:
                return # not valid yet, just accumulate
            builder = ASTBuilder(result.source, file="<repl>")
            ast = builder.build(result.root_node)
            interp, env = self._ensure_interpreter()
            try:
                interp.interpret(ast)
                if env.bindings:
                    for name, val in env.bindings.items():
                        self.app.call_from_thread(output.write, f"  [dim]{name} = {val}[/dim]")
            except (AssertionError_, InterpreterError):
                pass # silently ignore for incremental input
        except Exception:
            pass # code not complete yet

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


class FmtPanel(Container):
    """Format .yh files."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Format[/bold magenta] — Apply canonical formatting\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="fmt-path")
            yield Button("Format", id="btn-fmt", variant="primary")
            yield Button("Check Only", id="btn-fmt-check")
        yield RichLog(id="fmt-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-fmt")
    def handle_fmt(self) -> None:
        self._do_fmt(in_place=True)

    @on(Button.Pressed, "#btn-fmt-check")
    def handle_fmt_check(self) -> None:
        self._do_fmt(in_place=False)

    @on(Input.Submitted, "#fmt-path")
    def handle_fmt_enter(self) -> None:
        self._do_fmt(in_place=True)

    def _do_fmt(self, in_place: bool) -> None:
        output = self.query_one("#fmt-output", RichLog)
        output.clear()
        file_path = self.query_one("#fmt-path", Input).value.strip()
        if not file_path:
            output.write("[bold red]Error:[/] Please enter a file path.")
            return
        self._run_fmt(file_path, in_place)

    @work(thread=True)
    def _run_fmt(self, file_path: str, in_place: bool) -> None:
        output = self.query_one("#fmt-output", RichLog)
        try:
            from yuho.cli.commands.fmt import run_fmt
            if in_place:
                stdout, stderr = capture_cli(run_fmt, file_path, in_place=True, check=False, verbose=False)
            else:
                stdout, stderr = capture_cli(run_fmt, file_path, in_place=False, check=True, verbose=False)
            result = stdout.strip() or stderr.strip() or "[green]File is properly formatted.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


class DiffPanel(Container):
    """Compare two .yh files."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Diff[/bold magenta] — Compare two Yuho files\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="File 1 path...", id="diff-path1")
            yield Input(placeholder="File 2 path...", id="diff-path2")
            yield Button("Compare", id="btn-diff", variant="primary")
        yield RichLog(id="diff-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-diff")
    def handle_diff(self) -> None:
        output = self.query_one("#diff-output", RichLog)
        output.clear()
        p1 = self.query_one("#diff-path1", Input).value.strip()
        p2 = self.query_one("#diff-path2", Input).value.strip()
        if not p1 or not p2:
            output.write("[bold red]Error:[/] Both file paths are required.")
            return
        self._run_diff(p1, p2)

    @work(thread=True)
    def _run_diff(self, file1: str, file2: str) -> None:
        output = self.query_one("#diff-output", RichLog)
        try:
            from yuho.cli.commands.diff import run_diff
            stdout, stderr = capture_cli(run_diff, file1, file2, verbose=False, color=False)
            result = stdout.strip() or stderr.strip() or "[green]Files are identical.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


# ─── Graph Panel ─────────────────────────────────────────────────────────────


class GraphPanel(Container):
    """Generate dependency graphs for .yh files."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Graph[/bold magenta] — Generate dependency graph\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="graph-path")
            yield Button("Browse", id="btn-graph-browse")
            yield Select(
                options=[("Mermaid", "mermaid"), ("DOT", "dot")],
                value="mermaid",
                id="graph-format",
            )
            yield Button("Generate", id="btn-graph", variant="primary")
        yield RichLog(id="graph-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-graph")
    def handle_graph(self) -> None:
        output = self.query_one("#graph-output", RichLog)
        output.clear()
        file_path = self.query_one("#graph-path", Input).value.strip()
        if not file_path:
            output.write("[bold red]Error:[/] Please enter a file path.")
            return
        fmt_select = self.query_one("#graph-format", Select)
        fmt = str(fmt_select.value) if fmt_select.value != Select.BLANK else "mermaid"
        self._run_graph(file_path, fmt)

    @on(Input.Submitted, "#graph-path")
    def handle_graph_enter(self) -> None:
        self.handle_graph()

    @work(thread=True)
    def _run_graph(self, file_path: str, fmt: str) -> None:
        output = self.query_one("#graph-output", RichLog)
        try:
            from yuho.cli.commands.graph import run_graph
            stdout, stderr = capture_cli(run_graph, file_path, format=fmt, verbose=False)
            result = stdout.strip() or stderr.strip() or "(no output)"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


class VerifyPanel(Container):
    """Formal verification with Alloy/Z3."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Verify[/bold magenta] — Formal verification (Alloy/Z3)\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="verify-path")
            yield Select(
                options=[("Combined", "combined"), ("Alloy", "alloy"), ("Z3", "z3")],
                value="combined",
                id="verify-engine",
            )
            yield Button("Verify", id="btn-verify", variant="primary")
            yield Button("Capabilities", id="btn-verify-caps")
        yield RichLog(id="verify-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-verify")
    def handle_verify(self) -> None:
        output = self.query_one("#verify-output", RichLog)
        output.clear()
        file_path = self.query_one("#verify-path", Input).value.strip()
        if not file_path:
            output.write("[bold red]Error:[/] Please enter a file path.")
            return
        engine = self.query_one("#verify-engine", Select).value
        engine_str = str(engine) if engine != Select.BLANK else "combined"
        self._run_verify(file_path, engine_str)

    @on(Button.Pressed, "#btn-verify-caps")
    def handle_caps(self) -> None:
        output = self.query_one("#verify-output", RichLog)
        output.clear()
        self._run_caps()

    @work(thread=True)
    def _run_verify(self, file_path: str, engine: str) -> None:
        output = self.query_one("#verify-output", RichLog)
        try:
            from yuho.cli.commands.verify import run_verify
            stdout, stderr = capture_cli(run_verify, file_path, engine=engine, verbose=False)
            result = stdout.strip() or stderr.strip() or "[green]Verification passed.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")

    @work(thread=True)
    def _run_caps(self) -> None:
        output = self.query_one("#verify-output", RichLog)
        try:
            from yuho.cli.commands.verify import run_verify
            stdout, stderr = capture_cli(run_verify, None, capabilities_only=True, verbose=False)
            result = stdout.strip() or stderr.strip() or "(no output)"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


class ASTViewPanel(Container):
    """Visualize AST structure."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]AST View[/bold magenta] — Visualize abstract syntax tree\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="ast-path")
            yield Button("Show AST", id="btn-ast-show", variant="primary")
            yield Button("Stats", id="btn-ast-stats")
        yield RichLog(id="ast-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-ast-show")
    def handle_ast(self) -> None:
        output = self.query_one("#ast-output", RichLog)
        output.clear()
        file_path = self.query_one("#ast-path", Input).value.strip()
        if not file_path:
            output.write("[bold red]Error:[/] Please enter a file path.")
            return
        self._run_ast(file_path, stats=False)

    @on(Button.Pressed, "#btn-ast-stats")
    def handle_ast_stats(self) -> None:
        output = self.query_one("#ast-output", RichLog)
        output.clear()
        file_path = self.query_one("#ast-path", Input).value.strip()
        if not file_path:
            output.write("[bold red]Error:[/] Please enter a file path.")
            return
        self._run_ast(file_path, stats=True)

    @on(Input.Submitted, "#ast-path")
    def handle_ast_enter(self) -> None:
        self.handle_ast()

    @work(thread=True)
    def _run_ast(self, file_path: str, stats: bool) -> None:
        output = self.query_one("#ast-output", RichLog)
        try:
            from yuho.cli.commands.ast_viz import run_ast_viz
            stdout, stderr = capture_cli(run_ast_viz, file=file_path, stats=stats, verbose=False, color=False, depth=0, no_unicode=False)
            result = stdout.strip() or stderr.strip() or "(no output)"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


# ─── Explain Panel ───────────────────────────────────────────────────────────


class ExplainPanel(Container):
    """Generate natural language explanations of .yh files."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Explain[/bold magenta] — Generate natural language explanation\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="explain-path")
            yield Button("Browse", id="btn-explain-browse")
        with Horizontal(classes="input-row"):
            yield Label("Section:", classes="form-label")
            yield Input(placeholder="(optional) specific section to explain", id="explain-section")
        with Horizontal(classes="input-row"):
            yield Label("Provider:", classes="form-label")
            yield Select(
                options=[
                    ("Ollama (local)", "ollama"),
                    ("HuggingFace", "huggingface"),
                    ("OpenAI", "openai"),
                    ("Anthropic", "anthropic"),
                ],
                value="ollama",
                id="explain-provider",
            )
        with Horizontal(classes="input-row"):
            yield Label("Model:", classes="form-label")
            yield Input(placeholder="e.g. llama3, gpt-4", id="explain-model")
        with Horizontal(classes="input-row"):
            yield Select(
                options=[("Online", "online"), ("Offline", "offline")],
                value="online",
                id="explain-offline",
            )
            yield Select(
                options=[("Use LLM", "use-llm"), ("No LLM", "no-llm")],
                value="use-llm",
                id="explain-no-llm",
            )
            yield Button("Explain", id="btn-explain", variant="primary")
        yield RichLog(id="explain-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-explain")
    def handle_explain(self) -> None:
        output = self.query_one("#explain-output", RichLog)
        output.clear()
        file_path = self.query_one("#explain-path", Input).value.strip()
        if not file_path:
            output.write("[bold red]Error:[/] Please enter a file path.")
            return
        section = self.query_one("#explain-section", Input).value.strip() or None
        provider_sel = self.query_one("#explain-provider", Select).value
        provider = str(provider_sel) if provider_sel != Select.BLANK else None
        model = self.query_one("#explain-model", Input).value.strip() or None
        offline_sel = self.query_one("#explain-offline", Select).value
        offline = (str(offline_sel) == "offline")
        no_llm_sel = self.query_one("#explain-no-llm", Select).value
        no_llm = (str(no_llm_sel) == "no-llm")
        self._run_explain(file_path, section, provider, model, offline, no_llm)

    @on(Input.Submitted, "#explain-path")
    def handle_explain_enter(self) -> None:
        self.handle_explain()

    @work(thread=True)
    def _run_explain(self, file_path: str, section: Optional[str], provider: Optional[str], model: Optional[str], offline: bool, no_llm: bool) -> None:
        output = self.query_one("#explain-output", RichLog)
        try:
            from yuho.cli.commands.explain import run_explain
            stdout, stderr = capture_cli(
                run_explain, file_path,
                section=section, provider=provider, model=model,
                offline=offline, no_llm=no_llm, verbose=False, stream=False,
            )
            result = stdout.strip() or stderr.strip() or "(no output)"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


# ─── Generate Panel ──────────────────────────────────────────────────────────


class GeneratePanel(Container):
    """Scaffold a new statute file from a template."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Generate[/bold magenta] — Scaffold a new statute\n")
        with Horizontal(classes="input-row"):
            yield Label("Section:", classes="form-label")
            yield Input(placeholder="e.g. 415", id="gen-section")
        with Horizontal(classes="input-row"):
            yield Label("Title:", classes="form-label")
            yield Input(placeholder="e.g. Cheating", id="gen-title")
        with Horizontal(classes="input-row"):
            yield Label("Template:", classes="form-label")
            yield Select(
                options=[("Standard", "standard"), ("Minimal", "minimal"), ("Full", "full")],
                value="standard",
                id="gen-template",
            )
        with Horizontal(classes="input-row"):
            yield Select(
                options=[("Include Definitions", "yes"), ("No Definitions", "no")],
                value="yes",
                id="gen-definitions",
            )
            yield Select(
                options=[("Include Penalty", "yes"), ("No Penalty", "no")],
                value="yes",
                id="gen-penalty",
            )
            yield Select(
                options=[("Include Illustrations", "yes"), ("No Illustrations", "no")],
                value="yes",
                id="gen-illustrations",
            )
        with Horizontal(classes="action-row"):
            yield Button("Generate", id="btn-generate", variant="primary")
        yield RichLog(id="gen-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-generate")
    def handle_generate(self) -> None:
        output = self.query_one("#gen-output", RichLog)
        output.clear()
        section = self.query_one("#gen-section", Input).value.strip()
        title = self.query_one("#gen-title", Input).value.strip()
        if not section or not title:
            output.write("[bold red]Error:[/] Section and Title are required.")
            return
        tmpl_sel = self.query_one("#gen-template", Select).value
        template = str(tmpl_sel) if tmpl_sel != Select.BLANK else "standard"
        no_defs = str(self.query_one("#gen-definitions", Select).value) == "no"
        no_penalty = str(self.query_one("#gen-penalty", Select).value) == "no"
        no_illust = str(self.query_one("#gen-illustrations", Select).value) == "no"
        self._run_generate(section, title, template, no_defs, no_penalty, no_illust)

    @work(thread=True)
    def _run_generate(self, section: str, title: str, template: str, no_defs: bool, no_penalty: bool, no_illust: bool) -> None:
        output = self.query_one("#gen-output", RichLog)
        try:
            from yuho.cli.commands.generate import run_generate
            stdout, stderr = capture_cli(
                run_generate, section, title,
                template=template,
                no_definitions=no_defs,
                no_penalty=no_penalty,
                no_illustrations=no_illust,
                verbose=False, color=False,
            )
            result = stdout.strip() or stderr.strip() or "(no output)"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


# ─── Init Panel ──────────────────────────────────────────────────────────────


class InitPanel(Container):
    """Initialize a new Yuho project."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Init[/bold magenta] — Initialize a new Yuho project\n")
        with Horizontal(classes="input-row"):
            yield Label("Project Name:", classes="form-label")
            yield Input(placeholder="e.g. my-statute-project", id="init-name")
        with Horizontal(classes="input-row"):
            yield Label("Directory:", classes="form-label")
            yield Input(placeholder="(optional) target directory", id="init-dir")
        with Horizontal(classes="action-row"):
            yield Button("Init", id="btn-init", variant="primary")
        yield RichLog(id="init-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-init")
    def handle_init(self) -> None:
        output = self.query_one("#init-output", RichLog)
        output.clear()
        name = self.query_one("#init-name", Input).value.strip() or None
        directory = self.query_one("#init-dir", Input).value.strip() or None
        self._run_init(name, directory)

    @work(thread=True)
    def _run_init(self, name: Optional[str], directory: Optional[str]) -> None:
        output = self.query_one("#init-output", RichLog)
        try:
            from yuho.cli.commands.init import run_init
            stdout, stderr = capture_cli(run_init, name=name, directory=directory, verbose=False)
            result = stdout.strip() or stderr.strip() or "[green]Project initialized.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


# ─── Contribute Panel ────────────────────────────────────────────────────────


class ContributePanel(Container):
    """Validate .yh files for contribution."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Contribute[/bold magenta] — Validate a file for contribution\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Enter path to .yh file...", id="contribute-path")
            yield Button("Browse", id="btn-contribute-browse")
            yield Button("Validate", id="btn-contribute", variant="primary")
        yield RichLog(id="contribute-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-contribute")
    def handle_contribute(self) -> None:
        output = self.query_one("#contribute-output", RichLog)
        output.clear()
        file_path = self.query_one("#contribute-path", Input).value.strip()
        if not file_path:
            output.write("[bold red]Error:[/] Please enter a file path.")
            return
        self._run_contribute(file_path)

    @on(Input.Submitted, "#contribute-path")
    def handle_contribute_enter(self) -> None:
        self.handle_contribute()

    @work(thread=True)
    def _run_contribute(self, file_path: str) -> None:
        output = self.query_one("#contribute-output", RichLog)
        try:
            from yuho.cli.commands.contribute import run_contribute
            stdout, stderr = capture_cli(run_contribute, file_path, verbose=False)
            result = stdout.strip() or stderr.strip() or "[green]File is valid for contribution.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")


# ─── Library Panel ───────────────────────────────────────────────────────────


class LibraryPanel(Container):
    """Statute package management."""
    def compose(self) -> ComposeResult:
        yield Static("[bold magenta]Library[/bold magenta] — Manage statute packages\n")
        with Horizontal(classes="input-row"):
            yield Input(placeholder="Search query or package name...", id="lib-query")
            yield Button("Search", id="btn-lib-search", variant="primary")
            yield Button("List Installed", id="btn-lib-list")
        with Horizontal(classes="action-row"):
            yield Button("Install", id="btn-lib-install", variant="success")
            yield Button("Uninstall", id="btn-lib-uninstall", variant="error")
            yield Button("Update", id="btn-lib-update")
            yield Button("Info", id="btn-lib-info")
            yield Button("Outdated", id="btn-lib-outdated")
            yield Button("Tree", id="btn-lib-tree")
            yield Button("Publish", id="btn-lib-publish", variant="warning")
        yield RichLog(id="lib-output", highlight=True, markup=True)

    @on(Button.Pressed, "#btn-lib-search")
    def handle_search(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        output.clear()
        query = self.query_one("#lib-query", Input).value.strip()
        if not query:
            output.write("[bold red]Error:[/] Please enter a search query.")
            return
        self._run_search(query)

    @on(Button.Pressed, "#btn-lib-list")
    def handle_list(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        output.clear()
        self._run_list()

    @on(Button.Pressed, "#btn-lib-install")
    def handle_install(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        output.clear()
        pkg = self.query_one("#lib-query", Input).value.strip()
        if not pkg:
            output.write("[bold red]Error:[/] Please enter a package name.")
            return
        self._run_install(pkg)

    @on(Button.Pressed, "#btn-lib-uninstall")
    def handle_uninstall(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        output.clear()
        pkg = self.query_one("#lib-query", Input).value.strip()
        if not pkg:
            output.write("[bold red]Error:[/] Please enter a package name.")
            return
        self._run_uninstall(pkg)

    @on(Button.Pressed, "#btn-lib-update")
    def handle_update(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        output.clear()
        pkg = self.query_one("#lib-query", Input).value.strip() or None
        self._run_update(pkg)

    @on(Button.Pressed, "#btn-lib-info")
    def handle_info(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        output.clear()
        pkg = self.query_one("#lib-query", Input).value.strip()
        if not pkg:
            output.write("[bold red]Error:[/] Please enter a package name.")
            return
        self._run_info(pkg)

    @on(Button.Pressed, "#btn-lib-outdated")
    def handle_outdated(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        output.clear()
        self._run_outdated()

    @on(Button.Pressed, "#btn-lib-tree")
    def handle_tree(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        output.clear()
        pkg = self.query_one("#lib-query", Input).value.strip() or None
        self._run_tree(pkg)

    @on(Button.Pressed, "#btn-lib-publish")
    def handle_publish(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        output.clear()
        pkg = self.query_one("#lib-query", Input).value.strip()
        if not pkg:
            output.write("[bold red]Error:[/] Please enter a package path.")
            return
        self._run_publish(pkg)

    @on(Input.Submitted, "#lib-query")
    def handle_search_enter(self) -> None:
        self.handle_search()

    @work(thread=True)
    def _run_search(self, query: str) -> None:
        output = self.query_one("#lib-output", RichLog)
        try:
            from yuho.cli.commands.library import run_library_search
            stdout, stderr = capture_cli(run_library_search, query, verbose=False)
            result = stdout.strip() or stderr.strip() or "[dim]No packages found.[/dim]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")

    @work(thread=True)
    def _run_list(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        try:
            from yuho.cli.commands.library import run_library_list
            stdout, stderr = capture_cli(run_library_list, verbose=False)
            result = stdout.strip() or stderr.strip() or "[dim]No packages installed.[/dim]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")

    @work(thread=True)
    def _run_install(self, package: str) -> None:
        output = self.query_one("#lib-output", RichLog)
        try:
            from yuho.cli.commands.library import run_library_install
            stdout, stderr = capture_cli(run_library_install, package, verbose=False)
            result = stdout.strip() or stderr.strip() or f"[green]Installed {package}.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")

    @work(thread=True)
    def _run_uninstall(self, package: str) -> None:
        output = self.query_one("#lib-output", RichLog)
        try:
            from yuho.cli.commands.library import run_library_uninstall
            stdout, stderr = capture_cli(run_library_uninstall, package, verbose=False)
            result = stdout.strip() or stderr.strip() or f"[green]Uninstalled {package}.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")

    @work(thread=True)
    def _run_update(self, package: Optional[str]) -> None:
        output = self.query_one("#lib-output", RichLog)
        try:
            from yuho.cli.commands.library import run_library_update
            if package:
                stdout, stderr = capture_cli(run_library_update, package=package, verbose=False)
            else:
                stdout, stderr = capture_cli(run_library_update, all_packages=True, verbose=False)
            result = stdout.strip() or stderr.strip() or "[green]Update complete.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")

    @work(thread=True)
    def _run_info(self, package: str) -> None:
        output = self.query_one("#lib-output", RichLog)
        try:
            from yuho.cli.commands.library import run_library_info
            stdout, stderr = capture_cli(run_library_info, package, verbose=False)
            result = stdout.strip() or stderr.strip() or "[dim]No info available.[/dim]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")

    @work(thread=True)
    def _run_outdated(self) -> None:
        output = self.query_one("#lib-output", RichLog)
        try:
            from yuho.cli.commands.library import run_library_outdated
            stdout, stderr = capture_cli(run_library_outdated, verbose=False)
            result = stdout.strip() or stderr.strip() or "[green]All packages up to date.[/green]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")

    @work(thread=True)
    def _run_tree(self, package: Optional[str]) -> None:
        output = self.query_one("#lib-output", RichLog)
        try:
            from yuho.cli.commands.library import run_library_tree
            stdout, stderr = capture_cli(run_library_tree, package=package, verbose=False)
            result = stdout.strip() or stderr.strip() or "[dim]No dependency tree.[/dim]"
            self.app.call_from_thread(output.write, result)
        except Exception as e:
            self.app.call_from_thread(output.write, f"[bold red]Error:[/] {e}")

    @work(thread=True)
    def _run_publish(self, path: str) -> None:
        output = self.query_one("#lib-output", RichLog)
        try:
            from yuho.cli.commands.library import run_library_publish
            stdout, stderr = capture_cli(run_library_publish, path, dry_run=True, verbose=False)
            result = stdout.strip() or stderr.strip() or "[green]Publish dry-run complete.[/green]"
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
        yield Static("")
        yield Static("[bold]Theme[/bold]")
        with Horizontal(classes="action-row"):
            yield Button("Toggle Dark/Light", id="btn-theme-toggle")
        yield Rule()
        with Horizontal(classes="action-row"):
            yield Button("Save Settings", id="btn-settings-save", variant="primary")
            yield Button("Reset Defaults", id="btn-settings-reset")
        yield Static("", id="settings-status")

    def on_mount(self) -> None:
        """Load existing config from ~/.config/yuho/config.toml if present."""
        try:
            from yuho.config.loader import get_config
            cfg = get_config().to_dict()
            llm = cfg.get("llm", {})
            transpile = cfg.get("transpile", {})
            if llm.get("provider"):
                self.query_one("#settings-llm-provider", Select).value = llm["provider"]
            if llm.get("model"):
                self.query_one("#settings-llm-model", Input).value = llm["model"]
            if transpile.get("default_target"):
                self.query_one("#settings-default-target", Select).value = transpile["default_target"]
        except Exception:
            pass

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

    @on(Button.Pressed, "#btn-theme-toggle")
    def handle_theme_toggle(self) -> None:
        self.app.dark = not self.app.dark
        mode = "dark" if self.app.dark else "light"
        self.query_one("#settings-status", Static).update(f"[dim]Theme: {mode}[/dim]")


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
        Binding("t", "toggle_dark", "Theme", show=True),
        Binding("1", "nav(0)", "Home", show=False),
        Binding("2", "nav(1)", "Check", show=False),
        Binding("3", "nav(2)", "Transpile", show=False),
        Binding("4", "nav(3)", "Eval", show=False),
        Binding("5", "nav(4)", "Wizard", show=False),
        Binding("6", "nav(5)", "REPL", show=False),
        Binding("7", "nav(6)", "Lint", show=False),
        Binding("8", "nav(7)", "Test", show=False),
        Binding("9", "nav(8)", "Format", show=False),
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
                yield EvalPanel(id="eval", classes="panel")
                yield WizardPanel(id="wizard", classes="panel")
                yield ReplPanel(id="repl", classes="panel")
                yield LintPanel(id="lint", classes="panel")
                yield TestPanel(id="test", classes="panel")
                yield FmtPanel(id="fmt", classes="panel")
                yield DiffPanel(id="diff", classes="panel")
                yield GraphPanel(id="graph", classes="panel")
                yield VerifyPanel(id="verify", classes="panel")
                yield ASTViewPanel(id="ast-view", classes="panel")
                yield ExplainPanel(id="explain", classes="panel")
                yield GeneratePanel(id="generate", classes="panel")
                yield InitPanel(id="init", classes="panel")
                yield ContributePanel(id="contribute", classes="panel")
                yield LibraryPanel(id="library", classes="panel")
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

    def _open_file_picker(self, target_input_id: str) -> None:
        """Open file picker and set result to target input."""
        def on_dismiss(path: str) -> None:
            if path:
                self.query_one(f"#{target_input_id}", Input).value = path
        self.push_screen(FilePickerScreen(), callback=on_dismiss)

    @on(Button.Pressed, "#btn-check-browse")
    def handle_check_browse(self) -> None:
        self._open_file_picker("check-path")

    @on(Button.Pressed, "#btn-transpile-browse")
    def handle_transpile_browse(self) -> None:
        self._open_file_picker("transpile-path")

    @on(Button.Pressed, "#btn-eval-browse")
    def handle_eval_browse(self) -> None:
        self._open_file_picker("eval-path")

    @on(Button.Pressed, "#btn-graph-browse")
    def handle_graph_browse(self) -> None:
        self._open_file_picker("graph-path")

    @on(Button.Pressed, "#btn-explain-browse")
    def handle_explain_browse(self) -> None:
        self._open_file_picker("explain-path")

    @on(Button.Pressed, "#btn-contribute-browse")
    def handle_contribute_browse(self) -> None:
        self._open_file_picker("contribute-path")

    @on(Button.Pressed, "#btn-open")
    def handle_open_file(self) -> None:
        self.action_nav(1)
        self._open_file_picker("check-path")

    @on(Button.Pressed, "#btn-wizard")
    def handle_new_wizard(self) -> None:
        self.action_nav(4)

    @on(Button.Pressed, "#btn-copy-output")
    def handle_copy_output(self) -> None:
        text = self.query_one("#transpile-output", TextArea).text
        if not text:
            self.notify("No output to copy.", severity="warning")
            return
        if _copy_to_clipboard(text):
            self.notify("Copied to clipboard.")
        else:
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
        if _copy_to_clipboard(text):
            self.notify("Copied to clipboard.")
        else:
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
