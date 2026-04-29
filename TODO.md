# Yuho — Outstanding Work

Authoritative backlog. Positioning is deliberately narrow:
**a robust DSL + cohesive proof of concept for Singapore criminal law
(Penal Code)**, not a general legal-tech platform.

Primary audience: **researchers, law students, and legal engineers**.
Secondary audience: practising lawyers and government law drafters.
Third tranche: AI-tool builders who need grounded legal corpora and
benchmarks.

Status key: `[ ]` pending · `[~]` in progress · `(def)` deferred.

Current snapshot (2026-04-29): **12270 unit tests green · 524
sections at L1+L2 · 524 L3 author-stamped · §6.6 Lean 4 mechanisation
v8 (all 5 soundness lemmas + canonical models kernel-checked,
multi-statute `canonical_cross_satisfies` discharged, cross-library
`apply_scope` companion theorems closed, `CrossRefGraph.acyclic`
linter-invariant mechanised + `acyclic_canonical_cross_satisfies`
discharge kernel-checked) · structural diff harness 524/524
matched on full corpus, `--strict` regression gate active
(`make verify-structural-diff-full`) · runtime-eval sweep 95/95
rich tests passing (`make verify-runtime-tests`, wired into
`make paper-reproduce`) · §7.8 case-law differential testing
n=40 · §7.6 LLM benchmark full 205 fixtures, 4-way prompt sweep
· Direction B defeats-edge coverage 1253 edges across 147
sections · 32-page smoke PDF · `make paper-reproduce` end-to-end
including Lean kernel-check + runtime sweep.** Completed history
lives in git log + `docs/PHASE_*` notes.

---

## §6.6 — Lean 4 mechanisation `[~]`

v1–v8 shipped; per-version layout in
[`mechanisation/README.md`](./mechanisation/README.md). Headline:
all 5 soundness lemmas + G8/G14 sentinels + conviction-layer oracle
discharge + cross-library `apply_scope` companion theorems +
v8 acyclicity-invariant mechanisation
(`CrossRefGraph.acyclic` decidable predicate +
`acyclic_canonical_cross_satisfies` discharge) kernel-check
under Lean 4.10.0 with no `sorry`s.

- [ ] **v9 — lift cross-section refs into `Element.eval`** (depth,
      not a release blocker). Add an `Element.kind` constructor for
      `is_infringed(n)` / `apply_scope(n, F')`, with `Element.eval`
      recursively consulting the section table; the v8 acyclicity
      hypothesis becomes load-bearing on the recursion's well-
      foundedness at that point. Multi-session work; pays off only
      under external-review pressure.

---

## §7.8 — Case-law differential testing `[~]`

n=40 fixtures, three scorers (recommend / contrast /
constrained-contrast). Headline numbers in paper §7.8: top-1 47.5%,
top-3 47.5%, MRR 0.480, contrast F1 0.239, constrained-contrast
consistency 100% (n=25).

- [ ] **Further sample growth (user action — needs eLitigation /
      LawNet access).** Chapter coverage gaps documented in
      [`evals/case_law/README.md`](./evals/case_law/README.md)
      under *Coverage gaps — sample growth roadmap* (chapter II
      state offences, chapter XX marriage, chapter XXIII
      modesty/voyeurism, ss363–367 kidnapping). Fixture template
      ready at
      `evals/case_law/fixtures/case-template-chapter-xxiii.yaml.template`;
      author copies it, fills in a verified `case_url`, drops the
      file in `fixtures/`, and re-runs the three scorers. Claude
      blocked on this by the truth-verification rule (cannot
      fabricate citations); user has the access.
- [ ] **Inter-rater reliability** on the curated fact patterns.
      A second human curator extracts facts from the same judgments
      independently; compute κ score for §7.8's threats-to-validity
      caveat. Cannot be done by Claude (defeats the inter-rater
      claim); requires user action.

---

## §8 — Cross-jurisdiction comparative encoding `[ ]`

