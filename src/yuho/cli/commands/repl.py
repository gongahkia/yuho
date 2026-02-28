"""
REPL command - interactive statute experimentation.

Provides an interactive Read-Eval-Print Loop for:
- Parsing and validating Yuho code snippets
- Transpiling to various targets
- Exploring statute definitions
- Testing legal logic
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
    """

    PROMPT = "yuho> "
    CONTINUATION_PROMPT = "  ... "
    
    COMMANDS = {
        "help": "Show this help message",
        "exit": "Exit the REPL (also: quit, Ctrl+D)",
        "clear": "Clear the screen",
        "history": "Show command history",
        "load <file>": "Load and parse a .yh file",
        "transpile <target>": "Transpile last valid input (json, english, mermaid, latex, graphql)",
        "ast": "Show AST of last valid input",
        "targets": "List available transpile targets",
        "reset": "Clear session state",
    }

    def __init__(self, color: bool = True, verbose: bool = False):
        """
        Initialize the REPL.
        
        Args:
            color: Whether to use colored output
            verbose: Enable verbose mode
        """
        self.color = color
        self.verbose = verbose
        self.parser = get_parser()
        self.registry = TranspilerRegistry.instance()
        
        # Session state
        self.history: List[str] = []
        self.last_ast: Optional[ModuleNode] = None
        self.last_source: str = ""
        self.session_statutes: Dict[str, Any] = {}
        
        # Setup readline history
        self._setup_readline()

    def _setup_readline(self) -> None:
        """Configure readline for history and completion."""
        # History file
        history_file = Path.home() / ".yuho_history"
        try:
            readline.read_history_file(history_file)
        except FileNotFoundError:
            pass
        
        # Save history on exit
        import atexit
        atexit.register(lambda: readline.write_history_file(history_file))
        
        # Set history length
        readline.set_history_length(1000)

    def _colorize(self, text: str, color: str) -> str:
        """Apply color if enabled."""
        if not self.color:
            return text
        return colorize(text, color)

    def _print_banner(self) -> None:
        """Print welcome banner."""
        banner = f"""
{self._colorize("Yuho REPL", Colors.CYAN)} - Interactive statute experimentation
Type {self._colorize("help", Colors.YELLOW)} for commands, {self._colorize("exit", Colors.YELLOW)} to quit
"""
        print(banner.strip())
        print()

    def _print_help(self) -> None:
        """Print help message."""
        print(f"\n{self._colorize('Commands:', Colors.CYAN)}")
        for cmd, desc in self.COMMANDS.items():
            print(f"  {self._colorize(cmd, Colors.YELLOW):20s} {desc}")
        
        print(f"\n{self._colorize('Yuho Syntax Examples:', Colors.CYAN)}")
        examples = [
            'statute "299" "Culpable Homicide" { ... }',
            'struct Person { name: string, age: int }',
            'fn is_adult(age: int) -> bool { return age >= 18; }',
        ]
        for ex in examples:
            print(f"  {ex}")
        
        print(f"\n{self._colorize('Multi-line Input:', Colors.CYAN)}")
        print("  End a line with \\ to continue on the next line")
        print("  Or use matching braces { } for blocks")
        print()

    def _print_targets(self) -> None:
        """Print available transpile targets."""
        print(f"\n{self._colorize('Available Targets:', Colors.CYAN)}")
        for target in TranspileTarget:
            name = target.name.lower()
            ext = target.file_extension
            print(f"  {self._colorize(name, Colors.YELLOW):12s} -> {ext}")
        print()

    def _read_input(self) -> Optional[str]:
        """
        Read input, handling multi-line continuation.
        
        Returns:
            Complete input string, or None on EOF
        """
        lines: List[str] = []
        prompt = self.PROMPT
        brace_depth = 0
        
        while True:
            try:
                line = input(self._colorize(prompt, Colors.GREEN))
            except EOFError:
                if lines:
                    print()  # Newline after incomplete input
                return None
            except KeyboardInterrupt:
                print(f"\n{self._colorize('(Use exit to quit)', Colors.YELLOW)}")
                return ""
            
            # Track brace depth for multi-line blocks
            brace_depth += line.count("{") - line.count("}")
            
            # Check for line continuation
            if line.endswith("\\"):
                lines.append(line[:-1])
                prompt = self.CONTINUATION_PROMPT
                continue
            
            lines.append(line)
            
            # Continue if braces are unbalanced
            if brace_depth > 0:
                prompt = self.CONTINUATION_PROMPT
                continue
            
            break
        
        return "\n".join(lines)

    def _handle_command(self, cmd: str) -> bool:
        """
        Handle a REPL command.
        
        Args:
            cmd: The command string (without leading colon)
            
        Returns:
            True if command was handled, False otherwise
        """
        parts = cmd.strip().split(maxsplit=1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        
        if command in ("exit", "quit"):
            print("Goodbye!")
            return True  # Signal exit
        
        if command == "help":
            self._print_help()
            return False
        
        if command == "clear":
            os.system("clear" if os.name == "posix" else "cls")
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
            self.session_statutes.clear()
            print(self._colorize("Session state cleared", Colors.GREEN))
            return False
        
        if command == "ast":
            if not self.last_ast:
                print(self._colorize("No valid AST available. Parse some code first.", Colors.YELLOW))
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
        
        # Unknown command - try parsing as code
        return False

    def _load_file(self, filepath: str) -> None:
        """Load and parse a Yuho file."""
        path = Path(filepath).expanduser()
        
        if not path.exists():
            print(self._colorize(f"File not found: {filepath}", Colors.RED))
            return
        
        try:
            source = path.read_text(encoding="utf-8")
            self._parse_and_validate(source, str(path))
        except Exception as e:
            print(self._colorize(f"Error loading file: {e}", Colors.RED))

    def _parse_and_validate(self, source: str, filename: str = "<repl>") -> bool:
        """
        Parse and validate Yuho source code.
        
        Args:
            source: The source code
            filename: Filename for error messages
            
        Returns:
            True if parsing succeeded
        """
        result = self.parser.parse(source, filename)
        
        if result.errors:
            print(self._colorize("Parse errors:", Colors.RED))
            for err in result.errors[:5]:  # Limit to 5 errors
                loc = f"{err.location.line}:{err.location.col}" if err.location else "?"
                print(f"  [{loc}] {err.message}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more errors")
            return False
        
        # Build AST
        try:
            builder = ASTBuilder(source, filename)
            ast = builder.build(result.tree.root_node)
            
            self.last_ast = ast
            self.last_source = source
            
            # Track statutes in session
            for statute in ast.statutes:
                self.session_statutes[statute.section_number] = statute
            
            # Success message
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

    def _transpile(self, target_name: str) -> None:
        """Transpile last valid AST to a target format."""
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

    def _print_ast(self, ast: ModuleNode) -> None:
        """Print a simple representation of the AST."""
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

    def run(self) -> int:
        """
        Run the REPL loop.
        
        Returns:
            Exit code (0 for success)
        """
        self._print_banner()
        
        while True:
            try:
                source = self._read_input()
                
                if source is None:
                    # EOF
                    print("\nGoodbye!")
                    break
                
                if not source.strip():
                    continue
                
                # Add to history
                self.history.append(source)
                
                # Check if it's a command
                if source.strip() in self.COMMANDS or source.split()[0] in [
                    "help", "exit", "quit", "clear", "history", "load",
                    "transpile", "ast", "targets", "reset"
                ]:
                    if self._handle_command(source):
                        break  # Exit command
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
