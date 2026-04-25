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

### Research paper (LaTeX) `[~]`

arXiv preprint, attributed, acmart `manuscript` mode. Full first draft
landed; outstanding work is empirical methodology runs and submission
hardening.

All 8 sections drafted (1,464 prose lines total under `paper/sections/`):
intro 118, background 160, design 294, implementation 249, evaluation 226,
related 254, limitations 108, conclusion 55.

Outstanding before submission:
- [ ] **Manual read-through pass.** Read the rendered PDF cover-to-cover, mark places where prose drifts, claims need a citation, or a paragraph buries the lede. Add detail where missing (especially in evaluation §5 and limitations §7) but stay tight — no padding. Aim: every paragraph earns its place.
- [ ] **Switch to two-column layout.** Current build is single-column smoke (`article`) plus single-column acmart `manuscript`. For density and venue-readiness, swap `main.tex` documentclass to `\documentclass[sigconf]{acmart}` (two-column ACM conf style). This gets `table*` to span both columns, tightens line lengths, and roughly halves page count. Re-check Figure 1 fit at narrower column width; may need `\begin{figure*}` for the s415 listing.
- [ ] **Blog-post transpilation.** Hand the rendered paper to Claude with the prompt: *"Transpile this paper into a markdown blog post for gabrielongzm.com. Target ~1500 words. Keep the thesis (statute-as-source-of-truth + the 14-grammar-gaps argument), drop the implementation SLOC tables, drop the methodology threats-to-validity, keep one worked example (s415), keep the Catala/lam4/LexScript comparison as prose not table. Conversational tone, link to the GitHub repo, embed coverage stats inline."* Output to `paper/blog/yuho.md`.
- [ ] **Evaluation methodology runs** — fill the `\todo{}` placeholders in `evaluation.tex`:
    - Fidelity diagnostic hit-rate methodology (re-run 4 diagnostics over all 524 sections, spot-check 30 warnings per check)
    - Encoding throughput numbers (median + p95 wall-clock; reconstructable from git timestamps + `.phase_d_l3_progress.jsonl`)
    - Gap-trigger frequency bar chart (source data in `doc/PHASE_C_GAPS.md`)
- [ ] Render Mermaid figures to PDF (requires `mmdc`), inspect, and tune layouts.
- [ ] Verify all `\cite{}` keys resolve cleanly. Some bib entries carry TODO notes — confirm canonical citations for `lam4`, `lexscript`, `ldoc`, `hammond1983rights`. Fix the two bibtex warnings (`ldoc` missing author/key for sort; `jackson2002alloy` has redundant volume+number).
- [ ] `scripts/repo_stats.py` — emit SLOC-per-layer JSON so the implementation Table 1 can be auto-regenerated rather than hand-typed.
- [ ] External-reader pass on the full PDF; tighten phrasing and integrate cross-references where the prose has drift between sections.
- [ ] Decide final venue (currently arXiv-attributed, `manuscript,nonacm` mode). For ICAIL/JURIX retargeting, swap documentclass per `paper/README.md`.

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