The IPC scraper (`scripts/scrape_indiacode.py`) is committed and
fixture-tested.

- [ ] **First IPC scrape run** (user action): `python
      scripts/scrape_indiacode.py act --out
      library/indian_penal_code/_raw/act.json` (~50 minutes against
      the AdvocateKhoj backend). Spot-check the first few section
      JSONs.
- [ ] Encode at full coverage (511 IPC sections) using the
      agent-dispatch shape from Phase D — months of agent runs.
- [ ] Comparative analysis tool: `yuho refs --compare-libraries`
      emitting SCC overlap, divergent amendment paths, sections
      renumbered / added / repealed.
- [ ] **Paper §8 prose** writing the comparative findings.

---

## Research paper polish `[~]`

arXiv-attributed acmart `manuscript` mode for now; AI&L documentclass
swap on submission day.

- [ ] **Manual read-through pass.** Read the rendered PDF cover-to-
      cover, mark prose drift, missing citations, paragraphs that
      bury the lede. Detail where missing (especially evaluation §5
      and limitations §11) but stay tight. (User action.)
- [ ] **§6.6 / §11 staleness audit.** Read every "remaining gap" /
      "future work" / "out of scope" sentence and confirm it's still
      accurate. (User action; doubles as the read-through above.)
- [ ] **External-reader pass on the full PDF.** Catches drift both
      author and AI miss.
- [ ] **Local lualatex compile of arxiv.tar.gz.** Bundle structurally
      complete (`make arxiv` ships 24 files, 83K). Local lualatex
      blocked on `sudo tlmgr install latexmk hyperxmp`. arXiv's
      TeXLive has the full toolchain so this is verification-only.
      User action.

---

## Hardening `[~]`

- [ ] **Run `make paper-reproduce` end-to-end periodically.** Confirms
      every empirical claim still reproduces; now includes the 90/90
      runtime-eval sweep.
- [ ] **Mermaid `--shape verbose` audit** — see *Mermaid flowchart
      richness* below. User action.
- [ ] **Grammar restructure for comment-before-struct-instantiation
      bug.** Tree-sitter LR parser truncates `Foo p := Foo { … }`
      at `Foo` when any `// …` or `/* … */` comment appears earlier
      in the file; `prec`/`prec.dynamic` workarounds insufficient.
      Real fix needs grammar restructure (variable_declaration
      terminator, or hoist type-name+`{` into a single token) or
      tree-sitter parser upgrade. Mitigated today via the
      comment-strip pass (commit `ccca70dd`) + the runtime sweep
      (`make verify-runtime-tests`) acting as a regression gate.
      Authoring guidance lives in
      [`docs/grammar-quirks.md`](./docs/grammar-quirks.md).

---

## Reproducibility — Zenodo deposit `[ ]`

Dockerfile + Makefile + REPRODUCE.md shipped.

- [ ] Submission-day plumbing: zip v1.0 corpus + benchmark fixtures
      + AKN XSD + Lean mechanisation, upload to Zenodo, cite the DOI
      in `paper/REPRODUCE.md`. Triggered on paper submission.

---

## Risk register

| Risk | Mitigation |
|---|---|
| External counsel access not available | L3 stays author-stamped; §11 carries the explicit caveat |
| IPC text access blocked (paywall, robots.txt change) | Switch to Bangladeshi PC 1860 (Anglo-Indian lineage, public-domain text) |
| AI&L editorial rejection | Re-target *Formal Aspects of Computing* or ICAIL |
| Panellist presses on residual oracle scope | §6.6 + §11 v7 prose frames the discharge: conviction-layer oracle gone, full-corpus structural diff 524/524 matched |

---

## What to work on next (recommendation)

Recently closed (2026-04-29 session): structural-diff `--strict`
regression gate (commit `21472323`); behavioural-test ramp
+5 sections taking the runtime sweep to 95/95 (commit `067b6370`);
§6.6 v8 cross-section-reference acyclicity invariant mechanised
(commit `3b21401c`). The Claude-tractable shortlist below is the
*next* batch of items, not the one just shipped.

