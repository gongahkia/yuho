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

Current snapshot: **5046/5046 unit tests green · 524 sections at L1+L2 ·
524 L3 author-stamped · 82 sections with behavioural-test companions ·
14 grammar gaps closed or deferred to tooling · 7
transpiler targets shipped (JSON, English, LaTeX, Mermaid, Alloy, DOCX,
Akoma Ntoso) · 6 user-facing surfaces shipped (CLI, LSP, MCP, browser
extension, static explorer site, Word add-in) · 2 analytical surfaces
(counter-example explorer, charge recommender) · reference-graph
resolver shipped with Tarjan-SCC analysis, lam4-style `is_infringed`,
and Catala-style `apply_scope` cross-section predicates · paper draft
complete with applicability section + SCC empirical findings + Yuho
syntax highlighting in `listings` + Table 1 auto-generated from
`repo_stats.py`.**

Completed history (Phases A–D, L3 flag fixes, MCP expansion, LSP buff-up,
VS Code extension, DOCX transpile target, fidelity diagnostics, repo
restructure, the corpus-pivot product cycle, the analytical-surfaces
cycle, the test-suite triage, the SCC + IS_INFRINGED + apply_scope +
Akoma Ntoso work) lives in git log + `docs/PHASE_*` notes, not here.

---

## Research paper (LaTeX) `[~]`

arXiv preprint, attributed, acmart `manuscript` mode. Full first draft
landed and has since been extended with applicability, the corrected
exception-encoding semantics, SCC subsection, AKN transpiler mention,
and Yuho syntax highlighting via the `listings` package. Outstanding
work is submission hardening.

- [ ] **Manual read-through pass.** Read the rendered PDF cover-to-cover,
      mark places where prose drifts, claims need a citation, or a paragraph
      buries the lede. Add detail where missing (especially in evaluation §5
      and limitations §7) but stay tight — no padding.
- [ ] **Blog-post transpilation.** Hand the rendered paper to Claude with
      the prompt: *"Transpile this paper into a markdown blog post for
      gabrielongzm.com. Target ~1500 words. Keep the thesis (statute-as-
      source-of-truth + the 14-grammar-gaps argument), drop the
      implementation SLOC tables, drop the methodology threats-to-validity,
      keep one worked example (s415), keep the Catala/lam4/LexScript
      comparison as prose not table. Conversational tone, link to the
      GitHub repo, embed coverage stats inline."* Output to
      `paper/blog/yuho.md`.
- [ ] Render Mermaid figures to PDF (requires `mmdc`), inspect, and tune
      layouts.
- [ ] Confirm canonical citations for `lam4`, `lexscript`, `ldoc`,
      `hammond1983rights` (TODO notes still in `references.bib`).
- [ ] External-reader pass on the full PDF; tighten phrasing and integrate
      cross-references where the prose has drift between sections.
- [ ] Decide final venue (currently arXiv-attributed, `manuscript,nonacm`
      mode). For ICAIL/JURIX retargeting, swap documentclass per
      `paper/README.md`.
- [ ] **Methodology pipeline measurement-bug.** `paper/methodology/throughput.json`
      records a `min` of $-1$ days for one section (an `last_verified`
      stamp written before the first git commit). Root-cause and either
      fix or document.

---

## VS Code extension — marketplace publish `[ ]`

The extension itself is feature-complete. Remaining work is publishing.

- [ ] Marketplace publish (stretch).

---

## Evaluator-side semantics of `apply_scope` `[~]`

`apply_scope(<section_ref>, ...args)` and `is_infringed(<section>)`
now evaluate inside the tree-walking interpreter (commit
`feat(interp): wire apply_scope + is_infringed`): both AST nodes
delegate to `StatuteEvaluator` and return a boolean Value tracking
the inner scope's `overall_satisfied`. The remaining work is the
deeper static + symbolic layer.

- [ ] Type-check pass: when `apply_scope` is composed inside a parent
      statute, verify the parent's element shape is compatible with the
      base section's required inputs.
