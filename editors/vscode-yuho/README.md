# Yuho VS Code

Adds `.yh` language registration, TextMate fallback highlighting, optional tree-sitter semantic highlighting, and a Yuho LSP client.

The extension launches `yuho-lsp` by default. Override `yuho.lsp.command` and `yuho.lsp.args` when using a local checkout, for example command `uv` with args `["run", "yuho-lsp"]`.

Tree-sitter highlighting loads a built `tree-sitter-yuho` Node module when available. Set `yuho.treeSitter.modulePath` if the module is outside the repo checkout.