Claude-driven (no user action needed):

1. **Test-suite backlog continuation (next 5–10 sections).**
   The 95/95 runtime sweep currently covers 95 of the 524
   sections. Next batch candidates:
   `s127_receiving_property_taken_war_depredation`,
   `s128_public_servant_voluntarily_allowing_prisoner`,
   `s130D_genocide` (if not already covered),
   `s171_wearing_garb_carrying_token_used_public`,
   `s182_false_information_intent_cause_public`. Each adds a
   fixture to `make verify-runtime-tests`. ~10–15 min per
   section.

2. **Defeats-edge structural-coverage extension.** Direction B
   currently sits at 1141/1253 = 91.1% SAT. The remaining 112
   defeats edges fail SAT under specific element-conjunction
   shapes; a sweep of the failure set (logged in
   `evals/case_law/results-defeats-coverage.json`) would
   classify each as (a) fixture bug, (b) genuine doctrinal
   exclusion, or (c) encoder gap. ~1–2 hr.

3. **§6.6 v9 (depth, optional)** — lift cross-section refs
   into `Element.eval` so the v8 acyclicity hypothesis becomes
   load-bearing on well-founded recursion. Tracked under §6.6
   above; multi-session and pays off only on external-review
   pressure.

User-blocked items (no Claude work possible until you act):

* §7.8 sample growth — needs eLitigation access; chapter
  XXIII fixture template ready at
  `evals/case_law/fixtures/case-template-chapter-xxiii.yaml.template`.
* §7.8 inter-rater reliability — needs a second human curator.
* §8 IPC scrape — needs the ~50-min `scripts/scrape_indiacode.py
  act` command run against AdvocateKhoj.
* Paper read-through / external-reader pass / lualatex compile —
  user actions per *Research paper polish*.
* Mermaid `--shape verbose` audit — flagged for human.

---

## Long-tail / stretch

### VS Code extension marketplace publish `[ ]`

Extension feature-complete.

- [ ] Marketplace publish (stretch).

### Akoma Ntoso transpiler hardening `[ ]`

Structural transpiler validates 524/524 against vendored OASIS XSD.

- [ ] Decision criterion before further extension (richer FRBR
      hierarchy, full `<componentRef>` graph): a named external user
      asks for it.

### Mermaid flowchart richness `[~]` — **FLAGGED FOR HUMAN AUDIT**

`--shape verbose` v1 shipped in
`src/yuho/transpile/mermaid_transpiler.py`: per-element decision
diamonds, priority-ordered exception chains, per-conditional penalty
branches. The verbose shape is a mechanical rewrite that needs human
audit before being relied on for documentation, teaching, or
reviewer-facing rendering.

- [ ] Diamond labels — confirm doctrinal fidelity for long element
      descriptions; some labels may need a tooltip rather than an
      inline glyph (Mermaid does not natively support tooltips on
      diamonds).
- [ ] Exception priority chain — currently rendered in source order;
      AST visitor does NOT auto-sort by `priority` field. Audit
      output against sections that use explicit priorities (e.g.
      s300 Exceptions 1-7 are in priority order already; newer
      hand-edited sections might diverge).
- [ ] Penalty-conditional rendering — verify the AST attribute
      access in `_transpile_statute_verbose` (`pen.when_condition`
      then fallback `pen.when`) actually reads the `when` clause.
      Spot-check on a multi-penalty section (s404 carries
      `penalty when clerk_or_servant_case`; s302 has unconditional
      penalty).
- [ ] Mermaid render — run the verbose output through `mmdc` / the
      explorer site; confirm no syntax errors / no orphaned nodes.
      The 28 Mermaid unit tests cover the default `statute` shape
      only.

### Test-suite backlog `[ ]`

82 sections carry behavioural-test companions; 442 sections are
pure-interpretation provisions where structural parse + lint coverage
is the appropriate bar.

