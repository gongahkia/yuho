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

## Generation & Scaffolding

| Command | Description |
|---------|-------------|
| `yuho generate <section> -t <title>` | Generate statute scaffold |
| `yuho wizard` | Interactive step-by-step statute builder |
| `yuho init [name]` | Initialize a new Yuho project |

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
| `yuho preview <file>` | Live preview with auto-reload in browser |

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
