# Cookbook: Legal AI Assistant

Integrate Yuho with Claude or other LLMs via the MCP server.

## MCP Setup (Claude Desktop)

```json
{
  "mcpServers": {
    "yuho": {
      "command": "yuho",
      "args": ["serve"]
    }
  }
}
```

Claude can now call Yuho's MCP tools, including:

- `yuho_check` — validate Yuho source.
- `yuho_parse` — return the parsed AST as JSON.
- `yuho_transpile` — convert to any of the eight transpile targets
  (`json`, `english`, `latex`, `mermaid`, `mindmap`, `alloy`, `docx`,
  `akomantoso`).
- `yuho_explain` — prose-first per-section summary (the same renderer
  that backs `yuho explain` on the CLI).
- `yuho_lint` — fidelity diagnostics over an encoded section.
- `yuho_apply_flag_fix` — minimum-edit fix dispatcher (writes a
  transient `_L3_FLAG.md`, runs the flag-fix script, returns the
  outcome).

The full surface is documented at `docs/user/mcp-install.md`.

## End-to-end pattern: prose-explain a statute

```python
# Inside a Claude tool-use loop:
# 1. Claude calls yuho_explain(file_content="<.yh source>")
# 2. The tool returns the 5-section prose block (header → what-it-covers
#    → elements → penalty → worked example → disclaimer).
# 3. Claude paraphrases / answers the user's question grounded in that
#    prose, citing element names and penalty ranges back to the user.
```

No HTTP wrapper is needed — the MCP server speaks JSON-RPC over stdio
and Claude Desktop / Claude Code / Cursor / Codex CLI all wire to it
directly.

## Validate LLM-generated statutes

```python
# Same MCP loop, different tool:
# yuho_check(file_content="<LLM-generated .yh>")
# returns {valid: bool, errors: [...], lint_warnings: [...]}.
# Feed errors back to the LLM for self-correction.
```