- [ ] **442 sections without behavioural companions.** Author per-
      section companions opportunistically when an offence gains
      structural complexity that warrants behavioural testing.

### Yuho interpreter assertion-eval

Closed 2026-04-29 via option (a). Comment-strip pass applied to
all 92 rich `test_statute.yh` files, runtime sweep harness
(`scripts/verify_runtime_tests.py`) wired into
`make verify-runtime-tests` and `make paper-reproduce`. Current
result: **90/90 rich tests pass assertion eval**. Grammar
limitation documented at
[`docs/grammar-quirks.md`](./docs/grammar-quirks.md). Future
regressions surface as CI failures rather than silent pass-then-
fail-at-runtime.

---

## Notes for fresh contributors

- **Hypothesis dep.** Already declared in `pyproject.toml` under
  `[dev]`. To run property-based tests
  (`tests/test_properties.py`, `tests/test_statutes.py`), install
  with `pip install -e .[dev]`. CI configurations should pin to the
  `[dev]` extra so the property suite participates.

- **Lean toolchain.** `mechanisation/` requires Lean 4.10.0+ via
  `elan`. Install with `curl -sSf
  https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh
  | bash`, then `cd mechanisation && lake build`.

---

## Deferred — Phase 2a (Historical versions)

The Penal Code 1871 has accumulated 150+ years of amendments. Yuho
currently encodes only the current version of each section. Phase 2a
extends Yuho into a **diachronic** legal artefact: every section
carries every historical version, and the toolchain answers "what
did the law look like on date X?" temporally.

**Scope:** every encoded section gets every historical version since
1872. `yuho check --as-of 1995-06-15 my_facts.yh` and friends become
first-class queries.

### Scrape + ingest

The v0 scrape ships (`scripts/scrape_sso.py historical-list /
historical / historical-bulk`); per-Act snapshots land under
`_raw/historical/<act>/<YYYYMMDD>.json` with a sibling
`historical_index.json`.

- [ ] Build a `historical_index.json` mapping `(section, valid-date)
      → raw_path` so re-encoding can iterate snapshots in
      chronological order.
- [ ] Identify the canonical "current" snapshot date so the existing
      `_raw/act.json` doesn't duplicate the latest historical entry.

### Grammar (versioned blocks)

- [ ] Add `version <date> { definitions / elements / penalty /
      illustrations / exceptions }` block to `grammar.js`.
- [ ] AST: extend `StatuteNode` with `versions:
      Tuple[VersionedBlock, ...]`.
- [ ] Builder: when multiple `version` blocks are present, populate
      `versions` and leave the top-level fields empty. Lint check
      for contiguous effective-date ranges.
- [ ] Update parser tests + `tests/test_versioned_blocks.py`.

### Re-encoding pipeline

- [ ] Build `paper/reproducibility/historical_reencode.py`: given
      `historical_index.json`, dispatch agents to re-encode each
      `(section, date)` snapshot as a `version` block.
- [ ] L3-equivalent fidelity audit per version: extend the 11-point
      checklist with a "preserves 1872-era spelling and drafting
      style" check.
- [ ] Coverage harness extension — `coverage.json` rows become
      `(section, valid-date)` keyed.

### Temporal queries

- [ ] `yuho check --as-of <date> <file>`.
- [ ] `yuho refs --as-of <date>`.
- [ ] `yuho recommend --as-of <date> <facts>`.
- [ ] MCP: surface `--as-of` on the corresponding tools.

### Visualisations

- [ ] **Per-section timeline** (v1 — ship first). Vertical timeline
      per section with diff highlights, embedded on `/s/<N>.html`.
- [ ] **Penalty-inflation heatmap**: 524 sections × decade columns,
      cell colour = imprisonment / fine cap.
- [ ] **Library-wide amendment graph**: nodes = Acts, edges = "this
      Act amended sections [a, b, c]".
