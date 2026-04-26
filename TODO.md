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

## PhD-rigor hardening — single-paper expansion `[ ]`

All five rigor additions below land in **the same paper**, not
separate submissions. Each becomes a new section (Gaps 1, 2, Opp
A) or extends an existing section (Gaps 3, 4 slot into
`§Evaluation`). Mechanisation (Gap 5) becomes either a
present-tense subsection (if it lands in time) or a "future work"
pointer in `§Limitations` (if it doesn't). The paper grows from
the current 25 pages to ~60-80 pages — a journal-grade artefact.

**Venue:** *Artificial Intelligence and Law* (Springer journal)
— handles 60-80 page submissions naturally, audience is
dual-trained (legal-tech + formal methods), and is the target
venue Catala / DAPRECO / LegalRuleML follow-on work uses. AI&L's
dual-trained reviewers also cleanly absorb the legal-tech-first
empirical case + formal-methods-defence rigor stack we're
building. ICAIL / JURIX would also accept the work but the page
budget is tighter and the journal version reads as the canonical
record anyway.

**Sequencing (Shape A — ship-once):**

The paper submits to AI&L only once **everything** is done — Gaps
1-5 + Opportunity A all landed and present-tense in the
manuscript. Slower wall-clock (9-15 months) but the submission is
a finished artefact and avoids the risk of a "come back when §8
is done" rejection.

1. **Months 1-3** — Gaps 1, 2, 4 in parallel where possible:
   - Gap 1 (operational semantics): independent paper-writing
     work, can ship while corpus encoding runs.
   - Gap 2 (pen-and-paper soundness): depends on Gap 1; landed
     immediately after.
   - Gap 4 (case-law differential testing): curate cases in
     month 2-3; encode + score in month 3.
2. **Months 2-9** — Opportunity A (IPC or MPC encoding):
   - Scrape the foreign code in month 2-3 (in parallel with Gaps
     3-4 above).
   - Agent-dispatched encoding to L1+L2 over months 4-7 (mirrors
     Phase D's SG PC pace).
   - Cross-jurisdiction analysis + §8 prose in months 8-9.
3. **Months 6-12** — Gap 5 mechanisation. Started in month 6
   (after Gaps 1-2 land the pen-and-paper artefacts the
   mechanisation reproduces) and runs to month 12. Catala's
   comparable mechanisation (full default-calculus +
   compilation correctness) was a multi-quarter PhD project; we
   budget similarly.
4. **Months 12-15** — Paper-writing trench: integrate every
   shipped piece into the AI&L manuscript; final-pass
   read-through (the existing TODO bullet); submit.

This shape is the *Catala-as-it-would-have-been-written* pattern
— if Catala had waited until the Coq mechanisation was done
before submitting POPL'21, they would have shipped one paper
instead of two. We're choosing that path deliberately, which
means slower-but-completer rather than faster-but-iterative.

**Target paper structure** (each gap maps to a section):

| Section | Source |
|---|---|
| §1-3 (Intro / Background / Design) | Existing |
| §4 Formal semantics | **Gap 1** |
| §5 Implementation | Existing |
| §6 Transpiler soundness | **Gap 2** (+ Gap 5 mechanisation subsection if it lands) |
| §7 Evaluation | Existing + **Gap 4** (§7.8) |
| §8 Comparative encoding | **Opportunity A** |
| §9-12 Related / Applicability / Limitations / Conclusion | Existing |
| Appx A — full inference rules | Gap 1 detail |
| Appx B — full soundness proofs | Gap 2 detail |
| Appx C — mechanisation listing | Gap 5 (if shipped) |

### §4 of the paper — Pinned operational semantics `[x]`

Shipped at `paper/sections/semantics.tex`. Five subsections:
preliminaries (syntactic + semantic domains, judgement
shapes), element evaluation (small-step rules for actus_reus /
mens_rea / circumstance + all_of / any_of combinators),
exception precedence (Catala-style default-logic with explicit
defeats DAG), cross-section composition (is_infringed +
apply_scope), and penalty algebra (cumulative / or_both
combinators reducing to range pairs). Full inference rules
inventoried in Appendix A; body fragment is the page reviewers
follow without the appendix.

### §6 of the paper — Soundness theorem for the Z3 transpiler `[~]`

Pen-and-paper proof shipped at `paper/sections/soundness.tex`.
Theorem 6.1 (Z3-Operational Soundness): every satisfying Z3
assignment's `<sX>_conviction` truth value equals the
operational-semantic conviction judgement on the corresponding
fact pattern. Proof decomposes into **five** lemmas — element /
element-graph / exception / cross-section / **penalty**
correspondence — plus the main theorem. Penalty correspondence
(Lemma 6.5) lifted into a parallel correspondence lemma after
review feedback so the soundness claim covers the full encoded
library, not just the conviction layer.

Empirical witnesses shipped at `tests/test_soundness_sanity.py`
(8 tests) — one concrete-case witness per lemma. The tests pin
specific cases (true/false leaves, all_of/any_of combinators,
exception firing alongside satisfied elements, conviction-Bool
name dedupe across spellings, finite imprisonment range, G8
unlimited-fine sentinel) so regressions surface here rather than
silently invalidating the paper's soundness claim.

Remaining work:

- [ ] Mechanisation in Coq or Lean — see §6.3 below
      (deliberately deferred).

### §7.8 of the paper — Differential testing against published case law `[x]`

Shipped. `evals/case_law/` carries 23 curated SG criminal-case
fixtures + three orthogonal scorers (`score_recommend.py`,
`score_contrast.py`, `score_contrast_constrained.py`) +
README.md + tests. Headline numbers wired into the paper at
\S\ref{subsec:case_law_diff}: top-1 30.4% / top-3 34.8% / MRR
0.326 / unconstrained-contrast F1 0.188 / constrained-contrast
consistency 100%. The 100% consistency-rate is the load-bearing
positive finding: every court's stated element-level reasoning
is satisfiable in the encoded model.

Possible follow-ups (not in scope for §7.8 v1):

- [ ] **Grow case-law sample via manual curation from LawNet /
      Singapore Law Watch.** v1 ships 23 fixtures derived from
      training-data recall + an LLM research agent; this is
      necessary but not sufficient. The next trench requires
      *actual research*: sit with LawNet open, read judgments,
      hand-extract fact patterns, verify citations, and grow
      coverage to 50+ fixtures with the chapter-spread gaps
      (XX offences relating to marriage, XXII criminal
      intimidation, more XVII property-offence cases —
      s378 theft, s392 robbery, s415/420 cheating, s425 mischief,
      s441 criminal trespass — currently underrepresented).
      Some of the existing fixtures may also need verification
      against the judgments themselves; spot-check the
      `case_summary` and `fact_facts` mappings.
- [ ] Inter-rater reliability on the curated fact patterns. A
      second curator (human, not LLM) extracts facts from the
      same judgments independently; compute κ score for §7.8's
      threats-to-validity caveat.

### §8 of the paper — Cross-jurisdiction comparative encoding `[ ]`

The 1860/1871 Anglo-Indian PC family (Singapore, Malaysia, India,
Pakistan, Brunei) shares structural shape with divergent amendment
trajectories. No peer system can run this comparison — Catala is
French tax only, lam4 is contract fragments, DAPRECO is GDPR only.
Yuho is uniquely positioned. The full encoding lands as `§8` of
the paper. (Also tracked under Phase 2c Direction A; cross-link.)

- [x] **IPC scraper shipped** — `scripts/scrape_indiacode.py` with
      two HTML backends (AdvocateKhoj primary, India Code official
      fallback), CLI subcommands `index` / `section` / `act`,
      stdlib `urllib` (no Playwright needed since both sources are
      server-rendered), 6 s crawl-delay, output JSON shape mirrors
      `scrape_sso.py` so downstream encoders iterate the IPC the
      same way they iterate the SG PC. 8 fixture-based tests pin
      the parsers without network. **First real run is the
      user's:** `python scripts/scrape_indiacode.py act --out
      library/indian_penal_code/_raw/act.json` (~1 hour at
      6 s/request × ~511 sections).
- [ ] Encode at full coverage (511 IPC sections) using the same
      agent-dispatch shape that Phase D used for the SG PC. The
      long pole — months of agent runs.
- [ ] Comparative analysis: SCC overlap, divergent amendment
      paths, sections renumbered / added / repealed. Single tool
      (`yuho refs --compare-libraries`) emits the diff report.
- [ ] **Paper §8 prose** writing the comparative findings.

### §6.6 of the paper — Lean 4 mechanisation `[~]`

**v1 shipped** at `mechanisation/` (Lean 4.10.0, ~5 source
files + smoke tests + README). Two paper-load-bearing lemmas
kernel-checked:

- [x] **Lemma 6.2 (element correspondence)** — theorem
      `element_correspondence` in `Yuho/Soundness.lean`. Proof
      is `rfl` after unfolding `Element.eval` and
      `SMTModel.facts`.
- [x] **Lemma 6.4 (exception correspondence)** — theorem
      `exception_correspondence`. Catala-style priority
      precedence realised by the operational definition of
      `Exception.firedSet` walking the exception list in
      topological order.
- [x] **Composed corollary** `partial_conviction_correspondence`
      pairing the two lemmas.
- [x] **Paper §6.6 added** — `\subsection{Partial mechanisation
      in Lean 4}` documenting what's mechanised, the boundary,
      the trust base (Lean kernel + oracle assumption that the
      Z3 generator faithfully emits the biconditionals), the
      Coq-vs-Lean rationale.
- [x] **Limitations §11 updated** to flag the partial nature
      and size the remaining work (~6-9 person-months for
      Lemmas 6.3 / 6.5 / 6.6; mirroring Catala's
      `simulation_sred_to_cred.v` template).

Possible follow-ups (deferred to v2):

- [ ] Mechanise Lemma 6.3 (element-graph correspondence) — the
      structural twin of Catala's bisimulation lemma; ~2-3
      person-months.
- [ ] Mechanise Lemma 6.5 (penalty correspondence) — Yuho-specific,
      requires lifting range-arithmetic into Lean; ~2 person-months.
- [ ] Mechanise the cross-section composition step of Theorem 6.1
      (apply\_scope / is\_infringed dedupe simulation) — ~2-3
      person-months.
- [ ] Discharge the oracle assumption by porting Yuho's Python
      `Z3Generator` to Lean and proving its functional equivalence
      to a verified specification.

### Reproducibility artefact (AEC-grade) `[~]`

Two of three deliverables shipped — only the Zenodo DOI remains
(non-code, lands on submission day).

- [x] **Dockerfile** at repo root + `.dockerignore` boots a clean
      Python 3.12 image with the full toolchain (Python deps via
      `pip install -e .[dev]`, Node + tree-sitter-cli, xmllint
      for the AKN round-trip).
- [x] **Top-level Makefile** with `make paper-reproduce` that
      runs every empirical claim end-to-end (verify-coverage /
      verify-akn-xsd / verify-evals / verify-case-law) in ~3
      minutes and emits a one-page summary at
      `logs/paper-reproduce-summary.txt`. Each verify-* target
      is independently runnable; `PYTHON` and `YUHO` make
      variables let users override interpreter / CLI for hosts
      with broken default Pythons.
- [x] **`paper/REPRODUCE.md`** documents every paper claim with
      a per-claim verification command, expected output, expected
      wall-clock time, and what's deliberately *not* covered by
      `paper-reproduce` (real-LLM benchmark, full IPC scrape).
- [ ] **Zenodo deposit** of the v1.0 corpus + benchmark fixtures
      + AKN XSD with a citable DOI. Triggered on paper
      submission; nothing to do until then.

### Risk register

| Risk | Mitigation |
|---|---|
| Gap 5 mechanisation overruns | §6.3 demotes to future-work pointer; §6.2 pen-and-paper carries the soundness claim alone |
| External counsel access not available | L3 stays author-stamped; §11 Limitations carries the explicit caveat that external review is not part of this paper's claim |
| IPC/MPC text access blocked (paywall, robots.txt change) | Switch to the Bangladeshi PC 1860 (also Anglo-Indian lineage, public-domain text) |
| AI&L editorial rejection | Re-target *Formal Aspects of Computing* (legal-tech amenable) or ICAIL (page budget tighter but acceptable) |
| Case-law sample for §7.8 has too few clean single-charge cases | Widen to multi-charge cases; score per-charge top-k accuracy; drop the "single charge" cleanliness constraint |

### Cross-cutting notes

The §4 + §6 (formal semantics + soundness) layer is the **rigor
defence** against formal-methods-trained reviewers; §7.8
(case-law differential testing) is the **empirical case**;
§8 (cross-jurisdiction) is the **uniqueness claim**. All three
are needed for an AI&L journal submission of this scope; missing
any one weakens the paper to "interesting tooling" rather than
"PhD-thesis-grade contribution".

The 12-month-budget is realistic given existing Phase D agent-
dispatch tooling (re-used for Opportunity A's IPC/MPC encoding).
The biggest single risk is Gap 5 (mechanisation) — it's the only
item that has no incremental fallback if it overruns; if the
mechanisation goes sideways the paper still ships with §6.3 as a
future-work pointer.

**Overlap with deferred sections:** §8 supersedes Phase 2c
Direction A (Cross-jurisdiction PC port) — the Direction-A
bullets below are absorbed into §8.

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
- [ ] Inspect rendered Mermaid figures (`paper/figures/*.pdf` already
      generated by `make figures`) and tune layouts where needed.
- [ ] Confirm canonical citations for `lam4`, `lexscript`, `ldoc`,
      `hammond1983rights` (TODO notes still in `references.bib`).
- [ ] External-reader pass on the full PDF; tighten phrasing and integrate
      cross-references where the prose has drift between sections.
- [x] **Final venue: *Artificial Intelligence and Law*** (Springer
      journal). Audience is dual-trained (legal-tech +
      formal-methods), handles 60-80 page submissions naturally,
      and is the canonical follow-on venue for Catala / DAPRECO /
      LegalRuleML work. Documentclass swap to AI&L's template
      lands at submission day; pen the manuscript against the
      current arXiv-attributed acmart in the meantime.

---

## VS Code extension — marketplace publish `[ ]`

The extension itself is feature-complete. Remaining work is publishing.

- [ ] Marketplace publish (stretch).

---

## Evaluator-side semantics of `apply_scope` `[x]`

`apply_scope(<section_ref>, ...args)` and `is_infringed(<section>)`
now evaluate end-to-end across all three layers:

- **Tree-walking interpreter** evaluates either node to a boolean
  Value backed by `StatuteEvaluator`.
- **Static type-check pass** at the lint level surfaces empty-target
  and missing-struct-field warnings.
- **Z3 backend** translates either node to the target section's
  `<sX>_conviction` Bool (elements satisfied AND no defeating
  exception fires), declared lazily so cross-section references
  inside guards resolve to the same atom regardless of statute
  iteration order.

---

## Akoma Ntoso transpiler `[ ]`

Structural transpiler ships and validates 524/524 against the
vendored OASIS XSD via `python scripts/akn_roundtrip.py --xsd`.
Remaining work is hardening:

- [ ] Decision criterion before further extension (richer FRBR
      hierarchy, full `<componentRef>` graph): a named external user
      asks for it.

---

## Mermaid flowchart richness `(def)`

The current per-section flowchart (`yuho transpile -t mermaid` default
shape) renders structural shape: section node, element decomposition
under combinators, exception priority DAG, penalty terminals. It does
not yet *trace logic flow* — at a decision point ("did the actus_reus
fire?", "did an exception apply?"), the diagram doesn't show the
branch that leads to "offence made out" vs "no offence" vs "exception
defeats charge". A reader has to mentally execute the encoding rather
than read the diagram.

Deprioritised — ship later. When it lands, the flowchart should:

- [ ] Surface every binary decision point as a labelled diamond
      (`{guard expression}`) with explicit `yes` / `no` edges so the
      reader can trace any fact pattern through the diagram.
- [ ] Render exception precedence as a chain of guards (rather than the
      current flat priority list) so the reader sees *which* exception
      fires and which alternatives it shadows.
- [ ] Show penalty selection branches when multi-penalty (G12) is in
      play — `cumulative` vs `or_both` siblings should diverge with
      labelled edges, not collapse into a list.
- [ ] Carry over the existing schema-shape flag (`--shape schema`)
      style: typed terminals, collapsed enum dispatch, fn-call
      consequence nodes — but apply it to the structural per-section
      diagram by default.
- [ ] Don't lose the current diagram's compactness: the new richness
      should be opt-in via `--shape verbose` (or similar), not the
      default, so the existing per-section explorer pages don't blow
      up vertically.

Acceptance criteria: a reader unfamiliar with Yuho can predict, from
the flowchart alone, what the verdict will be for any concrete fact
pattern — without consulting the source `.yh`.

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

## L3 long tail `(closed)`

L3 author-stamping is at 524/524. External counsel review is out
of scope for this paper; the paper's `§Limitations` carries the
explicit caveat that L3 stamps are author-administered. No work
to track here.

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

### Phase 2c — Future directions (paper-shaped) `(def)`

Four directions all scoped as **full-corpus, paper-claim**. Sequence
them — they share infrastructure and the diachronic Phase 2a is a
prerequisite for one of them. Audience and core-asset constraints
hold throughout: each must hinge on the encoded library + the DSL
+ the existing Z3/Alloy/MCP surface, and target researchers, law
students, or legal engineers.

#### Direction A — Cross-jurisdiction PC port `(superseded by §8)`

This work has been promoted into the paper as `§8 of the paper —
Cross-jurisdiction comparative encoding` (under PhD-rigor
hardening). This section retained as a back-link only; do not
track work here.

#### Direction B — Counter-factual edge-case explorer `[x]`

All five v0 deliverables shipped; the paper claim has its own
evaluation subsection (\S\ref{subsec:scenario_synthesis}).

- [x] **`yuho contrast s_A s_B`** — finds a satisfying assignment
      where A's conviction holds and B's does not. Emits per-statute
      element values + the distinguishing-elements summary. JSON
      mode for downstream tooling. Honours the `not_legal_advice`
      contract.
- [x] **Minimum-distance via `--minimal`** — Z3's `Optimize`
      interface with a hamming-weight objective; returns the
      smallest fact-set that distinguishes A from B.
- [x] **`yuho narrow-defence offence defence`** — smallest fact-set
      where both sections' element conjunctions hold. Solves
      "structural-availability floor" for a defence against an
      offence. Same `--minimal` / `--timeout` / `--json` knobs.
      Subsection-element hoist in `Z3Generator` makes general
      defences (s76–s106, all subsection-scoped) queryable.
- [x] **Bulk run** — `scripts/bulk_contrast.py`. First end-to-end:
      143 doctrinally-related pairs, 115 landed (100% of subsumes,
      79% of referenced); output at
      `library/penal_code/_corpus/contrast/<a>_vs_<b>.json` plus
      summary `index.json`. Per-pair failures logged not aborting.
- [x] **Paper claim** — added evaluation subsection
      "Z3-driven scenario synthesis" with bulk-run numbers and the
      structural-not-doctrinal caveat.

Possible follow-ups (not in scope here):

- [ ] Cross-validate the synthesised scenarios against a published
      case-law corpus; report match rate per chapter.
- [ ] Encode general defences with explicit `defeats` edges into
      the offences they apply against, so `yuho narrow-defence`
      can switch from the "both elements fire" model to the
      stronger "elements fire AND defence prevents conviction" one.

#### Direction C — LLM legal-reasoning benchmark `[~]`

Package the encoded library as a graded benchmark for LLMs. Each
fixture is a fact-pattern + ground-truth answer (which section
applies, which elements are met, which exception fires). Yuho's
evaluator already computes the ground truth.

- [x] **v0 shipped:** `evals/schema.json` + `evals/run.py`
      single-file runner with two `BenchmarkClient` impls
      (Anthropic SDK + `FakeClient` for offline / CI). Three tasks:
      section identification, element-set F1, exception citation.
- [x] **Grown to 205 fixtures** (22 hand-authored + 183 synthesised
      from the encoded library's canonical illustrations). Driver:
      `scripts/synthesise_eval_fixtures.py`. Auto-detects
      polarity-negative illustrations and tags them as such.
- [x] **Stratified accuracy report** — per chapter / category /
      difficulty / synth-vs-hand / polarity. Triggered by
      `--no-per-fixture` for the headline view; full per-fixture
      table is the default.
- [x] **Paper subsection** "LLM legal-reasoning benchmark" added
      under \S\ref{subsec:llm_benchmark} with positioning vs
      LegalBench / LawBench, fixture-corpus stats, structural-not-
      doctrinal caveat, and explicit acknowledgment that the
      real-LLM run is queued.
- [ ] **Run real baselines** against Claude Sonnet 4.6 / Opus 4.7
      / one open-weights reference; emit
      `evals/results-<model>.json` and update the paper
      subsection's "Headline numbers" paragraph with the actual
      stratified accuracies. Requires `ANTHROPIC_API_KEY`.

#### Direction D — Interactive learn-by-doing legal-ed

Extend the static explorer site (`editors/explorer-site/build/`)
into a guided learning surface for law students. Each section page
gains an interactive fact-builder; the elements light up as the
student supplies fact values; the verdict updates live.

- [ ] Per-section JS fact-builder component: parses the section's
      element list from the existing JSON corpus, renders boolean /
      enum / numeric inputs, calls the in-browser evaluator (compile
      `StatuteEvaluator` to Pyodide or write a tiny TS port).
- [ ] Worked-example walkthrough per section: takes the canonical
      illustrations from the `.yh` source, plays them through the
      fact-builder one step at a time. Mode toggle: "show me how it
      gets to the answer" vs "let me try myself first".
- [ ] If Phase 2a lands first: integrate the per-section timeline
      so a student can replay the same fact pattern against the law
      as it stood in 1872, 1985, 2008, 2024 — directly visible
      doctrinal drift.
- [ ] **Paper claim:** "Interactive structural pedagogy for
      common-law penal codes". Co-author with a law-school educator
      who can run a classroom trial; report measured learning
      outcomes vs textbook control.

#### Sequencing notes

- A and B are independent; either can ship first. C depends on a
  stable benchmark schema (small) and the existing evaluator.
- D is the most user-facing and the highest leverage with law
  students; depends on a Pyodide port (modest) of `StatuteEvaluator`.
- All four benefit from Phase 2a (diachronic encodings) but none
  block on it.

---

### Phase 2b — Vision pivot `(def)`

Only after PC L3 coverage is high and tooling is battle-tested.

- [ ] Evidence Act (EA1893)
- [ ] Criminal Procedure Code
- [ ] Constitution (CONS1963)
- [ ] Contract Law (common law + Misrepresentation Act, Contracts
      (Rights of Third Parties) Act, etc.)
- [ ] Civil remedies and equitable doctrines — require AST shapes Yuho
      doesn't have yet.
