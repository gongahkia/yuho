# Roadmap

> **Status Legend:** ✅ Complete | 🔄 In Progress | ⏳ Planned | ❌ Not Started

Development continues on the `main` branch.

![](../asset/memes/roadrunner_skinamarink.jpg)

## 1. Yuho LSP ✅ Complete (v5)

Full Language Server Protocol implementation in `src/yuho/lsp/`:

- ✅ Works with VS Code, Neovim, and any LSP-compatible editor
- ✅ Code completions, hover documentation, go-to-definition
- ✅ Real-time diagnostics and error reporting
- ✅ Rename refactoring with workspace-wide updates
- ✅ Code actions (quick fixes, extract pattern, inline variable)
- ✅ Selection range support, folding ranges
- ✅ Semantic tokens, inlay hints, signature help

## 2. Yuho Live Editor ⏳ Planned (v6)

An in-browser IDE for Yuho:

- ⏳ Live transpilation to diagrams
- ⏳ Linting, snippets, autocomplete
- ⏳ Error messages with suggestions
- References:
  - [lawtodata](https://lawtodata.streamlit.app/)
  - [streamlit](https://streamlit.io/cloud)
  - [L4's IDE](https://smucclaw.github.io/l4-lp/)
  - [ANTLR Lab](http://lab.antlr.org/)
  - [L4 Google Sheets Extension](https://l4-documentation.readthedocs.io/en/latest/docs/quickstart-installation.html)

## 3. LLM Integration 🔄 In Progress (v5)

LLM module implemented in `src/yuho/llm/`:

- ✅ Multi-provider support (Ollama, HuggingFace, OpenAI, Anthropic)
- ✅ Local-first with cloud fallback
- ✅ MCP tool: `yuho_statute_to_yuho` - converts natural language to Yuho
- ✅ Prompt templates for statute explanation, coverage analysis
- ⏳ Fine-tuned model for statute conversion
- ⏳ Chatbot for legal advice with diagram explanations

References:
- [legal-bert](https://huggingface.co/nlpaueb/legal-bert-base-uncased)
- [ollama](https://ollama.com/library)
- [langchainlaw](https://github.com/nehcneb/langchainlaw)

## 4. Form Generation ❌ Not Started

Automated legal form generation:

- ❌ Google Docs/Sheets extension
- Reference: [motoraccidents.lawnet](https://motoraccidents.lawnet.sg/)

## 5. Scratch-like Visual Editor ⏳ Planned (v6)

Block-based visual programming for law:

- ⏳ Drag-and-drop interface with live struct updates
- ⏳ Svelte-based frontend (localhost only)
- ⏳ Block-to-AST and AST-to-block converters
- ⏳ "Why did" / "Why didn't" questioning system

References:
- [Svelteflow](https://svelteflow.dev/)
- [Whyline](https://www.cs.cmu.edu/~NatProg/whyline.html)
- [Blockly](https://developers.google.com/blockly)
- [blockly-page-editor tutorial](https://github.com/jaelle/blockly-page-editor)

## 6. Additional Features

### Implemented in v5:
- ✅ MCP server with 15+ tools for AI integration
- ✅ Package library with registry, versioning, signatures
- ✅ Multiple transpile targets (JSON, JSON-LD, English, Mermaid, Alloy)
- ✅ Formal verification with Alloy and Z3
- ✅ Test coverage reporting with HTML output

### Conceptual/Research:
- Jurisdictional prerequisites in statute reasoning
- See [CCLaw Sandbox](https://github.com/smucclaw) for inspiration
