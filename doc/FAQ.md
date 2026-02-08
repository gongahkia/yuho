# FAQ

## 1. What does Yuho mean?

Yuho is derived from 夢法 (*yume ho*) which roughly translates to 'ideal law' in Japanese.

## 2. What version of Python is required?

Python 3.10 or later. See `pyproject.toml` for the full list of supported versions.

## 3. How do I install Yuho?

```bash
pip install yuho
```

Or clone the repo and run `./setup.sh` for a development install.

## 4. What file extension does Yuho use?

`.yh` files.

## 5. Can Yuho model statutes from jurisdictions outside Singapore?

Yes. The syntax is jurisdiction-agnostic. Current examples focus on Singapore Criminal Law but the language can represent any statute-based legal system.

## 6. How do I start the LSP server?

```bash
yuho lsp
```

See `editors/nvim-yuho/` for Neovim integration.

## 7. What transpilation targets are supported?

JSON, JSON-LD, English, Mermaid (mindmap/flowchart), LaTeX, Alloy, GraphQL, and Blocks.
