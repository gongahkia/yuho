# Yuho for VS Code

Language support for `.yh` (Yuho) files: live LSP diagnostics, syntax
highlighting, snippets, commands, and a coverage status-bar readout.

## Install

### From source (dev loop)

```sh
cd editors/vscode-yuho
npm install
npm run build                      # compiles src/extension.ts → out/
ln -s "$(pwd)" ~/.vscode/extensions/yuho
# restart VS Code
```

### Without TypeScript build

If you only want highlighting + snippets (no LSP + commands), skip the
build step — activation still registers the language. The LSP will fail
silently on activation and a warning will appear.

## Features

### Language server

Connects to `yuho lsp` on activation. You get:

- **Diagnostics** — parse errors with did-you-mean suggestions, type errors, and fidelity warnings (G4 illustration-count, fabricated fine/caning cap, G11 disjunctive connective check) surfaced inline.
- **Hover** — canonical SSO URL, marginal note, ~280 char canonical excerpt, and L1/L2/L3 coverage badges per statute. Hover on `statute N` or `SN` to see it.
- **Completion** — context-aware. Typing after `penalty ` narrows to `cumulative / alternative / or_both / when`. After `fine := ` → `unlimited`. After `caning := ` → `unspecified`.
- **Inlay hints** — inferred variable types + per-statute summary (`⟨3 elements · 16 illustrations · 2 subsections · effective 1872-01-01⟩`).
- **Code lens** — L1/L2/L3 status badge + "Run tests" + "Transpile to English" per statute.
- **Code actions / definitions / references / document symbols / formatting / rename** — all via the Yuho LSP.

### Syntax highlighting

TextMate grammar covers the full statute-level surface: keywords
(`statute`, `subsection`, `definitions`, `elements`, `penalty`,
`illustration`, `exception`, `caselaw`, `parties`), penalty combinators
(`cumulative`, `alternative`, `or_both`, `when`), lifecycle keywords
(`effective`, `repealed`, `subsumes`, `amends`, `priority`, `defeats`),
sentinels (`unlimited`, `unspecified`), element kinds (`actus_reus`,
`mens_rea`, `circumstance`, `obligation`, `prohibition`, `permission`),
burden qualifiers, types, operators, money/percent/date/duration literals.

### Snippets

Type the prefix then tab.

| Prefix | Shape |
|---|---|
| `statute-header` | Header block with jurisdiction + amendment meta |
| `shape-offence` | Full offence: definitions + elements + penalty |
| `shape-punishment` | Pure punishment section with cross-ref comment |
| `shape-interpretation` | Definitions-only section |
| `subsection` | G5 subsection block |
| `penalty-or-both` | G8 — X years or fine or both |
| `penalty-nested` | G12 — imprisonment AND ALSO fine or caning (nested combinator) |
| `penalty-when` | G9 — conditional sibling branches |
| `exception` | G13 — prioritised exception with defeats edge |
| `illustration` | Verbatim illustration block |
| `match` | Match expression |
| `struct` | Struct |
| `fn` | Function |

### Commands

All reachable via the command palette (`Cmd/Ctrl+Shift+P`, type "Yuho").

| Command | What it does |
|---|---|
| `Yuho: Open SSO page for section under cursor` | Extracts the SSO anchor from `@meta source=` or the `statute N` header and opens sso.agc.gov.sg in your browser |
| `Yuho: Run check on active file` | Runs `yuho check` and reports the result in a notification |
| `Yuho: Transpile to Mermaid → open preview` | Runs `yuho transpile -t mermaid` and opens the output in a new untitled editor |
| `Yuho: Transpile to plain English` | Same but `english` target |
| `Yuho: Show coverage dashboard` | Opens `library/penal_code/_coverage/COVERAGE.md` (or a summary notification) |

### Status bar

Right-side bar shows `📖 Yuho L1 524/524 · L2 524/524 · L3 122/524` when
a workspace containing `library/penal_code/_coverage/coverage.json` is
open. Click to open the dashboard.

## Settings

| Setting | Default | Description |
|---|---|---|
| `yuho.lsp.enabled` | `true` | Launch `yuho lsp` on activation |
| `yuho.lsp.command` | `yuho` | Path to the Yuho executable |
| `yuho.lsp.args` | `["lsp"]` | Arguments to start the LSP |

## Requirements

- VS Code 1.75 or later
- Yuho installed and on `PATH` (`pip install -e . && pip install -e '.[lsp]'`) — verify with `yuho --version`