- [ ] Z3 backend hookup: model `apply_scope` as an inlined sub-formula
      so prioritised-rewriting at the parent retains the base's exception
      hierarchy.

---

## Akoma Ntoso transpiler `[ ]`

Structural transpiler ships and validates 524/524 against the
vendored OASIS XSD via `python scripts/akn_roundtrip.py --xsd`.
Remaining work is hardening:

- [ ] **Stretch:** add a CI job that runs `xmllint --schema` against
      every emitted document on every push (currently the round-trip
      is a one-shot script you opt into with `--xsd`).
- [ ] Decision criterion before further extension (richer FRBR
      hierarchy, full `<componentRef>` graph): a named external user
      asks for it.

---

## Test-suite backlog `[ ]`

The suite is green. 82 sections carry behavioural-test companions
(\texttt{test\_statute.yh}); 442 sections are pure-interpretation
provisions where structural parse + lint coverage is the appropriate
bar. The 202 broken companion files (which referenced helper `fn`
blocks the matching `statute.yh` didn't declare) were deleted in the
ship-readiness pass.

- [ ] **442 sections without behavioural companions.** Coverage gap,
      not a regression. Most are interpretation/definition provisions
      where there's no rich behaviour to assert beyond parse + lint.
      Author per-section companions opportunistically when an offence
      gains structural complexity that warrants behavioural testing.

---

## L3 long tail `(def)`

L3 author-stamping is at 524/524. Outstanding work is **external
counsel review** — a Singapore-qualified lawyer auditing a sample
of stamped encodings — which the paper §7 explicitly reserves.

- [ ] Identify a target sample size (e.g. 30 sections across chapters
      II / IV / XVI / XVII / XX) for external review.
- [ ] Engage external counsel; capture findings as `_L3_FLAG.md` files;
      run `scripts/apply_flag_fix.py` to address each flag.

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

The Penal Code 1871 has accumulated 150+ years of amendments. Yuho
currently encodes only the current version of each section; the
amendment-lineage metadata (`effective`, `amends`, `subsumes`) is
present but the historical clause text is not. This phase extends
Yuho into a **diachronic** legal artefact: every section carries
every historical version, and the toolchain answers "what did the
law look like on date X?" temporally.

**Scope (per design pick — full point-in-time replay):**

Every encoded section gets every historical version since 1872.
`yuho check --as-of 1995-06-15 my_facts.yh` and friends become
first-class queries.

#### Scrape + ingest

The v0 scrape ships (`scripts/scrape_sso.py historical-list /
historical / historical-bulk`); per-Act snapshots land under
`_raw/historical/<act>/<YYYYMMDD>.json` with a sibling
`historical_index.json`. Remaining work:

- [ ] Build a `historical_index.json` mapping `(section, valid-date)
      -> raw_path` so re-encoding can iterate snapshots in chronological
      order.
- [ ] Identify the canonical "current" snapshot date so the existing
      `_raw/act.json` doesn't duplicate the latest historical entry.

#### Grammar (per design pick — versioned blocks)

- [ ] Add `version <date> { definitions / elements / penalty /
      illustrations / exceptions }` block to `grammar.js`. Each
      version is a complete snapshot; renderers diff client-side.
- [ ] AST: extend `StatuteNode` with `versions: Tuple[VersionedBlock,
      ...]` where each `VersionedBlock` carries an effective date plus
      the same fields as the current `StatuteNode`. The current
      single-version fields (`elements`, `penalty`, …) remain as
      shorthand for a single-version statute.
- [ ] Builder: when multiple `version` blocks are present, populate
      `versions` and leave the top-level fields empty (or pointing at
      the latest version). Lint check: every section either has zero
      `version` blocks (current behaviour) or covers a contiguous
      effective-date range (no gaps, no overlaps).
- [ ] Update parser tests + a fresh `tests/test_versioned_blocks.py`
      pinning shape, ordering, and lint behaviour.

#### Re-encoding pipeline

- [ ] Build `paper/reproducibility/historical_reencode.py`: given the
      `historical_index.json`, dispatch agents to re-encode each
      `(section, date)` snapshot as a `version` block, producing one
      `versioned-statute.yh` per section. Reuse the agentic dispatcher
      shape from `apply_flag_fix.py` / `l3_audit.py`.
- [ ] L3-equivalent fidelity audit per version: extend the 11-point
      checklist with an additional "preserves 1872-era spelling and
      drafting style" check and any structural drift between
      adjacent versions.
- [ ] Coverage harness extension — `coverage.json` rows become
      `(section, valid-date)` keyed.

#### Temporal queries

- [ ] `yuho check --as-of <date> <file>`: filter the AST to the
      version effective on the given date before parse / lint /
      semantic checks.
- [ ] `yuho refs --as-of <date>`: reference graph at a historical
      date.
- [ ] `yuho recommend --as-of <date> <facts>`: charge recommender
      against the law as it stood on the date of the alleged offence.
- [ ] MCP: surface `--as-of` on the corresponding tools.

#### Visualisations

The first one ships with this phase; the others land separately.

- [ ] **Per-section timeline** (v1 — ship first): vertical timeline
      per section showing each version + diff highlights between
      adjacent versions. Embedded on `/s/<N>.html` per-section pages
      after the existing Diagram + Mindmap headings. Format:
      `version 1872-01-01 → version 2008-02-01 → version 2012-12-31`,
      each clickable to reveal the full version content. Diffs
      rendered client-side.
- [ ] **Penalty-inflation heatmap**: 524 sections × decade columns,
      cell colour = imprisonment cap or fine cap. New top-level
      `/penalty-inflation.html` page. Punchy paper figure.
- [ ] **Library-wide amendment graph**: nodes = Acts, edges = "this
      Act amended sections [a, b, c]". New `/amendment-graph.html`
      page alongside `/graph.html` and `/semantic-graph.html`.
- [ ] **Stable-kernel chart**: three-tier classification (verbatim
      since 1872 / partially amended / completely rewritten) rendered
      on `/coverage.html` as a chapter-by-chapter heatmap.

#### Novel concepts (paper contributions)

All four claimed; each gets its own subsection in the paper.

- [ ] **Encoding lineage** — section in design.tex on
      "statute-as-source-of-truth across time". Argues the encoding
      composes over time without external archives.
- [ ] **Amendment friction metric** — define a Levenshtein-style
      distance over AST node trees between adjacent versions; report
      the distribution across the 524-section corpus. New evaluation
      subsection.
- [ ] **Stable kernels** — empirical classification: which sections
      are verbatim from 1872, which are partially amended, which are
      completely rewritten? Report the percentages. New evaluation
      subsection.
- [ ] **Diachronic SCC analysis** — re-run Tarjan over the cross-
      reference graph at every historical date; surface structural
      changes invisible to clause-level diffs. Extends the existing
      §5 SCC subsection.

#### Acceptance criteria for closing Phase 2a

- 524 sections × at-least-3 historical versions encoded (median should
  be 4–5 versions; long tail handled by scrape coverage).
- All temporal queries return correct results when checked against
  hand-picked spot-checks (e.g. s300 in 2010 vs 2013 — known
  death-penalty discretion change).
- Per-section timeline renders for every section that has multiple
  versions; sections with one version skip cleanly.
- Paper has the four novel-concept subsections drafted and figure-
  ready.

### Phase 2b — Vision pivot `(def)`

Only after PC L3 coverage is high and tooling is battle-tested.

- [ ] Evidence Act (EA1893)
- [ ] Criminal Procedure Code
- [ ] Constitution (CONS1963)
- [ ] Contract Law (common law + Misrepresentation Act, Contracts
      (Rights of Third Parties) Act, etc.)
- [ ] Civil remedies and equitable doctrines — require AST shapes Yuho
      doesn't have yet.
