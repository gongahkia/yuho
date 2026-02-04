# Screenshot Guide for README

This guide documents the key functionalities to screenshot for the Yuho README and the commands to run for each.

## Key Functionalities to Capture

### 1. CLI Help Overview

Shows all 21 available CLI commands.

```bash
yuho --help
```

### 2. Syntax Highlighting & Code Example

Open a statute file in Neovim with the nvim-yuho plugin to showcase syntax highlighting.

```bash
nvim library/penal_code/s415_cheating.yh
```

Screenshot the `.yh` file with syntax highlighting enabled.

### 3. Validation with Error Messages

**Success case:**

```bash
yuho check library/penal_code/s415_cheating.yh
```

**Error case:** Create a file with intentional errors and run check on it to demonstrate error reporting with explanations.

### 4. Transpilation to Mermaid Diagrams

```bash
yuho transpile library/penal_code/s415_cheating.yh --target mermaid
```

Then render the Mermaid output in a Mermaid viewer (VS Code preview, mermaid.live, or similar) to capture the visual flowchart/mindmap.

### 5. Transpilation to Plain English

Shows how legal logic is converted to human-readable English.

```bash
yuho transpile library/penal_code/s415_cheating.yh --target english
```

### 6. Live Preview

Shows auto-reloading preview with file changes.

```bash
yuho preview library/penal_code/s415_cheating.yh
```

### 7. AST Visualization

Shows the parsed AST tree structure with statistics.

```bash
yuho ast library/penal_code/s415_cheating.yh
```

### 8. Interactive REPL

Screenshot the REPL interface with some sample commands executed.

```bash
yuho repl
```

Example REPL session to demonstrate:

```
>>> parse "scope test { integer x := 5 }"
>>> transpile --target english
>>> help
>>> exit
```

### 9. LLM-Powered Explanation

Requires LLM provider configuration (Ollama, OpenAI, Anthropic, or HuggingFace).

```bash
yuho explain library/penal_code/s415_cheating.yh
```

### 10. Testing with Coverage

```bash
yuho test library/penal_code/s415_cheating.yh --coverage
```

### 11. Diff Between Files

Compare two Yuho files and show semantic differences.

```bash
yuho diff file1.yh file2.yh
```

### 12. LSP Features in Neovim

Open a `.yh` file in Neovim and capture the following:

| Feature | How to Trigger |
|---------|----------------|
| Hover documentation | Position cursor over a symbol, wait for hover popup |
| Code completions | Start typing and trigger completion (Ctrl+Space or auto) |
| Diagnostic inline hints | Introduce an error to see inline diagnostics |
| Go-to-definition | `gd` on a symbol |
| Keybindings menu | `<leader>y` to show which-key Yuho commands |

Key Yuho keybindings to demonstrate:

- `<leader>ye` - Explain current file
- `<leader>yt` - Transpile current file
- `<leader>yc` - Check/validate current file
- `<leader>yv` - Verify current file

### 13. JSON Output

Machine-readable structured output for tooling integration.

```bash
yuho transpile library/penal_code/s415_cheating.yh --target json
```

### 14. Formal Verification

Requires Alloy Analyzer to be installed.

```bash
yuho verify library/penal_code/s415_cheating.yh
```

---

## Suggested Screenshot Order for README

| # | Screenshot | What it shows | Priority |
|---|------------|---------------|----------|
| 1 | Code sample | `.yh` file with syntax highlighting in editor | High |
| 2 | `yuho --help` | Available CLI commands overview | High |
| 3 | `yuho check` | Validation output (both success and error cases) | High |
| 4 | Mermaid diagram | Visual flowchart/mindmap of statute logic | High |
| 5 | English transpile | Human-readable plain English output | High |
| 6 | `yuho ast` | AST tree visualization with statistics | Medium |
| 7 | `yuho repl` | Interactive REPL session | Medium |
| 8 | Neovim LSP | Hover, completions, diagnostics in action | Medium |
| 9 | `yuho preview` | Live preview with auto-reload | Medium |
| 10 | `yuho explain` | LLM-powered explanation | Low |
| 11 | `yuho test` | Test execution with coverage report | Low |
| 12 | `yuho diff` | Semantic diff between files | Low |
| 13 | `yuho verify` | Formal verification output | Low |

---

## Tips for Good Screenshots

1. **Terminal screenshots**: Use a clean terminal with readable font size
2. **Editor screenshots**: Enable a visually appealing color scheme
3. **Mermaid diagrams**: Export as PNG/SVG for crisp rendering
4. **Consistent sizing**: Keep screenshots at similar dimensions
5. **Annotations**: Consider adding arrows or highlights for complex features
6. **Dark/Light mode**: Pick one theme and stay consistent

---

## Sample Statute Files for Screenshots

Located in `library/penal_code/`:

- `s415_cheating.yh` - Cheating (detailed with illustrations)
- `s299_culpable_homicide.yh` - Culpable Homicide
- `s300_murder.yh` - Murder
- `s378_theft.yh` - Theft
- `s390_robbery.yh` - Robbery
- `s463_forgery.yh` - Forgery
- `s499_defamation.yh` - Defamation
