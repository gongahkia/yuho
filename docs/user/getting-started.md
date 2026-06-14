# Getting Started for Legal Tech Developers

This guide covers the shipped local surfaces: CLI, transpilers, LSP, and
MCP. Yuho does not currently ship a REST API, GraphQL target, Prolog
target, or WASM package.

## 1. Install

For repository work, use the supported Python range from the README:

```bash
uv venv --python 3.13 .venv
source .venv/bin/activate
uv pip install -e '.[dev,lsp,mcp]'
```

For package use:

```bash
pip install yuho
```

## 2. Parse a statute

```bash
cat > theft.yh <<'YH'
statute 1 "Theft" {
  elements {
    actus_reus taking := "Takes movable property";
    mens_rea dishonestly := "With dishonest intent";
  }
  penalty {
    imprisonment := 1 year .. 3 years;
  }
}
YH

yuho check theft.yh
```

## 3. Transpile

```bash
yuho transpile -t english    theft.yh
yuho transpile -t json       theft.yh
yuho transpile -t latex      theft.yh
yuho transpile -t mermaid    theft.yh
yuho transpile -t mindmap    theft.yh
yuho transpile -t alloy      theft.yh
yuho transpile -t docx       theft.yh -o theft.docx
yuho transpile -t akomantoso theft.yh
```

`yuho transpile --all theft.yh --dir out/` writes the standard target
set into a directory. The PDF/SVG/PNG paths are CLI conveniences built
from LaTeX and Mermaid outputs; they are not separate AST targets.

## 4. Explore the shipped library

```bash
yuho ci-report
yuho refs --scc --json
yuho explain library/penal_code/s415_cheating/statute.yh
yuho recommend simulator/fixtures/s415_classic.yaml
```

The repository ships all 524 Singapore Penal Code sections as `.yh`,
plus a raw Indian Penal Code snapshot and eight phase-1 encoded IPC
sections for cross-jurisdiction checks.

## 5. Editor and AI integrations

Start the language server over stdio:

```bash
yuho lsp
```

Start the MCP server for AI-client workflows:

```bash
yuho serve --stdio
```

See `editors/vscode-yuho/README.md` for VS Code setup and
`docs/user/mcp-install.md` for MCP client wiring.

## Next Steps

- [CLI Reference](cli-reference.md)
- [Feature Walkthrough](verify-features.md)
- [5-Minute Tour](5-minutes.md)
- [Contributor Architecture](../contributor/architecture.md)
