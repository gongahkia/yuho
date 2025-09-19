#!/usr/bin/env python3
"""
Yuho v3.0 REPL - Interactive shell for Yuho language
"""

import sys
import os
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init()

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from parser import YuhoParser
from semantic_analyzer import SemanticAnalyzer
from transpilers.mermaid_transpiler import MermaidTranspiler
from transpilers.alloy_transpiler import AlloyTranspiler

class YuhoREPL:
    """Interactive REPL for Yuho language"""

    def __init__(self):
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()
        self.mermaid_transpiler = MermaidTranspiler()
        self.alloy_transpiler = AlloyTranspiler()
        self.history = []

    def run(self):
        """Run the REPL"""
        print(f"{Fore.CYAN}Yuho v3.0 REPL{Style.RESET_ALL}")
        print(f"Type {Fore.YELLOW}'help'{Style.RESET_ALL} for commands, {Fore.YELLOW}'exit'{Style.RESET_ALL} to quit")
        print()

        while True:
            try:
                # Get input
                line = input(f"{Fore.GREEN}yuho> {Style.RESET_ALL}")
                line = line.strip()

                if not line:
                    continue

                # Handle special commands
                if line == 'exit' or line == 'quit':
                    print("Goodbye!")
                    break
                elif line == 'help':
                    self.show_help()
                    continue
                elif line == 'history':
                    self.show_history()
                    continue
                elif line == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    continue
                elif line.startswith('load '):
                    self.load_file(line[5:].strip())
                    continue
                elif line.startswith('mermaid'):
                    self.generate_mermaid()
                    continue
                elif line.startswith('alloy'):
                    self.generate_alloy()
                    continue

                # Try to parse as Yuho code
                try:
                    # Add to history
                    self.history.append(line)

                    # Parse the input
                    ast = self.parser.parse(line)

                    # Semantic analysis
                    errors = self.analyzer.analyze(ast)

                    if errors:
                        print(f"{Fore.RED}Semantic errors:{Style.RESET_ALL}")
                        for error in errors:
                            print(f"  {Fore.RED}ERROR: {error}{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.GREEN}✓ Valid Yuho code{Style.RESET_ALL}")

                        # Show AST structure
                        if ast.statements:
                            print(f"{Fore.CYAN}Parsed:{Style.RESET_ALL} {len(ast.statements)} statement(s)")

                except Exception as e:
                    print(f"{Fore.RED}Parse error: {str(e)}{Style.RESET_ALL}")

            except KeyboardInterrupt:
                print(f"\\n{Fore.YELLOW}Use 'exit' to quit{Style.RESET_ALL}")
            except EOFError:
                print("\\nGoodbye!")
                break

    def show_help(self):
        """Show REPL help"""
        help_text = f"""
{Fore.CYAN}Yuho REPL Commands:{Style.RESET_ALL}

{Fore.YELLOW}Special Commands:{Style.RESET_ALL}
  help          - Show this help
  exit, quit    - Exit the REPL
  history       - Show command history
  clear         - Clear screen
  load <file>   - Load and parse a Yuho file
  mermaid       - Generate Mermaid from last valid input
  alloy         - Generate Alloy from last valid input

{Fore.YELLOW}Yuho Syntax Examples:{Style.RESET_ALL}
  struct Person {{ name: string, age: int }}
  int x := 42;
  match {{ case x > 0 := consequence "positive"; }}

{Fore.YELLOW}Types:{Style.RESET_ALL}
  int, float, bool, string, percent, money, date, duration
"""
        print(help_text)

    def show_history(self):
        """Show command history"""
        if not self.history:
            print(f"{Fore.YELLOW}No history yet{Style.RESET_ALL}")
            return

        print(f"{Fore.CYAN}Command History:{Style.RESET_ALL}")
        for i, cmd in enumerate(self.history, 1):
            print(f"  {i:2d}: {cmd}")

    def load_file(self, filepath):
        """Load and parse a Yuho file"""
        try:
            if not os.path.exists(filepath):
                print(f"{Fore.RED}File not found: {filepath}{Style.RESET_ALL}")
                return

            ast = self.parser.parse_file(filepath)
            errors = self.analyzer.analyze(ast)

            if errors:
                print(f"{Fore.RED}Semantic errors in {filepath}:{Style.RESET_ALL}")
                for error in errors:
                    print(f"  {Fore.RED}ERROR: {error}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✓ Successfully loaded {filepath}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Statements: {len(ast.statements)}{Style.RESET_ALL}")

        except Exception as e:
            print(f"{Fore.RED}Error loading {filepath}: {str(e)}{Style.RESET_ALL}")

    def generate_mermaid(self):
        """Generate Mermaid from last valid AST"""
        if not self.history:
            print(f"{Fore.YELLOW}No code to convert{Style.RESET_ALL}")
            return

        try:
            # Try to parse last command
            last_code = self.history[-1]
            ast = self.parser.parse(last_code)

            flowchart = self.mermaid_transpiler.transpile_to_flowchart(ast)
            print(f"{Fore.CYAN}Mermaid Flowchart:{Style.RESET_ALL}")
            print(flowchart)

        except Exception as e:
            print(f"{Fore.RED}Error generating Mermaid: {str(e)}{Style.RESET_ALL}")

    def generate_alloy(self):
        """Generate Alloy from last valid AST"""
        if not self.history:
            print(f"{Fore.YELLOW}No code to convert{Style.RESET_ALL}")
            return

        try:
            # Try to parse last command
            last_code = self.history[-1]
            ast = self.parser.parse(last_code)

            alloy_spec = self.alloy_transpiler.transpile(ast)
            print(f"{Fore.CYAN}Alloy Specification:{Style.RESET_ALL}")
            print(alloy_spec)

        except Exception as e:
            print(f"{Fore.RED}Error generating Alloy: {str(e)}{Style.RESET_ALL}")

if __name__ == '__main__':
    repl = YuhoREPL()
    repl.run()