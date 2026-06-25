# Yuho LSP

`yuho-lsp` is the pygls-backed language server for `.yh` files.

## Install

The command is exposed by `[project.scripts]` in `pyproject.toml`:

```bash
uv pip install -e '.[lsp]'
yuho-lsp
```

The `lsp` extra installs `pygls`. The dev install also includes it:
`uv pip install -e '.[dev]'`.

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

Completion returns core Yuho keywords and cross-section helpers. References
returns same-file section uses plus the declaration when requested. Semantic
tokens classify keywords, strings, and numeric section references. Code actions
expose a `yuho.check` command for clients that wire command execution.

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
