# Yuho — Outstanding Work

Authoritative backlog. Positioning is deliberately narrow:
**a robust DSL + cohesive proof of concept for Singapore criminal law
(Penal Code)**, not a general legal-tech platform.

Primary audience: **researchers, law students, and legal engineers**.
Secondary audience: practising lawyers and government law drafters.
Third tranche: AI-tool builders who need grounded legal corpora and
benchmarks.

Delivery order: **paper + product demo first**, installable package second,
practitioner workflow third. Yuho remains research / education oriented.
The headline is the **DSL for statutes**; the machine-checkable Penal Code
corpus is the proof and second headline.

Status key: `[ ]` pending · `[~]` in progress · `(def)` deferred.

Current snapshot: **524/524 L1+L2 green · 122 L3 stamped · all 14
grammar gaps (G1–G14) closed or deferred to tooling · 12,305 tests
passing across the suite · 6 user-facing surfaces shipped (CLI, LSP,
MCP, browser extension, static explorer site, Word add-in) · 2
analytical surfaces shipped (counter-example explorer, charge
recommender) · paper draft complete with applicability + corrected-
exception-encoding sections.**

Completed history (Phases A–D, L3 flag fixes, MCP expansion, LSP buff-up,
VS Code extension, DOCX transpile target, fidelity diagnostics, repo
restructure, the corpus-pivot product cycle, the analytical-surfaces
cycle, the test-suite triage) lives in git log + `docs/PHASE_*` notes,
not here.

---

## Research paper (LaTeX) `[~]`

arXiv preprint, attributed, acmart `manuscript` mode. Full first draft
landed and has since been extended with an applicability section
(\S\ref{sec:applicability}) on cross-jurisdiction portability and a
documentation pass on the corrected exception-encoding semantics.
Outstanding work is empirical methodology runs and submission
hardening.

- [ ] **Manual read-through pass.** Read the rendered PDF cover-to-cover,
      mark places where prose drifts, claims need a citation, or a paragraph
      buries the lede. Add detail where missing (especially in evaluation §5
      and limitations §7) but stay tight — no padding. Aim: every paragraph
      earns its place.
- [ ] **Switch to two-column layout.** Current build is single-column smoke
      (`article`) plus single-column acmart `manuscript`. Swap `main.tex`
      documentclass to `\documentclass[sigconf]{acmart}` for density and
      venue-readiness. Re-check Figure 1 fit at narrower column width;
      may need `\begin{figure*}` for the s415 listing.
- [ ] **Blog-post transpilation.** Hand the rendered paper to Claude with
      the prompt: *"Transpile this paper into a markdown blog post for
      gabrielongzm.com. Target ~1500 words. Keep the thesis (statute-as-
      source-of-truth + the 14-grammar-gaps argument), drop the
      implementation SLOC tables, drop the methodology threats-to-validity,
      keep one worked example (s415), keep the Catala/lam4/LexScript
      comparison as prose not table. Conversational tone, link to the
      GitHub repo, embed coverage stats inline."* Output to
      `paper/blog/yuho.md`.
- [ ] **Evaluation methodology runs** — fill the `\todo{}` placeholders in
      `evaluation.tex`:
    - Fidelity diagnostic hit-rate methodology (re-run 4 diagnostics over
      all 524 sections, spot-check 30 warnings per check)
    - Encoding throughput numbers (median + p95 wall-clock; reconstructable
      from git timestamps + `.phase_d_l3_progress.jsonl`)
    - Gap-trigger frequency bar chart (source data in `docs/PHASE_C_GAPS.md`)
- [ ] Render Mermaid figures to PDF (requires `mmdc`), inspect, and tune
      layouts.
- [ ] Verify all `\cite{}` keys resolve cleanly. Some bib entries carry
      TODO notes — confirm canonical citations for `lam4`, `lexscript`,
      `ldoc`, `hammond1983rights`. Fix the two bibtex warnings.
