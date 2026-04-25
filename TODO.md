# Yuho — Outstanding Work

Authoritative backlog. Positioning is deliberately narrow:
**a robust DSL + cohesive proof of concept for Singapore criminal law
(Penal Code)**, not a general legal-tech platform.

Status key: `[ ]` pending · `[~]` in progress · `(def)` deferred.

Current snapshot: **524/524 L1+L2 green · 122 L3 stamped · all 14
grammar gaps (G1–G14) closed or deferred to tooling.**

Completed history (Phases A–D, L3 flag fixes, MCP expansion, LSP buff-up,
VS Code extension v0.2, DOCX transpile target, fidelity diagnostics) lives
in git log + `doc/PHASE_*` notes, not here.

---

## Next session — priority queue

### Repository restructure + documentation overhaul `[ ]`

Bring the repo's presentation layer to PAR. Goal: on-brand, navigable,
comparable to top-tier OSS/knowledge projects.

- [ ] Audit current top-level layout (`src/`, `library/`, `editors/`, `doc/`, `scripts/`, `tests/`) — decide keep / rename / collapse / split. Write the proposed tree before moving anything.
- [ ] Update every README (`README.md`, `src/README.md`, `library/penal_code/README.md`, `editors/*/README.md`, `doc/*.md`) to the new structure.
- [ ] Reference benchmarks for README / docs styling:
    - Hugging Face (model/dataset cards, badges, tabbed quickstart)
    - Catala (legal DSL — narrative intro + example-first docs)
    - Obsidian (graph-style cross-linking, callouts)
    - Notion (block-based, heavy use of toggles + callouts)
    - Logseq (outliner style, knowledge-graph emphasis)
- [ ] New top-level `README.md` with: hero banner, 1-paragraph pitch, live-demo badge row, "what is Yuho" diagram, 60-sec quickstart, feature matrix, architecture diagram, citation block, contribution blurb.
- [ ] Unified doc index at `doc/INDEX.md` grouped by audience (user / contributor / researcher).
- [ ] Cross-link `.md` files like an Obsidian vault (relative-path wikilinks where sensible).
- [ ] Generate a dependency/architecture SVG (Mermaid → rendered) showing: grammar → AST → analyzers → transpilers → CLI / LSP / MCP / TUI.
- [ ] Add per-phase "lessons learned" appendix in `doc/RETROSPECTIVE.md` (pulling from `PHASE_C_REVIEW.md`, `PHASE_D_*`, etc.).
- [ ] Normalize heading styles, badge order, and code-block language tags across all `.md` files.

### Research paper (LaTeX) `[ ]`

Draft a full academic paper about Yuho from scratch, suitable for submission
to a legal-tech or PL venue (ICAIL, JURIX, CoNLL demo track, SPLASH OOPSLA
Onward!, PLDI SRC).

- [ ] Scaffold `paper/` with `main.tex`, `references.bib`, `paper/sections/` (intro, background, design, implementation, evaluation, related-work, limitations, conclusion), `paper/figures/`, `paper/Makefile`.
- [ ] Pick template: ACM primary-article or LNCS. Default to ACM `acmart` + `\documentclass[sigconf,review,anonymous]{acmart}`.
- [ ] **Introduction**: thesis — legal statutes are executable-adjacent artefacts, and SG Penal Code is a tractable testbed.
- [ ] **Background**: brief survey of legal DSLs (Catala, lam4, LexScript, LDOC, Akoma Ntoso) + formal methods (Z3, Alloy) usage in law.
- [ ] **Design**: Yuho grammar (14 grammar gaps G1–G14), element/penalty/exception model, deontic types, burden qualifiers, Catala-style defaults, temporal/causal constraints.
- [ ] **Implementation**: tree-sitter parser, Python AST, 6 transpilers (JSON/English/LaTeX/Mermaid/Alloy/DOCX), LSP + MCP surfaces, fidelity diagnostics, Z3/Alloy verification hookup, scraper + 3-tier coverage (L1/L2/L3).
- [ ] **Evaluation**: 524/524 L1+L2, 122 L3 signoff; fidelity-diagnostic hit rate; encoding time per section; qualitative analysis of grammar gaps uncovered.
- [ ] **Related work** matrix comparing Yuho vs Catala/lam4/LexScript/LDOC across: expressivity (deontic, defaults, temporal), tooling (LSP/MCP), target coverage, formal-verification hookup.
- [ ] **Limitations** — common-law doctrines not yet modelled, precedent integration shallow, no live SSO diffing, single-jurisdiction.
- [ ] Figures: AST diagram, penalty-combinator tree (G12), Catala-style default chain (G13), coverage Sankey.
- [ ] Auto-include repo stats from `coverage.json` via Makefile preprocessing.
- [ ] `paper/Makefile` with `make paper` (latexmk), `make figures`, `make arxiv` (tar the sources).

