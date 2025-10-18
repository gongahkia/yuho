# Frequently Asked Questions

Common questions about Yuho and their answers.

## General Questions

### What is Yuho?

Yuho is a domain-specific language (DSL) designed specifically for representing legal statutes and reasoning patterns in code. It helps law students and legal professionals better understand complex legal logic by providing a programmatic representation.

### Why "Yuho"?

The name reflects the goal of making legal reasoning clear and understandable - helping users say "Yuho!" (like "Eureka!") when they finally grasp complex legal concepts.

### Who should use Yuho?

- **Law students** learning statutory interpretation
- **Legal educators** teaching legal reasoning
- **Legal professionals** working with Singapore Criminal Law
- **Legal tech developers** building tools for legal analysis

### Is Yuho production-ready?

Yes! Yuho v3.0 is production-ready with:
- Comprehensive testing (234+ tests)
- Docker containerization
- CI/CD pipeline
- Full documentation
- Type safety and error handling

---

## Installation & Setup

### How do I install Yuho?

```bash
# From source (recommended)
git clone https://github.com/gongahkia/yuho.git
cd yuho
pip install -e .

# Or with Docker
docker pull yuho:latest
```

See [Installation Guide](../getting-started/installation.md) for details.

### What are the requirements?

- Python 3.8 or higher
- pip package manager
- Optional: Docker for containerized usage

### Can I use Yuho on Windows?

Yes! Yuho works on Windows, macOS, and Linux. Install Python 3.8+ and follow the installation instructions.

### Why am I getting "command not found" errors?

Ensure Python's scripts directory is in your PATH:
```bash
# Check installation
which yuho
yuho --version

# If not found, reinstall
pip install -e . --force-reinstall
```

---

## Language Questions

### Is Yuho Turing-complete?

No, and by design! Yuho intentionally lacks:
- Loops (no `for`, `while`)
- Recursion (limited)
- Side effects

This reflects the nature of legal statutes, which don't contain loops or recursive definitions.

### Why no loops?

Legal statutes don't iterate or loop. They define fixed conditions and consequences. Yuho's design mirrors this structure.

### Why immutability?

Immutability reflects the fixed nature of legal statutes - once defined, statutory elements don't change within a single analysis.

### Can I use Yuho for contract law?

Currently, Yuho is focused on Singapore Criminal Law, but the principles can be applied to any statute-based legal system. Contract law support may be added in future versions.

### What about case law?

Yuho currently focuses on statutes rather than case law. Adding case law precedent support is on the roadmap.

---

## Syntax Questions

### Why `:=` instead of `=`?

The `:=` operator makes variable binding explicit and distinguishes it from comparison (`==`). This is common in functional languages and mathematical notation.

### Why match-case instead of if-else?

Match-case ensures complete coverage of all possibilities (through the `_` wildcard), mirroring legal reasoning where all cases must be considered.

### Can I have optional fields in structs?

Not yet, but union types are on the roadmap. Currently, use union types like:
```yh
pass || money optionalAmount := pass
```

### Why are there so few data structures?

Simplicity! Yuho intentionally provides only structs, which can represent arrays, tuples, dictionaries, and enums. This reduces cognitive load for legal professionals learning to code.

---

## Usage Questions

### How do I check my Yuho code?

```bash
yuho check file.yh
```

This validates both syntax and semantics.

### How do I generate diagrams?

```bash
# Flowchart
yuho draw file.yh --format flowchart -o diagram.mmd

# Mindmap
yuho draw file.yh --format mindmap -o mindmap.mmd
```

### Can I use Yuho in my IDE?

Basic syntax highlighting is available. LSP (Language Server Protocol) support is planned for future releases.

Current editor support:
- Vim: Basic highlighting available
- VS Code: Extension in development
- Emacs: Configuration available

### How do I view Mermaid diagrams?

Options:
1. **Mermaid Live Editor**: https://mermaid.live
2. **VS Code**: Install Mermaid extension
3. **GitHub**: Renders automatically in README files
4. **Documentation tools**: MkDocs, Docusaurus support Mermaid

---

## Transpiler Questions

### What output formats are supported?

Currently:
- **Mermaid** (flowcharts and mindmaps)
- **Alloy** (formal verification)

Planned:
- Python code generation
- JSON/YAML export
- GraphViz diagrams

### Why use Alloy?

Alloy is a formal specification language that can automatically verify logical consistency. It's perfect for ensuring legal logic is sound.

### Do I need to know Alloy?

No! Yuho generates Alloy automatically. If you want to verify specifications, you can learn Alloy basics, but it's not required.

### Can I add my own transpiler?

Yes! See [Transpilers Overview](../transpilers/overview.md) for how to add new transpilers.

---

## Development Questions

### How can I contribute?

See [Contributing Guide](../development/contributing.md) for:
- Code contributions
- Documentation improvements
- Bug reports
- Feature requests

### What's the technology stack?

- **Language**: Python 3.8+
- **Parser**: Lark (LALR parser generator)
- **CLI**: Click framework
- **Testing**: pytest
- **Docs**: MkDocs with Material theme
- **CI/CD**: GitHub Actions

### How is Yuho tested?

Comprehensive testing with 234+ tests:
- Unit tests for components
- Integration tests for workflows
- End-to-end tests with real examples
- Performance tests