- [ ] `scripts/repo_stats.py` — emit SLOC-per-layer JSON so Table 1 can
      be auto-regenerated rather than hand-typed.
- [ ] External-reader pass on the full PDF; tighten phrasing and integrate
      cross-references where the prose has drift between sections.
- [ ] Decide final venue (currently arXiv-attributed, `manuscript,nonacm`
      mode). For ICAIL/JURIX retargeting, swap documentclass per
      `paper/README.md`.

---

## VS Code extension — marketplace publish `[ ]`

The extension itself is feature-complete (LSP wiring, status bar, tree
view, command palette, code lens for explorer / recommender, status-bar
coverage indicator). Remaining work is publishing.

- [ ] Marketplace publish (stretch).

---

## Remaining tooling gaps `[ ]`

- [ ] **Aggregate-all-errors compilation** (LexScript pattern). Don't
      short-circuit on first parse error; collect every diagnostic in
      one pass and surface them together. Useful for batch authoring
      and CI lint runs.

---

## Ideas borrowed from other legal DSLs `[ ]`

Discovered while auditing LexScript (MIT), lam4 (Apache-2.0),
Catala (Apache-2.0).

- [ ] **Tarjan SCC + BFS over the statute reference graph** (LexScript).
      Catches unreachable exception branches and cyclic cross-refs.
      Reference graph is shipped (G10); this is the next analysis on top.
- [ ] **Named-norm references / `IS_INFRINGED` predicate** (lam4). Lets
      `s107` abetment express "if `s299` IS_INFRINGED, then …" in grammar.
      Composes with G10.
- [ ] **Scope composition** (Catala). Callable statute scopes so s34 common
      intention and s107 abetment can wrap arbitrary base offences as
      functions.

---

## Test-suite backlog `[ ]`

Surfaced during the 1742→0 failure sweep. The suite is green; these are
real backlog items currently tracked as `xfail` / `skip` rather than
hidden.

- [ ] **202 broken companion `test_statute.yh` files.** Reference Yuho
      `fn` blocks (e.g. `is_abetment(...)`, `evaluate_cheating(...)`)
      that the corresponding `statute.yh` doesn't declare. The 28
      working companions (s415, s300, s378, s411, s470, s473C, …) show
      the working pattern: per-section `fn` definitions alongside the
      `elements` block. Three honest paths:
    1. **Delete the broken files.** They're never run, never depended on.
       Suite: 202 xfail → 202 deleted. Risk: zero. Loses aspirational
       test fixtures.
    2. **Agent-author `fn` blocks.** Spawn one agent per broken section
       to read `test_statute.yh`, infer required signatures, and write
       matching `fn` definitions into `statute.yh`. Risk: agent-generated
       function bodies may pass the assertions while drifting from the
       elements' doctrinal meaning.
    3. **Hybrid:** delete the bulk (62 `is_liable` / 28 `is_offence`
       generic-predicate files where the simulator already does the
       work); agent-author the ~10 high-traffic sections (s378 theft,
       s299 / s300 culpable homicide / murder, s319 hurt, s320 grievous
       hurt, s107 abetment, etc.) where the test exercises real
       section-specific logic.
    4. **294 sections without any companion file.** Coverage gap, not
       a regression. Authoring is per-section domain work; tackle
       opportunistically as L3 stamping reaches each one.
- [ ] **Pre-existing `test_documented_cli_commands_exist`.** The CLI
      reference documents commands (`api`, `explain`, `playground`,
      `static-site`) not implemented in `cli.commands`. Either implement
      them or trim the doc. Untouched by recent triage; still failing.

---

## Akoma Ntoso transpiler `[ ]`

The other planned transpilers (CATALA, FSTAR, JSONLD, GRAPHQL, BIBTEX,
COMPARATIVE, BLOCKS, PROLOG) were deliberately removed during cleanup —
their tests were referenced but the transpilers themselves never shipped,
and on close audit none have a load-bearing use case beyond the existing
six (JSON, ENGLISH, LATEX, MERMAID, ALLOY, DOCX).

