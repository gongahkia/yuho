# Yuho LSP

`yuho-lsp` is the pygls-backed language server for `.yh` files.

## Install

The command is exposed by `[project.scripts]` in `pyproject.toml`:

```bash
uv pip install -e '.[dev]'
yuho-lsp
```

The dev install includes `pygls`, so no separate Python LSP package is
needed.

## Capabilities

Diagnostics are published on open, change, and save. They come from the
same analysis service used by `yuho check`: parser diagnostics, AST build
errors, semantic/type-check issues, and `statute_lint` warnings.

Hover returns the AST node type and source span for the node under the
cursor. The span comes from `parser/source_location.py`.

Go-to-definition works for section references. The server first checks
the current file, then imported modules resolved through
`ModuleResolver`, then the checked-in Penal Code reference graph from
`library/reference_graph.py`.

## VS Code

The extension lives at `editors/vscode-yuho/`.

```bash
cd editors/vscode-yuho
npm install
```

Open that folder in VS Code and press F5 to launch an extension
development host. The extension starts `yuho-lsp` by default.

For a checkout where `yuho-lsp` is not on `PATH`, set:

```json
{
  "yuho.lsp.command": "uv",
  "yuho.lsp.args": ["run", "yuho-lsp"]
}
```

The extension also registers `.yh` files and provides TextMate fallback
highlighting. Optional tree-sitter highlighting is controlled by
`yuho.treeSitter.modulePath`.