### Can I use Yuho in my project?

Yes! Yuho is open-source. See the license for details.

---

## Performance Questions

### How fast is Yuho?

Typical performance:
- Small files (<10 statements): <10ms
- Medium files (10-100 statements): <50ms
- Large files (100-1000 statements): <500ms

### Can Yuho handle large codebases?

Yes, though Yuho is designed for individual statutes rather than entire codebases. Each statute is typically a separate file.

### Is there a file size limit?

No hard limit, but practical considerations:
- Files over 1000 lines may be slow to parse
- Consider splitting large statutes into modules

---

## Error Messages

### "Syntax error at line X"

Check common issues:
- Using `=` instead of `:=`
- Missing semicolons `;`
- Unclosed braces `{}`
- Wrong comment syntax

### "Type mismatch" error

Ensure types match:
```yh
// Wrong
int x := "string";

// Correct
int x := 42;
string s := "string";
```

### "Undefined variable" error

Variables must be declared before use:
```yh
// Wrong
int y := x;  // x not defined

// Correct
int x := 42;
int y := x;
```

### "Module not found" error

When importing, ensure:
- File exists
- Path is correct
- Using correct import syntax

---

## Docker Questions

### Why use Docker?

Benefits:
- Consistent environment across systems
- No need to install Python locally
- Easy testing and deployment
- Isolated from system Python

### How do I run Yuho in Docker?

```bash
# Check a file
docker run --rm -v $(pwd):/workspace yuho:latest check file.yh

# Interactive REPL
docker-compose run --rm yuho-repl
```

### Can I develop in Docker?

Yes! Use the development container:
```bash
docker-compose up yuho-dev
```

---

## Documentation Questions

### Where is the documentation?

Multiple locations:
- **This site**: https://gongahkia.github.io/yuho
- **Syntax spec**: `doc/SYNTAX.md` in repository
- **Examples**: `example/` directory
- **API docs**: Auto-generated from code

### Is there a PDF version?

Not currently, but you can print any documentation page to PDF from your browser.

### How do I contribute to documentation?

Documentation is in `docs/` directory. Edit Markdown files and submit a pull request.

---

## Legal Questions

### Is Yuho legally binding?

No! Yuho is an educational and analytical tool. It does not constitute legal advice and representations in Yuho are not legally binding.

### Can I use Yuho in court?

Yuho is not designed for courtroom use. It's an educational and analytical tool for understanding legal logic.

### What jurisdiction does Yuho cover?

Currently focused on Singapore Criminal Law, but applicable to any statute-based jurisdiction.

### Can Yuho replace lawyers?

Absolutely not! Yuho is a tool for understanding and analyzing legal logic, not for providing legal advice or services.

---

## Troubleshooting

### My code won't parse

Common issues:
1. Check for typos in keywords
2. Ensure proper use of `:=`
3. Verify all braces are matched
4. Check semicolon placement

### Diagrams aren't generating

1. Check file passes `yuho check`
2. Verify output path is writable
3. Ensure proper command syntax
4. Check for transpiler errors in verbose mode

### Tests are failing

1. Ensure all dependencies installed: `pip install -r requirements-dev.txt`
2. Check Python version: `python --version` (need 3.8+)
3. Clear cache: `rm -rf __pycache__ .pytest_cache`
4. Reinstall: `pip install -e . --force-reinstall`

---

## Future Plans

### What's on the roadmap?

See [Roadmap](../../doc/ROADMAP.md) for detailed plans, including:
- LSP support for IDEs
- More transpiler targets
- Web interface
- Additional legal domains
- Contract law support

### When will feature X be added?

Check the [GitHub Issues](https://github.com/gongahkia/yuho/issues) for feature requests and timelines.

### Can I request a feature?

Yes! Open an issue on GitHub with your feature request.

---

## Community

### How do I get help?

1. Check this FAQ
2. Read the [documentation](../index.md)
3. Search [GitHub Issues](https://github.com/gongahkia/yuho/issues)
4. Open a new issue if needed

### Is there a community forum?

Currently, discussions happen on GitHub. A dedicated forum may be added if there's demand.

### How do I report bugs?

Use the [bug report template](../../admin/BUG_REPORT.md) and open a GitHub issue.

---

## Comparisons

### Yuho vs Natural L4

- **Natural L4**: English-like syntax, broader scope (all Singapore law)
- **Yuho**: Code-like syntax, focused on criminal law
- Both aim to formalize legal reasoning

### Yuho vs Catala

- **Catala**: Mimics legal text structure exactly
- **Yuho**: More programming-oriented syntax
- Both transpile to multiple formats

### Yuho vs traditional legal tools

Yuho is NOT a replacement for:
- Legal research tools (Westlaw, LexisNexis)
- Document automation (Docassemble)
- Case management systems

Yuho is FOR:
- Understanding legal logic
- Teaching legal reasoning
- Analyzing statutory structure

---

## Still Have Questions?

- Check the [documentation](../index.md)
- Read the [syntax guide](../language/syntax.md)
- See [examples](../examples/criminal-law.md)
- Open a [GitHub issue](https://github.com/gongahkia/yuho/issues)

---

*This FAQ is continuously updated. Last updated: 2024*

