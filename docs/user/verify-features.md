# Verifying Yuho's user-facing features

A manual walkthrough of every shipped surface. Run top-to-bottom; each
section is self-contained and you can stop after any one.

Prerequisites: from the repo root,

```sh
pip install -e .[dev]
```

(or `pip install -e .[all]` for everything including the LSP/MCP/Word
extras).

---

## 1. The CLI — `yuho` (~30 commands)

### Basic file checks

```sh
yuho check library/penal_code/s415_cheating/statute.yh
yuho lint  library/penal_code/s415_cheating/statute.yh
yuho ast   library/penal_code/s415_cheating/statute.yh --stats
yuho fmt   library/penal_code/s415_cheating/statute.yh --check
```

Expected: each prints structured output, exits 0.

### Transpile to all eight targets

```sh
yuho transpile -t json       library/penal_code/s415_cheating/statute.yh
yuho transpile -t english    library/penal_code/s415_cheating/statute.yh
yuho transpile -t latex      library/penal_code/s415_cheating/statute.yh
yuho transpile -t mermaid    library/penal_code/s415_cheating/statute.yh
yuho transpile -t mindmap    library/penal_code/s415_cheating/statute.yh
yuho transpile -t alloy      library/penal_code/s415_cheating/statute.yh
yuho transpile -t akomantoso library/penal_code/s415_cheating/statute.yh
yuho transpile --all         library/penal_code/s415_cheating/statute.yh --dir /tmp/s415-all/
```

The DOCX target writes a binary; pass `-o out.docx`.

For Mermaid flowcharts there are two **shapes**:

```sh
# default — statute structure (combinator-aware decision tree per section)
yuho transpile -t mermaid library/penal_code/s415_cheating/statute.yh

# schema — case-struct walk + fn consequence terminals (5-min doc style)
yuho transpile -t mermaid --shape schema my_section_with_struct_and_fn.yh
```

`-t mindmap` always emits the structural mindmap (`mindmap` Mermaid
dialect). To validate the AKN round-trip across the whole library:

```sh
python scripts/akn_roundtrip.py        # 524/524 validate clean
```

### Reference graph + SCC analysis

```sh
yuho refs                              # whole-library stats
yuho refs s415                         # in/out edges for s415
yuho refs s415 --transitive --out      # transitive closure
yuho refs --scc                        # find cross-section cycles
yuho refs --scc --json                 # machine-readable
```

The `--scc` run should report **4 non-trivial cycles** in the encoded
library (s292↔s293, s85↔s86, s424A↔s424B, s304B↔s74A).

### Plain-language section summaries

```sh
# Five-section prose block (header + what-it-covers + elements + penalty +
# worked example + disclaimer). Use when you want a reader-friendly summary.
yuho explain library/penal_code/s415_cheating/statute.yh
yuho explain library/penal_code/s415_cheating/statute.yh 415   # specific section
```

### Counter-example explorer + charge recommender

```sh
# Explorer: enumerates satisfying / borderline scenarios over a section.
yuho explore library/penal_code/s415_cheating/statute.yh 415

# Recommender: takes a fact-pattern YAML (see simulator/fixtures/ for
# examples) and ranks sections by structural fit.
yuho recommend simulator/fixtures/s415_classic.yaml
```

The recommender ranks Penal Code sections by structural fit. Output
is decorated with the `LEGAL_DISCLAIMER` envelope and a
`not_legal_advice` flag — that is not a hedge, it is the contract.

### Verification (Z3 / Alloy)

```sh
yuho verify        library/penal_code/s415_cheating/statute.yh
yuho verify-report library/penal_code/s415_cheating/statute.yh -o report.tex
```

Z3 is bundled with the `[verify]` extras. Alloy needs a separate
install (see `docs/contributor/architecture.md` §verification).

### Other handy commands

```sh
yuho repl                              # interactive REPL
yuho graph --format mermaid library/penal_code/s415_cheating/statute.yh
yuho diff  library/penal_code/s299_culpable_homicide/statute.yh \
           library/penal_code/s300_murder/statute.yh
yuho ci-report                         # repo-wide pass/fail summary
yuho schema                            # JSON schema for transpile output
yuho generate-tests library/penal_code/s415_cheating/statute.yh
yuho compliance-matrix library/penal_code/s415_cheating/statute.yh
yuho library list
yuho library search theft
yuho library tree
```

---

## 2. The Language Server (LSP)

```sh
# Start the LSP over stdio (most editors expect this transport).
yuho lsp
```

Then connect from any LSP client. For a quick CLI sanity check:

```sh
echo '{}' | yuho lsp --check  # spawn, log capabilities, exit
```

Smoke-tested via `tests/test_lsp_handlers.py`.

---

## 3. The MCP server (Model Context Protocol)

```sh
# Start the MCP server. Speaks JSON-RPC over stdio by default.
yuho serve
```

Wire to Claude Desktop / Cursor / Codex CLI by adding to your
client's MCP config (see `docs/user/mcp-install.md`). The server
exposes ~40 tools (`yuho_check`, `yuho_transpile`, `yuho_apply_flag_fix`,
…), ~20 resources (`yuho://library/<section>`, `yuho://prompts/...`),
and a handful of structured prompts.

Verify all tools register cleanly:

```sh
.venv-test/bin/python -m pytest tests/test_mcp_tools.py -q
```

---

## 4. VS Code extension

