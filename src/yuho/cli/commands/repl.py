"""
REPL command - interactive statute experimentation.

Provides an interactive Read-Eval-Print Loop for:
- Parsing and validating Yuho code snippets
- Transpiling to various targets
- Exploring statute definitions
- Testing legal logic
- GDB-style interactive debugging
"""

import os
import sys
import readline
from pathlib import Path
from typing import Optional, List, Dict, Any

import click

from yuho.parser import get_parser
from yuho.ast import ASTBuilder
from yuho.ast.nodes import ModuleNode
from yuho.transpile.base import TranspileTarget
from yuho.transpile.registry import TranspilerRegistry
from yuho.eval.interpreter import Interpreter, Environment, Value, InterpreterError, AssertionError_
from yuho.eval.debugger import DebugInterpreter, DebuggerPause, StepMode, Breakpoint
from yuho.cli.error_formatter import format_errors, Colors, colorize


class YuhoREPL:
    """
    Interactive REPL for Yuho statute language.

    Supports:
    - Multi-line input with continuation
    - Command history (via readline)
    - Transpilation to any target
    - AST inspection
    - Statute exploration
    - GDB-style interactive debugging
    """

    PROMPT = "yuho> "
    CONTINUATION_PROMPT = "  ... "
    DEBUG_PROMPT = "(ydb) "

    COMMANDS = {
        "help": "Show this help message",
        "exit": "Exit the REPL (also: quit, Ctrl+D)",
        "clear": "Clear the screen",
        "history": "Show command history",
        "load <file>": "Load and parse a .yh file",
        "transpile <target>": "Transpile last valid input (json, english, mermaid, latex, graphql)",
        "ast": "Show AST of last valid input",
        "targets": "List available transpile targets",
        "eval": "Evaluate last parsed module using the interpreter",
        "env": "Show current interpreter environment bindings",
        "reset": "Clear session state",
        "break <line|fn>": "Set a breakpoint (alias: b)",
        "run": "Run last loaded file under the debugger (alias: r)",
        "info <what>": "Show info: locals, functions, statutes, breakpoints, watch",
        "delete <n>": "Delete breakpoint #n",
        "watch <var>": "Break when variable changes value",
        "unwatch <var>": "Remove a watchpoint",
    }

    DEBUG_COMMANDS = {
        "s / step": "Step into next statement",
        "n / next": "Step over (stay in current frame)",
        "c / continue": "Continue to next breakpoint",
        "finish": "Run until current function returns",
        "p / print <expr>": "Evaluate expression in current scope",
        "bt / backtrace": "Show call stack",
        "l / list": "Show source around current line",
        "info locals": "Show local variable bindings",
        "info functions": "Show defined functions",
        "info statutes": "Show loaded statutes",
        "info breakpoints": "Show all breakpoints",
        "info watch": "Show all watchpoints",
        "q / quit": "Abort debugging and return to REPL",
    }

    def __init__(self, color: bool = True, verbose: bool = False):
        self.color = color
        self.verbose = verbose
        self.parser = get_parser()
        self.registry = TranspilerRegistry.instance()

        # Session state
        self.history: List[str] = []
        self.last_ast: Optional[ModuleNode] = None
        self.last_source: str = ""
        self.last_file: str = "<repl>"
        self.session_statutes: Dict[str, Any] = {}
        # Persistent interpreter environment across REPL session
        self.interp_env = Environment()
        self.interpreter = Interpreter(self.interp_env)
        # Debug interpreter (shares env with normal interpreter)
        self.debugger = DebugInterpreter(self.interp_env)

        # Setup readline history
        self._setup_readline()

    def _setup_readline(self) -> None:
        """Wire up readline history; tolerate any read/write failure.

        macOS sandboxing, immutable filesystems (e.g. Nix store), and
        SELinux-restricted homedirs can all surface as PermissionError or
        OSError on either the read or the write path. None of those are
        fatal — the REPL just runs without persistent history.
        """
        history_file = Path.home() / ".yuho_history"
        try:
            readline.read_history_file(history_file)
        except (FileNotFoundError, PermissionError, OSError):
            pass
        import atexit

        def _write_history() -> None:
            try:
                readline.write_history_file(history_file)
            except (PermissionError, OSError):
                pass

        atexit.register(_write_history)
        readline.set_history_length(1000)

    def _colorize(self, text: str, color: str) -> str:
        if not self.color:
            return text
        return colorize(text, color)

    def _print_banner(self) -> None:
        banner = f"""
{self._colorize("Yuho REPL", Colors.CYAN)} - Interactive statute experimentation
Type {self._colorize("help", Colors.YELLOW)} for commands, {self._colorize("exit", Colors.YELLOW)} to quit
"""
        print(banner.strip())
        print()

    def _print_help(self) -> None:
        print(f"\n{self._colorize('Commands:', Colors.CYAN)}")
        for cmd, desc in self.COMMANDS.items():
            print(f"  {self._colorize(cmd, Colors.YELLOW):30s} {desc}")

        print(f"\n{self._colorize('Debugger Commands (inside debug session):', Colors.CYAN)}")
        for cmd, desc in self.DEBUG_COMMANDS.items():
            print(f"  {self._colorize(cmd, Colors.YELLOW):30s} {desc}")

        print(f"\n{self._colorize('Yuho Syntax Examples:', Colors.CYAN)}")
        examples = [
            'statute "299" "Culpable Homicide" { ... }',
            "struct Person { name: string, age: int }",
            "fn is_adult(age: int) -> bool { return age >= 18; }",
        ]
        for ex in examples:
            print(f"  {ex}")

        print(f"\n{self._colorize('Multi-line Input:', Colors.CYAN)}")
        print("  End a line with \\ to continue on the next line")
        print("  Or use matching braces { } for blocks")
        print()

    def _print_targets(self) -> None:
        print(f"\n{self._colorize('Available Targets:', Colors.CYAN)}")
        for target in TranspileTarget:
            name = target.name.lower()
            ext = target.file_extension
            print(f"  {self._colorize(name, Colors.YELLOW):12s} -> {ext}")
        print()

    def _read_input(self) -> Optional[str]:
        lines: List[str] = []
        prompt = self.PROMPT
        brace_depth = 0

        while True:
            try:
                line = input(self._colorize(prompt, Colors.GREEN))
            except EOFError:
                if lines:
                    print()
                return None
            except KeyboardInterrupt:
                print(f"\n{self._colorize('(Use exit to quit)', Colors.YELLOW)}")
                return ""

            brace_depth += line.count("{") - line.count("}")

            if line.endswith("\\"):
                lines.append(line[:-1])
                prompt = self.CONTINUATION_PROMPT
                continue

            lines.append(line)

            if brace_depth > 0:
                prompt = self.CONTINUATION_PROMPT
                continue

            break

        return "\n".join(lines)

    def _handle_command(self, cmd: str) -> bool:
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if command in ("exit", "quit"):
            print("Goodbye!")
            return True

        if command == "help":
            self._print_help()
            return False

        if command == "clear":
            import subprocess

            subprocess.run(["clear" if os.name == "posix" else "cls"], shell=False, check=False)
            return False

        if command == "history":
            if not self.history:
                print(self._colorize("No history yet", Colors.YELLOW))
            else:
                print(f"\n{self._colorize('History:', Colors.CYAN)}")
                for i, h in enumerate(self.history[-20:], 1):
                    preview = h[:60] + "..." if len(h) > 60 else h
                    print(f"  {i:2d}: {preview}")
            print()
            return False

        if command == "targets":
            self._print_targets()
            return False

        if command == "reset":
            self.last_ast = None
            self.last_source = ""
            self.last_file = "<repl>"
            self.session_statutes.clear()
            self.interp_env = Environment()
            self.interpreter = Interpreter(self.interp_env)
            self.debugger = DebugInterpreter(self.interp_env)
            print(self._colorize("Session state cleared", Colors.GREEN))
            return False

        if command == "ast":
            if not self.last_ast:
                print(
                    self._colorize("No valid AST available. Parse some code first.", Colors.YELLOW)
                )
            else:
                self._print_ast(self.last_ast)
            return False

        if command == "load":
            if not arg:
                print(self._colorize("Usage: load <file.yh>", Colors.RED))
            else:
                self._load_file(arg)
            return False

        if command == "transpile":
            if not arg:
                print(self._colorize("Usage: transpile <target>", Colors.RED))
                self._print_targets()
            else:
                self._transpile(arg)
            return False

        if command == "eval":
            self._eval_last_ast()
            return False

        if command == "env":
            self._print_env()
            return False

        # -- debugger commands (outside debug session) ----------------------

        if command in ("break", "b"):
            self._cmd_break(arg)
            return False

        if command in ("run", "r"):
            self._cmd_run()
            return False

        if command == "delete":
            self._cmd_delete(arg)
            return False

        if command == "info":
            self._cmd_info(arg)
            return False

        if command == "watch":
            self._cmd_watch(arg)
            return False

        if command == "unwatch":
            self._cmd_unwatch(arg)
            return False

        # Unknown command - try parsing as code
        return False

    # ======================================================================
    # File loading
    # ======================================================================

    def _load_file(self, filepath: str) -> None:
        from yuho.parser.wrapper import validate_file_path

        try:
            path = validate_file_path(Path(filepath).expanduser())
        except (ValueError, FileNotFoundError) as e:
            print(self._colorize(f"Error: {e}", Colors.RED))
            return
        try:
            source = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError, OSError) as e:
            print(self._colorize(f"Error reading file: {e}", Colors.RED))
            return
        if "\x00" in source:
            print(self._colorize("Error: file contains null bytes (binary file?)", Colors.RED))
            return
        self.last_file = str(path)
        self._parse_and_validate(source, str(path))

    def _parse_and_validate(self, source: str, filename: str = "<repl>") -> bool:
        result = self.parser.parse(source, filename)

        if result.errors:
            print(self._colorize("Parse errors:", Colors.RED))
            for err in result.errors[:5]:
                loc = f"{err.location.line}:{err.location.col}" if err.location else "?"
                print(f"  [{loc}] {err.message}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more errors")
            return False

        try:
            if result.root_node is None:
                print(self._colorize("Parser returned no root node.", Colors.RED))
                return False
            builder = ASTBuilder(source, filename)
            ast = builder.build(result.root_node)

            self.last_ast = ast
            self.last_source = source
            self.last_file = filename

            for statute in ast.statutes:
                self.session_statutes[statute.section_number] = statute

            # Cache source in debugger for 'list' command
            self.debugger.load_source(filename, source)

            stats = []
            if ast.statutes:
                stats.append(f"{len(ast.statutes)} statute(s)")
            if ast.type_defs:
                stats.append(f"{len(ast.type_defs)} type(s)")
            if ast.function_defs:
                stats.append(f"{len(ast.function_defs)} function(s)")

            if stats:
                print(self._colorize(f"✓ Parsed: {', '.join(stats)}", Colors.GREEN))
            else:
                print(self._colorize("✓ Valid (empty module)", Colors.GREEN))

            return True

        except Exception as e:
            print(self._colorize(f"AST build error: {e}", Colors.RED))
            if self.verbose:
                import traceback

                traceback.print_exc()
            return False

    # ======================================================================
    # Transpilation
    # ======================================================================

    def _transpile(self, target_name: str) -> None:
        if not self.last_ast:
            print(self._colorize("No valid AST available. Parse some code first.", Colors.YELLOW))
            return
        try:
            target = TranspileTarget.from_string(target_name)
        except ValueError:
            print(self._colorize(f"Unknown target: {target_name}", Colors.RED))
            self._print_targets()
            return
        try:
            transpiler = self.registry.get(target)
            output = transpiler.transpile(self.last_ast)
            print(f"\n{self._colorize(f'=== {target.name} Output ===', Colors.CYAN)}")
            print(output)
            print()
        except Exception as e:
            print(self._colorize(f"Transpilation error: {e}", Colors.RED))
            if self.verbose:
                import traceback

                traceback.print_exc()

    # ======================================================================
    # Eval (non-debug)
    # ======================================================================

    def _eval_last_ast(self) -> None:
        if not self.last_ast:
            print(self._colorize("No valid AST available. Parse some code first.", Colors.YELLOW))
            return
        try:
            self.interpreter.interpret(self.last_ast)
            bindings = self.interp_env.bindings
            structs = self.interp_env.struct_defs
            funcs = self.interp_env.function_defs
            stats: List[str] = []
            if bindings:
                stats.append(f"{len(bindings)} binding(s)")
            if structs:
                stats.append(f"{len(structs)} struct(s)")
            if funcs:
                stats.append(f"{len(funcs)} function(s)")
            if self.interp_env.statutes:
                stats.append(f"{len(self.interp_env.statutes)} statute(s)")
            msg = ", ".join(stats) if stats else "no definitions"
            print(self._colorize(f"Evaluated: {msg}", Colors.GREEN))
        except AssertionError_ as e:
            print(self._colorize(f"Assertion failed: {e}", Colors.RED))
        except InterpreterError as e:
            print(self._colorize(f"Runtime error: {e}", Colors.RED))
        except Exception as e:
            print(self._colorize(f"Error: {e}", Colors.RED))
            if self.verbose:
                import traceback

                traceback.print_exc()

    # ======================================================================
    # Environment display
    # ======================================================================

    def _print_env(self) -> None:
        if (
            not self.interp_env.bindings
            and not self.interp_env.struct_defs
            and not self.interp_env.function_defs
        ):
            print(
                self._colorize(
                    "Environment is empty. Use 'eval' after parsing code.", Colors.YELLOW
                )
            )
            return
        print(f"\n{self._colorize('=== Environment ===', Colors.CYAN)}")
        if self.interp_env.struct_defs:
            print(f"Structs: {', '.join(self.interp_env.struct_defs.keys())}")
        if self.interp_env.function_defs:
            print(f"Functions: {', '.join(self.interp_env.function_defs.keys())}")
        if self.interp_env.statutes:
            print(f"Statutes: {', '.join(self.interp_env.statutes.keys())}")
        if self.interp_env.bindings:
            print("Bindings:")
            for name, val in self.interp_env.bindings.items():
                print(f"  {name} = {val.raw!r} ({val.type_tag})")
        print()

    def _print_ast(self, ast: ModuleNode) -> None:
        print(f"\n{self._colorize('=== AST ===', Colors.CYAN)}")
        if ast.imports:
            print(f"Imports: {len(ast.imports)}")
            for imp in ast.imports:
                print(f"  - {imp.path}")
        if ast.type_defs:
            print(f"Types: {len(ast.type_defs)}")
            for td in ast.type_defs:
                fields = ", ".join(f.name for f in td.fields)
                print(f"  - struct {td.name} {{ {fields} }}")
        if ast.function_defs:
            print(f"Functions: {len(ast.function_defs)}")
            for fn in ast.function_defs:
                params = ", ".join(p.name for p in fn.params)
                print(f"  - fn {fn.name}({params})")
        if ast.statutes:
            print(f"Statutes: {len(ast.statutes)}")
            for st in ast.statutes:
                title = st.title.value if st.title else "(untitled)"
                print(f"  - Section {st.section_number}: {title}")
                if st.elements:
                    print(f"      Elements: {len(st.elements)}")
                if st.penalty:
                    print(f"      Has penalty")
                if st.illustrations:
                    print(f"      Illustrations: {len(st.illustrations)}")
        print()

    # ======================================================================
    # Debugger commands (outside debug session)
    # ======================================================================

    def _cmd_break(self, arg: str) -> None:
        """Set a breakpoint: 'break 10', 'break myFunction', 'break 10 if x > 3'."""
        if not arg:
            print(self._colorize("Usage: break <line|function> [if <condition>]", Colors.RED))
            return

        condition = ""
        if " if " in arg:
            arg, condition = arg.split(" if ", 1)
            arg = arg.strip()
            condition = condition.strip()

        arg = arg.strip()
        try:
            line = int(arg)
            bp = self.debugger.add_breakpoint(line=line, file=self.last_file, condition=condition)
            print(self._colorize(f"Breakpoint {bp}", Colors.GREEN))
        except ValueError:
            bp = self.debugger.add_breakpoint(function=arg, condition=condition)
            print(self._colorize(f"Breakpoint {bp}", Colors.GREEN))

    def _cmd_delete(self, arg: str) -> None:
        if not arg:
            print(self._colorize("Usage: delete <breakpoint-id>", Colors.RED))
            return
        try:
            bp_id = int(arg)
        except ValueError:
            print(self._colorize(f"Invalid breakpoint id: {arg}", Colors.RED))
            return
        if self.debugger.delete_breakpoint(bp_id):
            print(self._colorize(f"Deleted breakpoint #{bp_id}", Colors.GREEN))
        else:
            print(self._colorize(f"No breakpoint #{bp_id}", Colors.RED))

    def _cmd_watch(self, arg: str) -> None:
        if not arg:
            print(self._colorize("Usage: watch <variable>", Colors.RED))
            return
        self.debugger.add_watch(arg.strip())
        print(self._colorize(f"Watching: {arg.strip()}", Colors.GREEN))

    def _cmd_unwatch(self, arg: str) -> None:
        if not arg:
            print(self._colorize("Usage: unwatch <variable>", Colors.RED))
            return
        name = arg.strip()
        if self.debugger.remove_watch(name):
            print(self._colorize(f"Removed watchpoint: {name}", Colors.GREEN))
        else:
            print(self._colorize(f"No watchpoint on: {name}", Colors.RED))

    def _cmd_info(self, arg: str) -> None:
        what = arg.strip().lower()
        if what == "breakpoints":
            if not self.debugger.breakpoints:
                print(self._colorize("No breakpoints set.", Colors.YELLOW))
            else:
                print(f"\n{self._colorize('Breakpoints:', Colors.CYAN)}")
                for bp in self.debugger.breakpoints:
                    status = (
                        self._colorize("on", Colors.GREEN)
                        if bp.enabled
                        else self._colorize("off", Colors.RED)
                    )
                    print(f"  {bp}  [{status}]")
            return

        if what == "watch":
            if not self.debugger._watchpoints:
                print(self._colorize("No watchpoints set.", Colors.YELLOW))
            else:
                print(f"\n{self._colorize('Watchpoints:', Colors.CYAN)}")
                for name, val in self.debugger._watchpoints.items():
                    v = repr(val.raw) if val else "undefined"
                    print(f"  {name} = {v}")
            return

        if what == "locals":
            bindings = self.debugger.get_locals()
            if not bindings:
                print(self._colorize("No local bindings.", Colors.YELLOW))
            else:
                print(f"\n{self._colorize('Local bindings:', Colors.CYAN)}")
                for name, val in bindings.items():
                    print(f"  {name} = {val.raw!r} ({val.type_tag})")
            return

        if what == "functions":
            fns = self.debugger.env.function_defs
            if not fns:
                fns = self.interp_env.function_defs
            if not fns:
                print(self._colorize("No functions defined.", Colors.YELLOW))
            else:
                print(f"\n{self._colorize('Functions:', Colors.CYAN)}")
                for name, fn_def in fns.items():
                    params = ", ".join(p.name for p in fn_def.params)
                    loc = ""
                    if fn_def.source_location:
                        loc = f" at {fn_def.source_location.line}"
                    print(f"  fn {name}({params}){loc}")
            return

        if what == "statutes":
            stats = self.debugger.env.statutes
            if not stats:
                stats = self.interp_env.statutes
            if not stats:
                print(self._colorize("No statutes loaded.", Colors.YELLOW))
            else:
                print(f"\n{self._colorize('Statutes:', Colors.CYAN)}")
                for sec, st in stats.items():
                    title = st.title.value if st.title else "(untitled)"
                    print(f"  s{sec}: {title}")
                    if st.elements:
                        for elem in st.elements:
                            etype = getattr(elem, "element_type", "")
                            ename = getattr(elem, "name", "")
                            if etype and ename:
                                print(f"    {etype} {ename}")
            return

        print(
            self._colorize("Usage: info <locals|functions|statutes|breakpoints|watch>", Colors.RED)
        )

    # ======================================================================
    # Debugger: run & interactive debug loop
    # ======================================================================

    def _cmd_run(self) -> None:
        """Run last parsed AST under the debugger."""
        if not self.last_ast:
            print(self._colorize("No valid AST available. Load a file first.", Colors.YELLOW))
            return

        # Reset debugger state for a fresh run
        self.debugger.env = Environment()
        self.interp_env = self.debugger.env
        self.debugger.call_stack.clear()
        self.debugger.mode = StepMode.RUN
        self.debugger._last_listed_line = 0

        if self.last_source:
            self.debugger.load_source(self.last_file, self.last_source)

        has_bp = bool(self.debugger.breakpoints) or bool(self.debugger._watchpoints)
        if has_bp:
            print(
                self._colorize(
                    f"Starting with {len(self.debugger.breakpoints)} breakpoint(s), "
                    f"{len(self.debugger._watchpoints)} watchpoint(s)",
                    Colors.CYAN,
                )
            )
        else:
            # No breakpoints -- start in STEP mode so user can interact
            self.debugger.mode = StepMode.STEP
            print(self._colorize("No breakpoints set -- starting in step mode.", Colors.CYAN))

        self._run_debug_loop()

    def _run_debug_loop(self) -> None:
        """Execute the AST, pausing at breakpoints/steps for user commands."""
        if self.last_ast is None:
            print(self._colorize("No program loaded for debugging.", Colors.RED))
            return
        try:
            self.debugger.interpret(self.last_ast)
            # Finished without pause
            print(self._colorize("Program finished.", Colors.GREEN))
        except DebuggerPause as dp:
            self._show_pause_location(dp)
            self._debug_interactive(dp)
        except AssertionError_ as e:
            print(self._colorize(f"ASSERTION FAILED: {e}", Colors.RED))
        except InterpreterError as e:
            print(self._colorize(f"Runtime error: {e}", Colors.RED))
        except Exception as e:
            print(self._colorize(f"Error: {e}", Colors.RED))
            if self.verbose:
                import traceback

                traceback.print_exc()

    def _show_pause_location(self, dp: DebuggerPause) -> None:
        """Display the source location where we paused."""
        node = dp.node
        reason = dp.reason
        line = node.source_location.line if node.source_location else 0
        file = node.source_location.file if node.source_location else self.last_file
        col = node.source_location.col if node.source_location else 0

        print(self._colorize(f"\n[{reason}]", Colors.YELLOW), end=" ")
        if self.debugger.call_stack:
            frame = self.debugger.call_stack[-1]
            print(self._colorize(f"in {frame.function_name}()", Colors.CYAN), end=" ")
        print(f"at {file}:{line}:{col}")

        # Show the current source line
        src_lines = self.debugger.get_source_lines(file, line, radius=2)
        for ln, text, is_cur in src_lines:
            marker = self._colorize("=>", Colors.GREEN) if is_cur else "  "
            num = self._colorize(f"{ln:4d}", Colors.DIM)
            print(f" {marker} {num}  {text}")
        self.debugger._last_listed_line = line

    def _debug_interactive(self, dp: DebuggerPause) -> None:
        """Interactive debugger command loop. Runs until user continues or quits."""
        while True:
            try:
                cmd = input(self._colorize(self.DEBUG_PROMPT, Colors.YELLOW)).strip()
            except (EOFError, KeyboardInterrupt):
                print(self._colorize("\nDebug session ended.", Colors.YELLOW))
                return

            if not cmd:
                continue

            parts = cmd.split(maxsplit=1)
            verb = parts[0].lower()
            arg = parts[1].strip() if len(parts) > 1 else ""

            # -- stepping commands (resume execution) -----------------------
            if verb in ("s", "step"):
                self.debugger.mode = StepMode.STEP
                self._resume_after_pause(dp)
                return

            if verb in ("n", "next"):
                self.debugger.mode = StepMode.NEXT
                self.debugger._step_frame_depth = len(self.debugger.call_stack)
                self._resume_after_pause(dp)
                return

            if verb in ("c", "continue"):
                self.debugger.mode = (
                    StepMode.CONTINUE if self.debugger.breakpoints else StepMode.RUN
                )
                self._resume_after_pause(dp)
                return

            if verb == "finish":
                self.debugger.mode = StepMode.FINISH
                self.debugger._step_frame_depth = len(self.debugger.call_stack)
                self._resume_after_pause(dp)
                return

            # -- inspection commands (stay paused) --------------------------
            if verb in ("p", "print"):
                self._dbg_print(arg)
                continue

            if verb in ("bt", "backtrace"):
                self._dbg_backtrace()
                continue

            if verb in ("l", "list"):
                self._dbg_list(arg)
                continue

            if verb == "info":
                self._cmd_info(arg)
                continue

            if verb in ("b", "break"):
                self._cmd_break(arg)
                continue

            if verb == "delete":
                self._cmd_delete(arg)
                continue

            if verb == "watch":
                self._cmd_watch(arg)
                continue

            if verb == "unwatch":
                self._cmd_unwatch(arg)
                continue

            if verb in ("q", "quit"):
                print(self._colorize("Debug session aborted.", Colors.YELLOW))
                return

            if verb == "help":
                print(f"\n{self._colorize('Debugger Commands:', Colors.CYAN)}")
                for c, d in self.DEBUG_COMMANDS.items():
                    print(f"  {self._colorize(c, Colors.YELLOW):30s} {d}")
                print()
                continue

            print(self._colorize(f"Unknown command: {verb}. Type 'help' for commands.", Colors.RED))

    def _resume_after_pause(self, dp: DebuggerPause) -> None:
        """Continue execution from where we paused.

        We re-run ``interpret()`` but the debugger's internal state (env,
        call_stack, breakpoints) has already been set, so it will continue
        from the next steppable node.  Because ``DebuggerPause`` aborts
        the current visit chain via exception, we need to re-interpret
        the module.  To avoid re-executing already-completed top-level
        definitions, we mark them as done.

        A cleaner approach is to use a coroutine / continuation, but
        re-interpretation is simpler and sufficient for a REPL debugger.
        """
        if self.last_ast is None:
            print(self._colorize("No program loaded for debugging.", Colors.RED))
            return
        try:
            self.debugger.interpret(self.last_ast)
            print(self._colorize("Program finished.", Colors.GREEN))
        except DebuggerPause as new_dp:
            self._show_pause_location(new_dp)
            self._debug_interactive(new_dp)
        except AssertionError_ as e:
            print(self._colorize(f"ASSERTION FAILED: {e}", Colors.RED))
        except InterpreterError as e:
            print(self._colorize(f"Runtime error: {e}", Colors.RED))
        except Exception as e:
            print(self._colorize(f"Error: {e}", Colors.RED))
            if self.verbose:
                import traceback

                traceback.print_exc()

    def _dbg_print(self, expr: str) -> None:
        if not expr:
            print(self._colorize("Usage: print <expression>", Colors.RED))
            return
        try:
            val = self.debugger.eval_expr(expr)
            print(f"  {self._colorize(expr, Colors.CYAN)} = {val.raw!r} ({val.type_tag})")
        except (InterpreterError, Exception) as e:
            print(self._colorize(f"  Error: {e}", Colors.RED))

    def _dbg_backtrace(self) -> None:
        if not self.debugger.call_stack:
            print(self._colorize("  (at top level)", Colors.DIM))
            return
        print(f"\n{self._colorize('Call stack:', Colors.CYAN)}")
        for i, frame in enumerate(reversed(self.debugger.call_stack)):
            marker = self._colorize("#" + str(i), Colors.YELLOW)
            print(f"  {marker} {frame}")
        print()

    def _dbg_list(self, arg: str) -> None:
        """Show source around current (or specified) line."""
        node = self.debugger._paused_node
        file = node.source_location.file if node and node.source_location else self.last_file

        if arg:
            try:
                center = int(arg)
            except ValueError:
                print(self._colorize(f"Usage: list [line]", Colors.RED))
                return
        elif self.debugger._last_listed_line:
            center = self.debugger._last_listed_line + 10
        elif node and node.source_location:
            center = node.source_location.line
        else:
            center = 1

        src_lines = self.debugger.get_source_lines(file, center, radius=5)
        if not src_lines:
            print(self._colorize("(no source available)", Colors.YELLOW))
            return

        cur_line = node.source_location.line if node and node.source_location else -1
        for ln, text, _ in src_lines:
            marker = self._colorize("=>", Colors.GREEN) if ln == cur_line else "  "
            num = self._colorize(f"{ln:4d}", Colors.DIM)
            print(f" {marker} {num}  {text}")
        self.debugger._last_listed_line = center

    # ======================================================================
    # Main loop
    # ======================================================================

    def run(self) -> int:
        self._print_banner()

        while True:
            try:
                source = self._read_input()

                if source is None:
                    print("\nGoodbye!")
                    break

                if not source.strip():
                    continue
                if len(source) > 1_000_000:
                    print(self._colorize("Input too large (max 1MB)", Colors.RED))
                    continue
                self.history.append(source)

                # Check if it's a command
                first_word = source.split()[0].lower()
                known_commands = [
                    "help",
                    "exit",
                    "quit",
                    "clear",
                    "history",
                    "load",
                    "transpile",
                    "ast",
                    "targets",
                    "eval",
                    "env",
                    "reset",
                    "break",
                    "b",
                    "run",
                    "r",
                    "delete",
                    "info",
                    "watch",
                    "unwatch",
                ]
                if first_word in known_commands:
                    if self._handle_command(source):
                        break
                    continue

                # Try to parse as Yuho code
                self._parse_and_validate(source)

            except KeyboardInterrupt:
                print(f"\n{self._colorize('(Use exit to quit)', Colors.YELLOW)}")
                continue
            except Exception as e:
                print(self._colorize(f"Error: {e}", Colors.RED))
                if self.verbose:
                    import traceback

                    traceback.print_exc()

        return 0


def run_repl(color: bool = True, verbose: bool = False) -> int:
    """
    Entry point for the REPL command.

    Args:
        color: Whether to use colored output
        verbose: Enable verbose mode

    Returns:
        Exit code
    """
    repl = YuhoREPL(color=color, verbose=verbose)
    return repl.run()