Akoma Ntoso is the exception. It's the OASIS standard for legislative
XML used by the EU, UN, Italian Senate, Brazilian Congress, and the
broader legislative-informatics community. The applicability section
(\S\ref{sec:applicability}) argues Yuho should travel to other Anglo-
Indian penal codes; if any of those jurisdictions publish in Akoma Ntoso
(India's BNS 2023 has not yet, but the LegalDocML push is moving in
that direction), being able to emit Akoma Ntoso XML is the on-ramp.

Build only when there is a concrete cross-jurisdictional use case
demanding it; pre-building it as speculative interop is exactly the
mistake the cleanup just corrected.

- [ ] Decision criterion before building: a named external user
      (regulator, LegalDocML researcher, or downstream Akoma-Ntoso-
      consuming tool) asks for it.
- [ ] Scope when triggered: ~1k SLOC structural map from Yuho AST to
      Akoma Ntoso `<act>` / `<section>` / `<element>` / `<exception>`
      tags, including cross-reference resolution via the G10 graph.
- [ ] Validate output against the OASIS schema (xmllint or a
      schema-aware validator).

---

## L3 long tail `(def)`

~400 shorter / simpler sections still unstamped. Most are single-
sentence interpretation sections where the encoding is a faithful mirror
and the bug surface is small.

- [ ] Revisit when L3 matters for a concrete deliverable.
      Command:
      `phase_d_l3_review.py --all-unstamped --dispatch --reasoning medium --parallel 8`.

---

## Deferred from the repo restructure `(def)`

- [ ] Once L3 dispatcher idle: move `docs/PHASE_D_*PROMPT.md` to
      `docs/researcher/phase-d-*.md` with kebab-case; remove
      `doc -> docs` symlink.
- [ ] Render `paper/figures/architecture.mmd` to `docs/architecture.svg`
      (requires `mmdc`).
- [ ] Write `docs/retrospective.md` consolidating PHASE_C_REVIEW +
      PHASE_D_*PROMPT lessons-learned.
- [ ] `CLAUDE.md` symlink at root works for local user but breaks for
      other contributors. Either unsymlink + plain-file with a note,
      or `.gitignore` it.
- [ ] Phase-D progress JSONL files at root — should move under
      `library/penal_code/_coverage/` or a new `state/` dir for tidiness.

---

## Notes for fresh contributors

- **Hypothesis dep.** Already declared in `pyproject.toml` under the
  `[dev]` extras group. To run the property-based tests
  (`tests/test_properties.py`, `tests/test_statutes.py`), install with:
  `pip install -e .[dev]` (or `pip install -e .[all]` for everything).
  CI configurations should pin to the `[dev]` extra so the property
  suite participates in the test run.

---

## Deferred

### Phase 2a — Historical versions `(def)`

- [ ] Extend `scrape_sso.py` with `--historical` flag. Enumerate
      `/Act/<CODE>/Historical/<DATE>` snapshots.
- [ ] Store each historical snapshot under
      `library/<act>/_raw/historical/<date>.json`.
- [ ] Extend AST's `effective_dates` semantics to thread version lineage.
- [ ] Coverage harness extension — per `(section, valid-date)` rows.
- [ ] Temporal query support: "what did s300 look like in 1995?"

### Phase 2b — Vision pivot `(def)`

Only after PC L3 coverage is high and tooling is battle-tested.

- [ ] Evidence Act (EA1893)
- [ ] Criminal Procedure Code
- [ ] Constitution (CONS1963)
- [ ] Contract Law (common law + Misrepresentation Act, Contracts
      (Rights of Third Parties) Act, etc.)
- [ ] Civil remedies and equitable doctrines — require AST shapes Yuho
      doesn't have yet.