```sh
cd editors/vscode-yuho
npm install
npm run package    # produces yuho-x.y.z.vsix
code --install-extension yuho-*.vsix
```

Open any `.yh` file in VS Code and you should see syntax highlighting,
hover popups, completion, code lens (Explore / Recommend), and a
status-bar L3 coverage indicator.

---

## 5. Browser extension

```sh
cd editors/browser-yuho
python build_data.py             # regenerate data/ from library/penal_code
python build_explore.py
# Load the unpacked extension from editors/browser-yuho/ in chrome://extensions/
# (Firefox: about:debugging > "Load Temporary Add-on" > pick manifest.firefox.json)
```

The extension overlays Penal Code sections with their encoded form
when you visit Singapore Statutes Online.

---

## 6. Static explorer site

Two-step build for the fast path:

```sh
# Step 1: structural corpus rebuild (no SVG rendering — fast, ~30 s).
python scripts/build_corpus.py --no-mermaid-svg

# Step 2: parallel SVG rendering (mmdc + Chrome via puppeteer).
# 524 sections * 2 diagrams = 1048 renders, ~10 min at --workers 8.
# Requires `npm i -g @mermaid-js/mermaid-cli` plus
# `npx puppeteer browsers install chrome` once on first install.
python scripts/render_svg_cache.py --workers 8

# Step 3: build the static HTML.
python editors/explorer-site/build.py
python -m http.server -d editors/explorer-site/build 8000
open http://localhost:8000
```

Single-step (slower) alternative for a one-off rebuild:

```sh
python scripts/build_corpus.py    # ~2 hours single-threaded
```

A browseable per-section index of the entire encoded Penal Code. No
backend, just static HTML + JS.

Pages shipped:

- `/` – index (search + row-by-row section listing)
- `/coverage.html` – L1/L2/L3 dashboard
- `/graph.html` – **interactive cross-reference graph** (cytoscape.js,
  524 nodes, click a node to open its section page, toggle implicit
  edges, live filter)
- `/semantic-graph.html` – **typed semantic graph** at definition / element
  / exception granularity (~2,300 nodes, ~2,000 edges across the full
  library; section nodes click through, kind-coloured edges, toggles
  to hide noisy mention/shared-term layers)
- `/about.html` – mascot + methodology summary
- `/s/<N>.html` – per-section pages with both **Diagram** (Mermaid
  flowchart) and **Mindmap** sections, plus controlled English,
  references in/out, encoded `.yh` source.

---

## 7. Microsoft Word add-in

```sh
cd editors/word-yuho
python build_data.py             # regenerate the per-section SVG/JSON cache
python build_manifest.py         # writes manifest.xml
# Side-load manifest.xml in Word (Insert → Add-ins → "Upload My Add-in")
```

Adds a Yuho ribbon to the **Insert** tab; insert encoded penal-code
section quotes / element lists / Mermaid SVGs into a Word document.

---

## 8. Akoma Ntoso XML round-trip

```sh
yuho transpile -t akomantoso library/penal_code/s415_cheating/statute.yh > /tmp/s415.akn.xml
xmllint --noout /tmp/s415.akn.xml          # well-formed?
python scripts/akn_roundtrip.py            # validate ALL 524 sections
```

Should print `AKN round-trip: 524/524 validate clean`.

---

## 9. Run the full test suite

```sh
.venv-test/bin/python -m pytest tests/ --ignore=tests/e2e -q
```

Should report ~4800 passed, 0 failed. Add `tests/e2e/` for the
end-to-end pack (slower).

---

## 10. Build the paper

```sh
cd paper
make smoke              # article-class build (basic TeX Live)
make paper              # full acmart build (needs latexmk + acmart)
make stats stats-extra  # regenerate auto-injected metrics
```

Output is `paper/main.pdf` (or `paper/main_smoke.pdf`).

---

## 11. Reference-graph cycle dump (for the paper's §5)

```sh
yuho refs --scc --json | python -m json.tool
```

The four cycles printed are the empirical evidence cited in
evaluation §5.X (Cross-reference graph structure).

---

## 12. Methodology numbers (for paper readers)

```sh
python scripts/paper_methodology.py
cat paper/methodology/throughput.json | python -m json.tool
cat paper/methodology/fidelity_hits.json | python -m json.tool
cat paper/methodology/gap_frequency.json | python -m json.tool
```

Regenerates the throughput / fidelity / gap-frequency JSON that
backs the empirical claims in evaluation §5.

---

## 13. Behavioural-test fixtures

```sh
.venv-test/bin/python -m pytest tests/test_library_statutes.py -k 'test_test_file_is_semantically_valid' -q
```

Should report 82 passed (the working companions) + ~442 skipped (the
sections without companions, mostly interpretation provisions where
structural parse + lint coverage is the appropriate bar).

---

## What "passing" means at each tier

| Tier | What it asserts | Automated? |
|---|---|---|
| **L1** | The `.yh` parses without syntax errors. | Yes — `yuho check`. |
| **L2** | AST builds, lint passes, fidelity diagnostics quiet. | Yes — `yuho check` + `yuho lint`. |
| **L3** | An 11-point human-checklist audit passed. | Author-administered; external counsel review pending. |

The paper's §7 is explicit that L3 stamps are author-administered, not
externally validated. That is the load-bearing caveat to read the
"524/524 L3-stamped" claim alongside.
