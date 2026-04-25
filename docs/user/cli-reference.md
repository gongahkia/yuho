# CLI Reference

All commands support `-h` / `--help` for detailed usage.

## Core Commands

| Command | Description |
|---------|-------------|
| `yuho check <file>` | Parse and validate a `.yh` file |
| `yuho transpile <file> -t <target>` | Transpile to json, jsonld, english, latex, mermaid, alloy, graphql, blocks |
| `yuho ast <file>` | Visualize AST as tree |
| `yuho fmt <file>` | Format a `.yh` file |
| `yuho lint <files...>` | Check for style and best practice issues |
| `yuho diff <file1> <file2>` | Semantic diff between two `.yh` files |
| `yuho test [file]` | Run `.yh` test assertions |
| `yuho repl` | Interactive REPL |
| `yuho verify <file>` | Run formal verification (Alloy/Z3) |
| `yuho graph <file>` | Visualize statute dependency graph |

## Generation & Scaffolding

| Command | Description |
|---------|-------------|
| `yuho generate <section> -t <title>` | Generate statute scaffold |
| `yuho wizard` | Interactive step-by-step statute builder (recommended for beginners) |
| `yuho init [name]` | Initialize a new Yuho project |
| `yuho contribute <file>` | Validate a statute for library contribution |

### `yuho wizard`

The wizard asks you questions in plain English and generates valid `.yh` code. This is the recommended starting point for users who have never written a `.yh` file. It prompts for: section number, title, definitions, elements (with type selection), penalty ranges, and illustrations. Output is saved to a file of your choice.

```bash
yuho wizard                # interactive mode
yuho wizard -o theft.yh    # specify output file
```

### `yuho repl`

Interactive REPL for experimenting with Yuho without creating files. Supports multi-line input and loading existing files.

```bash
yuho repl
```

Available commands inside the REPL:

| Command | Description |
|---------|-------------|
| `load <file>` | Load a `.yh` file into the session |
| `transpile <target>` | Transpile current session (english, mermaid, json, etc.) |
| `ast` | Show AST of current session |
| `history` | Show input history |
| `reset` | Clear the session |
| `help` | Show available commands |
| `exit` | Exit the REPL |

## LLM & AI Integration

| Command | Description |
|---------|-------------|
| `yuho explain <file>` | LLM-powered statute explanation |
| `yuho serve` | Start MCP server for AI assistant integration |

## Server & Editor Integration

| Command | Description |
|---------|-------------|
| `yuho lsp` | Start Language Server Protocol server |
| `yuho api` | Start REST API server |

## Advanced Commands

| Command | Description |
|---------|-------------|
| `yuho batch` | Run batch analysis or transpilation over many files |
| `yuho ci-report` | Generate machine-readable CI summaries |
| `yuho completion` | Emit shell completion scripts |
| `yuho compliance-matrix` | Build compliance comparison views |
| `yuho deps` | Inspect Yuho dependency information |
| `yuho eval` | Evaluate facts or expressions against Yuho models |
| `yuho explain-all <dir>` | Explain multiple Yuho files in one pass |
| `yuho export-training` | Export training-ready statute data |
| `yuho generate-tests <file>` | Generate test cases from statute constraints |
| `yuho playground` | Start the local playground server |
| `yuho refs [section]` | Query the cross-section reference graph (G10): subsumes / amends / implicit edges |
| `yuho schema` | Print the config or data schema |
| `yuho static-site` | Build a static study site from Yuho sources |
| `yuho verify-report` | Generate verification-focused reports |
| `yuho watch <file>` | Re-run checks as files change |
| `yuho webhook` | Start webhook integration endpoints |
| `yuho workspace` | Manage multi-file Yuho workspaces |

## Package Library

| Command | Description |
|---------|-------------|
| `yuho library search <query>` | Search for statute packages |
| `yuho library install <package>` | Install a package |
| `yuho library uninstall <package>` | Uninstall a package |
| `yuho library list` | List installed packages |
| `yuho library update [package]` | Update packages |
| `yuho library publish <path>` | Publish to registry |
| `yuho library info <package>` | Show package details |
| `yuho library outdated` | Show packages with updates |
| `yuho library tree [package]` | Show dependency tree |

## Configuration

| Command | Description |
|---------|-------------|
| `yuho config show` | Display current config |
| `yuho config set <key> <value>` | Set a config value |
| `yuho config init` | Create default config file |

## Transpilation Output Examples

### English

```bash
yuho transpile my_statute.yh -t english
```

Produces a structured plain English breakdown of the statute with definitions, elements classified by type, penalties, and illustrations. Most useful output for law students verifying their model.

### Validation Modes

```bash
yuho check my_statute.yh
yuho check my_statute.yh --syntax-only
```

`yuho check` runs parse, AST, semantic, and lint phases by default. Use `--syntax-only` when you explicitly want parse/AST validation without semantic checks.

### Mermaid

```bash
yuho transpile my_statute.yh -t mermaid
```

Generates Mermaid diagram code (mindmap or flowchart). View by pasting into [mermaid.live](https://mermaid.live) or wrapping in a ` ```mermaid ` block on GitHub.

### LaTeX / PDF

```bash
yuho transpile my_statute.yh -t latex > statute.tex
pdflatex statute.tex    # generates statute.pdf
```

Produces formatted statute documents. Requires LaTeX installed (`brew install --cask mactex-no-gui` on macOS).

### JSON

```bash
yuho transpile my_statute.yh -t json
```

Produces machine-readable structured output. Example:

```json
{
  "statutes": [{
    "section": "415",
    "title": "Cheating",
    "definitions": {
      "deceive": "To cause a person to believe something that is false",
      "fraudulently": "With intent to defraud another person"
    },
    "elements": [
      {"type": "actus_reus", "name": "deception", "description": "Deceiving any person"},
      {"type": "mens_rea", "name": "intent", "description": "Fraudulently or dishonestly"}
    ],
    "penalty": {
      "imprisonment": {"min": "1 year", "max": "7 years"},
      "fine": {"min": "$0.00", "max": "$50,000.00"}
    }
  }]
}
```

JSON output is primarily for tool integration -- feeding statute data into web apps, databases, or other programs. For study purposes, English and Mermaid outputs are more useful.

## Shell Completion

```bash
eval "$(yuho completion bash)"   # bash
eval "$(yuho completion zsh)"    # zsh
yuho completion fish > ~/.config/fish/completions/yuho.fish  # fish
```

## Global Options

| Flag | Description |
|------|-------------|
| `-v, --verbose` | Verbose output |
| `-q, --quiet` | Suppress non-error output |
| `--color / --no-color` | Force color on/off |
| `--version` | Show version |
| `-h, --help` | Show help |
