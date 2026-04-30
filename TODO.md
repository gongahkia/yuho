# Yuho — Outstanding Work

Authoritative backlog. Positioning is deliberately narrow:
**a robust DSL + cohesive proof of concept for Singapore criminal law
(Penal Code)**, not a general legal-tech platform.

Primary audience: **researchers, law students, and legal engineers**.
Secondary audience: practising lawyers and government law drafters.
Third tranche: AI-tool builders who need grounded legal corpora and
benchmarks.

Status key: `[ ]` pending · `[~]` in progress · `(def)` deferred.

Current snapshot (2026-04-30 late evening): **12350 unit tests
green · 524 sections at L1+L2 · 524 L3 author-stamped · §6.6
Lean 4 mechanisation v9 (all 5 soundness lemmas + canonical models
kernel-checked, multi-statute `canonical_cross_satisfies`
discharged, cross-library `apply_scope` companion theorems closed,
`CrossRefGraph.acyclic` linter-invariant mechanised +
`acyclic_canonical_cross_satisfies` discharge kernel-checked, v9
`ElementDeep` cross-ref-bearing AST + `crossRef` + `applyScope`
constructors + fuel-bounded evaluator + `Statute.deepBody_compat`
conservative-extension theorem + 6 cross-ref semantics-smoke
theorems kernel-checked + 6 `native_decide` end-to-end deep-eval
smoke fixtures in `Tests/Smoke.lean`) · structural diff harness
**524/524 matched** on full corpus (recursive subsection walker
landed both sides), `--strict` regression gate active
(`make verify-structural-diff-full`) · runtime-eval sweep
**125/125 rich tests passing** (`make verify-runtime-tests`,
wired into `make paper-reproduce`) · §7.8 case-law differential
testing **n=43** (was n=40; +3 chapter-XXIII fixtures from public
eLitigation: PP v GED [2022] SGHC 301, PP v GEH [2022] SGHC 301,
Abdul Ghufran [2025] SGHC 98), **top-1 51.2% / top-3 53.5% /
top-5 53.5%** (was 47.5% / 47.5% / 47.5%) · **defeats-edge SAT
1214/1214 = 100% post-fix** (was 1141/1253 = 91.1% pre-fix; 39
doctrinal-exclusion edges filtered from corpus, 73 encoder-gap
edges closed via referencing-host lift + recursive subsection
walk; per-section history in
`evals/case_law/results-defeats-coverage-classification.json`)
· §7.6 LLM benchmark full 205 fixtures, 4-way prompt sweep ·
Direction B defeats-edge coverage 1214 edges across 142 sections
· **§8 IPC scraper unblocked** — `parse_advocatekhoj_index`
fixed for relative hrefs (commit `a0bea2af`),
`parse_advocatekhoj_section` rewritten for current
`bareacts_contentarea` DOM (commit `4f161471`); index returns
493 sections; **full scrape running in background** (task
`b1hn44gaj`) at 6-second-per-request throttle (~50 min wall
time) · Mermaid `--shape verbose` audit pass — penalty-conditional
diamond rendering bug (silently dead since v1) fixed (commit
`50eae123`); exception priority chain auto-sort by `priority`
field (commit `d825d2e5`); **corpus-wide static syntax sweep
524/524 sections, 0 transpile failures, 0 orphan nodes** wired
as `make verify-mermaid-verbose` regression gate (commit
`363f134b`) · 32-page smoke PDF · `make paper-reproduce`
end-to-end exit 0, summary at
`logs/paper-reproduce-summary.txt`.** Completed history lives
in git log + `docs/PHASE_*` notes.

---

## §6.6 — Lean 4 mechanisation `[~]`

v1–v9 shipped; per-version layout in
[`mechanisation/README.md`](./mechanisation/README.md). Headline:
all 5 soundness lemmas + G8/G14 sentinels + conviction-layer oracle
discharge + cross-library `apply_scope` companion theorems +
v8 acyclicity-invariant mechanisation
(`CrossRefGraph.acyclic` decidable predicate +
`acyclic_canonical_cross_satisfies` discharge) +
v9 deep-element AST (`ElementDeep` with `crossRef` leaf + fuel-
bounded evaluator + `Statute.deepBody_compat` conservative-
extension theorem) kernel-check under Lean 4.10.0 with no
`sorry`s.

