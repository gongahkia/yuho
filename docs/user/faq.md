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

## 8. Do I need to know how to code?

No. Yuho's syntax is designed to read like structured English. If you can read a statute and identify its elements (actus reus, mens rea, etc.), you can write Yuho. The `yuho wizard` command guides you through creating a statute interactively without writing any code. For those who want to write `.yh` files directly, the syntax uses only ~10 keywords and has no loops or complex programming constructs.

## 9. What editor should I use to write `.yh` files?

Any text editor works (VS Code, Sublime Text, TextEdit, Notepad). Save files with a `.yh` extension. For syntax highlighting in Neovim, see `editors/nvim-yuho/`.

## 10. How do I set up `yuho explain` without Ollama?

The `explain` command works without any LLM configured -- it falls back to the built-in English transpiler. For enhanced AI-powered explanations, set an API key via environment variable:

```bash
export YUHO_LLM_PROVIDER=anthropic
export YUHO_LLM_ANTHROPIC_API_KEY=sk-ant-...
```

Or use Ollama locally (see `CONFIG.md` for full setup).