- [ ] **Stable-kernel chart**: three-tier classification (verbatim
      / partially amended / completely rewritten) on
      `/coverage.html`.

### Novel concepts (paper contributions)

- [ ] **Encoding lineage** — section in design.tex on
      "statute-as-source-of-truth across time".
- [ ] **Amendment friction metric** — Levenshtein-style distance
      over AST node trees between adjacent versions; report the
      distribution across the 524-section corpus.
- [ ] **Stable kernels** — empirical classification of section
      stability since 1872.
- [ ] **Diachronic SCC analysis** — re-run Tarjan over the
      cross-reference graph at every historical date; surface
      structural changes invisible to clause-level diffs.

### Acceptance criteria

- 524 sections × at-least-3 historical versions encoded.
- All temporal queries return correct results on hand-picked
  spot-checks (e.g. s300 in 2010 vs 2013 — known death-penalty
  discretion change).
- Per-section timeline renders for every section with multiple
  versions.
- Paper has the four novel-concept subsections drafted.

---

## Deferred — Phase 2c Direction D (Interactive learn-by-doing)

Extend the static explorer site into a guided learning surface for
law students. Each section page gains an interactive fact-builder;
elements light up as the student supplies fact values; the verdict
updates live.

- [ ] Per-section JS fact-builder component: parses the section's
      element list from the existing JSON corpus, renders boolean /
      enum / numeric inputs, calls the in-browser evaluator (compile
      `StatuteEvaluator` to Pyodide or write a tiny TS port).
- [ ] Worked-example walkthrough per section: takes the canonical
      illustrations from the `.yh` source, plays them through the
      fact-builder one step at a time. Mode toggle: "show me how it
      gets to the answer" vs "let me try myself first".
- [ ] If Phase 2a lands first: integrate the per-section timeline so
      a student can replay the same fact pattern against the law as
      it stood in 1872, 1985, 2008, 2024 — directly visible
      doctrinal drift.
- [ ] **Paper claim:** "Interactive structural pedagogy for common-
      law penal codes". Co-author with a law-school educator who can
      run a classroom trial; report measured learning outcomes vs
      textbook control.

---

## Deferred — Phase 2b (Vision pivot)

Only after PC L3 coverage is high and tooling is battle-tested.

- [ ] Evidence Act (EA1893)
- [ ] Criminal Procedure Code
- [ ] Constitution (CONS1963)
- [ ] Contract Law (common law + Misrepresentation Act, Contracts
      (Rights of Third Parties) Act, etc.)
- [ ] Civil remedies and equitable doctrines — require AST shapes
      Yuho doesn't have yet.

---

## Post-submission — arXiv publish + cross-link `[ ]`

Triggered the moment the paper is done (all "Research paper polish"
items above closed).

- [ ] **Build the arXiv tarball.** `cd paper && make paper && make
      arxiv`. Confirm `paper/arxiv.tar.gz` is produced and includes
      `00README.XXX`, `main.tex`, `main.bbl`, `sections/`,
      `figures/*.tex`, `references.bib`, `stats.tex`,
      `stats-extra.tex`, `yuho-listing.sty`,
      `methodology/methodology.tex`.
- [ ] **Upload to arXiv** (`gabrielzmong@gmail.com`, primary
      `cs.PL`, cross-list `cs.LO` + `cs.CY` + optional `cs.SE`).
      First-time `cs.*` submissions typically need endorsement;
      secure an endorser before upload day.
- [ ] **Record the arXiv ID + DOI.** Save the assigned
      `arXiv:YYMM.NNNNN` ID to `paper/REPRODUCE.md` next to the
      Zenodo deposit DOI.
- [ ] **Cross-link from `README.md`.** Add a "Paper" section near
      the top linking to the arXiv abstract page and the source
      build (`cd paper && make paper`).
- [ ] **Cross-link from `gongahkia.github.io`.** Add a paper entry
      to the personal site (publications / projects section) with
      the arXiv link and a one-line abstract pointer.