- [ ] **v9 follow-ups (depth, not a release blocker).** v9 base
      camp shipped in `mechanisation/Yuho/CrossDeep.lean`:
      `ElementDeep` AST + fuel-bounded `eval` + lift
      `ElementGroup.toDeep` + conservative-extension theorem
      `Statute.deepBody_compat`. Remaining v9 work, all multi-
      session and pay off only under external-review pressure:
      (i) replace `fuel : Nat` with well-founded recursion driven
      by `CrossRefGraph` topological depth, making the v8
      `acyclic` hypothesis load-bearing on termination;
      (ii) recursive `crossRef` semantics (replace the v8-side
      `Statute.convicts` call with `Statute.convictsDeep sigma F
      (n - 1)`); (iii) `crossRef`-bearing strengthening of
      `acyclic_canonical_cross_satisfies`; (iv) `applyScope`
      constructor for substituted-fact element leaves.

---

## §7.8 — Case-law differential testing `[~]`

n=43 fixtures (post-2026-04-30 chapter-XXIII growth via public
eLitigation + Singapore Law Watch, all citations verified by
WebFetch), three scorers (recommend / contrast /
constrained-contrast). Headline numbers: **top-1 51.2%, top-3
53.5%, top-5 53.5%, contrast F1 0.239, constrained-contrast
consistency 100%.** Paper §7.8 prose still cites the n=40 numbers
and needs a refresh on the next paper compile.

- [~] **Further sample growth.** Chapter XXIII closed three slots
      this session (PP v GED [2022] SGHC 301, PP v GEH [2022]
      SGHC 301, Abdul Ghufran [2025] SGHC 98). Remaining gaps —
      all genuinely Penal-Code-track-empty per multi-query
      eLitigation sweeps (chapter II via Internal Security Act,
      chapter XX marriage via Women's Charter, ss359–367
      kidnapping via Kidnapping Act 1961) — cannot grow without
      a deliberate non-PC-source decision. The s364A Au Gan Chye
      [2009] SGHC 124 case is the only s364-family Penal Code
      conviction located, but s364A is not yet encoded in the
      library.
- [ ] **Inter-rater reliability** on the curated fact patterns.
      A second human curator extracts facts from the same judgments
      independently; compute κ score for §7.8's threats-to-validity
      caveat. Cannot be done by Claude (defeats the inter-rater
      claim); requires user action.
- [ ] **s364A path closed.** The Au Gan Chye [2009] SGHC 124
      kidnapping case was prosecuted under s364A, but s364A was
      repealed before the current 2020 PC revision; encoding
      repealed sections is out of scope (Phase 2a — historical
      versions — is deferred). The chapter XV reported case-law
      slot therefore remains gappable only through the
      Kidnapping Act 1961, which is not on the encoded-PC scope.

---

## §8 — Cross-jurisdiction comparative encoding `[~]`

The IPC scraper (`scripts/scrape_indiacode.py`) is committed and
2026-04-30 working — fixed `parse_advocatekhoj_index` for
relative-href shape (commit `a0bea2af`) and rewrote
`parse_advocatekhoj_section` for the current `bareacts_contentarea`
DOM (commit `4f161471`). Index returns 493 sections (s1–s511 with
gaps for repealed sections).

- [~] **First IPC scrape run.** Background task `b1hn44gaj` — `python
      scripts/scrape_indiacode.py act --out
      library/indian_penal_code/_raw/act.json` running at
      6-second-per-request throttle (~50 min wall time). Spot-check
      first few section JSONs on completion.
- [ ] Encode at full coverage (493 IPC sections) using the
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

Recently closed (2026-04-30 PM session, all in-session):