---

## Microsoft Word extension `[ ]`

Reach into the editor practitioners actually use. DOCX transpile target
already landed — Word add-in can call `yuho transpile -t docx` directly.

- [ ] Office Add-in (TypeScript) targeting Word desktop + web under `editors/word-yuho/`.
- [ ] Ribbon command: "Insert encoded statute" — picker over the local library, inserts English transpilation as formatted text + footnote link to SSO anchor.
- [ ] Context menu on a SG Penal Code citation (e.g. "s415") → hover card with marginal note, penalty range, illustrations count, and SSO link.
- [ ] Side panel: search/browse by section / title / element keyword with L1/L2/L3 badges.
- [ ] Live check: paste a Yuho snippet into Word; add-in streams it to `yuho check` and marks errors inline.
- [ ] Stretch — "Convert statute citation → Yuho skeleton" button.
- [ ] Office.js app manifest + Microsoft AppSource publish (stretch).

## LSP — remaining polish `[ ]`

- [ ] Cross-file rename (`s415` across the library).
- [ ] Goto-definition into `referencing` / `subsumes` / `amends` targets — blocked on G10 semantic hookup.

## VS Code extension — remaining polish `[ ]`

- [ ] Tree view panel: library browser sorted by section number with L1/L2/L3 badges.
- [ ] Marketplace publish (stretch).

## Remaining tooling gaps `[ ]`

- [ ] **G10** semantic hookup for cross-section references. Resolver walks `referencing` / `subsumes` / `amends` edges so queries like "all sections that extend s415" become answerable. Unlocks LSP goto-def, Tarjan SCC, and named-norm references.
- [ ] Aggregate-all-errors compilation (LexScript pattern) — don't short-circuit on first parse error.

## Ideas borrowed from other legal DSLs `[ ]`

Discovered while auditing LexScript (MIT), lam4 (Apache-2.0), Catala (Apache-2.0).

- [ ] **Tarjan SCC + BFS over the statute reference graph** (LexScript). Catches unreachable exception branches and cyclic cross-refs. Unlocks after G10.
- [ ] **Named-norm references / `IS_INFRINGED` predicate** (lam4). Lets `s107` abetment express "if `s299` IS_INFRINGED, then …" in grammar. Composes with G10.
- [ ] **Scope composition** (Catala). Callable statute scopes so s34 common intention and s107 abetment can wrap arbitrary base offences as functions.

## L3 long tail `(def)`

~400 shorter / simpler sections still unstamped. Most are single-sentence
interpretation sections where the encoding is a faithful mirror and the
bug surface is small.

- [ ] Revisit when L3 matters for a concrete deliverable.
      Command: `phase_d_l3_review.py --all-unstamped --dispatch --reasoning medium --parallel 8`.

---

## Deferred

### Documentation site `(def)`

Final polish. Static HTML site built from the committed library.

- [ ] Index page listing all 524 encoded PC sections with L1/L2/L3 badges.
- [ ] Per-section page: raw statute text + encoded `.yh` (syntax-highlighted) + Mermaid diagram + English transpilation + SSO deep-link.
- [ ] Cross-reference graph page (needs G10).
- [ ] Coverage dashboard page.
- [ ] Gap / review notes linked from affected sections.

### Phase 2a — Historical versions `(def)`

- [ ] Extend `scrape_sso.py` with `--historical` flag. Enumerate `/Act/<CODE>/Historical/<DATE>` snapshots.
- [ ] Store each historical snapshot under `library/<act>/_raw/historical/<date>.json`.
- [ ] Extend AST's `effective_dates` semantics to thread version lineage.
- [ ] Coverage harness extension — per `(section, valid-date)` rows.
- [ ] Temporal query support: "what did s300 look like in 1995?"

### Phase 2b — Vision pivot `(def)`

Only after PC L3 coverage is high and tooling is battle-tested.

- [ ] Evidence Act (EA1893)
- [ ] Criminal Procedure Code
- [ ] Constitution (CONS1963)
- [ ] Contract Law (common law + Misrepresentation Act, Contracts (Rights of Third Parties) Act, etc.)
- [ ] Civil remedies and equitable doctrines — require AST shapes Yuho doesn't have yet.