* **Defeats-edge SAT 91.1% → 100%.** Doctrinal-exclusion filter
  (commit `6cd7b7f6`) drops 39 interpretation-only mis-pairings
  from the fixture corpus; recursive subsection walker
  (`d2b1e7e3`, `bf079f8b`) flattens nested elements on both
  Z3-side and Lean-side fixture generators (s305 / s420A / s74);
  `referencing`-host element lift (`00d56692`) closes 56
  punishment-only-section edges. Re-sweep shows 1214/1214 SAT
  (`7a262f30`); `make verify-structural-diff-full --strict` exit 0
  (524/524 matched).
* **Runtime sweep 100 → 105.** Behavioural companions for s132 /
  s133 / s136 / s137 / s138 (5 commits ending in
  `<sNNN>` series).
* **§6.6 v9 deepening.** `applyScope` constructor + 6 semantics-
  smoke theorems (`eval_crossRef_resolves` /
  `eval_applyScope_resolves` + missing / zero-fuel variants)
  kernel-checked (commit `1f9fdbb3`).

Claude-driven (no user action needed):

1. **Test-suite backlog continuation (incremental).** The
   110/110 runtime sweep covers 110 of the 524 sections. Next
   batch candidates with offence-style elements + penalty:
   s150, s151, s152, s153, s154 (continuing the Chapter VIII
   unlawful-assembly + public tranquillity cluster). ~10–15 min
   per section.

2. **§6.6 v9 deepening (multi-session, optional).** Remaining
   v9 follow-ups: (i) replace `fuel : Nat` with well-founded
   recursion driven by `CrossRefGraph` depth — acyclicity
   becomes load-bearing on termination, completing the §6.6
   boundary statement; (ii) recursive `crossRef` / `applyScope`
   semantics (replace v8 `Statute.convicts` delegation with deep
   recursion at each cross-ref); (iii) `crossRef`-bearing
   strengthening of `acyclic_canonical_cross_satisfies`. Pays
   off only on external-review pressure.

3. **Grammar restructure for comment-before-struct bug**
   (multi-session). Tree-sitter LR parser truncates `Foo p :=
   Foo { … }` at `Foo` when a `// …` or `/* … */` comment
   appears earlier in the file; `prec`/`prec.dynamic`
   workarounds insufficient. Real fix needs grammar restructure
   (variable_declaration terminator, or hoist type-name+`{`
   into a single token). Mitigated today via comment-strip pass
   + runtime-sweep regression gate (commit `ccca70dd`).

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

### Mermaid flowchart richness `[~]` — code-level audit done

`--shape verbose` v1 shipped in
`src/yuho/transpile/mermaid_transpiler.py`: per-element decision
diamonds, priority-ordered exception chains, per-conditional
penalty branches. 2026-04-30 audit pass closed two silent bugs:

* **Penalty-conditional rendering** read `pen.when_condition` /
  `pen.when` (commit `50eae123`) but `PenaltyNode` actually
  carries the G9 conditional identifier on `pen.condition` —
  the conditional-penalty diamonds had been silently dead since
  v1 landed; verified working on s130 (`life_imprisonment_sentence`
  / `non_life_sentence` chain renders correctly).
* **Exception priority chain auto-sort** (commit `d825d2e5`) —
  the loop now sorts by `exc.priority` (lower = higher
  priority, rendered first; null priorities fall through in
  source order at the tail). Previously the chain rendered in
  source order, drifting silently for hand-edited sections that
  interleaved priorities.
* **Static syntax sanity** — verbose output for s300 has 44
  nodes, 41 referenced in edges, 0 orphans, 16 diamonds, 28
  rectangles. No parse-error structure detected by static
  inspection.

- [ ] **Doctrinal fidelity audit on diamond labels.** Long
      element descriptions are truncated and rendered as inline
      diamond labels. Whether the truncation preserves doctrinal
      meaning is a content-audit question that needs a human
      reader. Some labels may need tooltips rather than inline
      glyphs — Mermaid does not natively support tooltips on
      diamonds, so the alternative is to shorten on the encoder
      side. (User action.)
- [ ] **`mmdc` rendering smoke** — run verbose output through
      the Mermaid CLI to confirm visual layout. Local
      `mmdc` install needs `npx puppeteer browsers install
      chrome-headless-shell` (Chrome download). Falls back to
      the Mermaid Live Editor / explorer site. (User action;
      Claude has no display target.)

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
