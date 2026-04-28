# Yuho — Outstanding Work

Authoritative backlog. Positioning is deliberately narrow:
**a robust DSL + cohesive proof of concept for Singapore criminal law
(Penal Code)**, not a general legal-tech platform.

Primary audience: **researchers, law students, and legal engineers**.
Secondary audience: practising lawyers and government law drafters.
Third tranche: AI-tool builders who need grounded legal corpora and
benchmarks.

Status key: `[ ]` pending · `[~]` in progress · `(def)` deferred.

Current snapshot (2026-04-28): **4947 unit tests green · 524 sections at
L1+L2 · 524 L3 author-stamped · §4 + §6 paper sections shipped (formal
semantics + soundness theorem with 5 lemmas + 8 sanity-witness tests) ·
§6.6 Lean 4 mechanisation v5: all 5 soundness lemmas kernel-checked
(6.2 + 6.3 + 6.4 + 6.4' cross-section + 6.5 penalty) PLUS conviction-
layer oracle assumption discharged via `Generator.lean`'s constructive
canonical models (`canonical_smt_satisfies` /
`canonical_graph_satisfies` + unconditional forms of 6.2 / 6.3 / 6.4)
PLUS `Range.cumulativeJoin` / `Range.orBothMeet` algebraic surface +
canonical-model smoke coverage extended to s299 / s300 / s378 / s415 +
`make verify-structural-diff` PoC harness comparing Lean spec ↔
Python `Z3Generator` on those four fixtures ·
§7.8 case-law differential testing (n=38, three scorers; top-1 44.7%,
MRR 0.461, contrast F1 0.239, constrained-contrast consistency 100%) ·
§7.6 LLM benchmark with full 205-fixture GPT-4o-mini + GPT-4o + o3-mini
cross-model baselines + 4-way prompt-variant comparison (baseline /
polarity / polarity-soft / polarity-conditional; polarity-conditional
is the only Pareto-improving variant on gpt-4o-mini, T1 48.8% / T2
exact 37.1% / F1 0.699; o3-mini reproduces the polarity-negative
collapse despite reasoning-token spend) · Direction B
defeats-edge coverage at 1253 edges across 147 sections (28% of corpus,
22 distinct standalone general defences spanning every Chapter IV
affirmative defence the SG PC carries (only s79A and s90, which are
exclusionary and consent-validity-defining respectively, are excluded
by design; ss98, s101, s104 are excluded after the doctrinal audit
demoted them as validity-condition / timing qualifiers): the family
covers s76 (bound or justified by law), s77 (judge acting judicially),
s78 (act pursuant to court order), s79 (mistake of fact), s80
(accident), s81 (necessity), s82 (child <10), s83 (child 10-12 without
maturity), s84 (unsoundness), s85+s86 (intoxication), s87 (consent-
bounded), s88 (consent for benefit), s89 (good faith for child/unsound),
s92 (good faith without consent), s94 (duress), s95 (de minimis), s96
(private-defence operative gateway), s97 (right of body or property
defence), s100 (deadly body), s103 (non-deadly body), s106 (non-deadly
property); ss95-s106 private-defence family fully encoded with
elements{}; defeats-edge structural-coverage sweep at 1141/1253 = 91.1%
SAT, every defence clearing 60-100%) · 32-page smoke PDF ·
`make paper-reproduce` end-to-end including Lean kernel-check.**

Completed history (Phases A–D, the rigor-hardening trench, mechanisation
v1, case-law differential testing, the LLM-benchmark closed-vocab fix,
TikZ figure rewrite, Z3 hookup, AKN OASIS XSD validation, and the rest)
lives in git log + `docs/PHASE_*` notes, not here.

---

## §6.6 — Lean 4 mechanisation `[~]`

v1–v5 shipped; per-version layout, theorem inventory, and trust
base live in [`mechanisation/README.md`](./mechanisation/README.md).
Headline state: all 5 soundness lemmas (6.2, 6.3, 6.4, 6.4', 6.5)
+ the G8/G14 unbounded-axis sentinels + the conviction-layer
oracle discharge (`Generator.lean`'s constructive
`canonicalSMTModel` / `canonicalGraphModel` + unconditional forms
of 6.2 / 6.3 / 6.4) all kernel-check under Lean 4.10.0 with no
`sorry`s. `lake build` + `lake build Tests` both green.

Open follow-ups (deferred to v6):

- [ ] **CrossSMTModel discharge.** The single
      `excFires : String → Bool` indexed by raw exception labels
      needs a refactor to qualified atom names (`<sX>_exc_<label>`)
      before a constructive module-wide witness fits. Adjacent to
      the cross-library `apply_scope` extension.
- [ ] **`Penalty.canonicalModel`.** Analogous to v5's discharge
      for SMTModel / GraphSMTModel. The §6.5 `PenaltySMTModel`
      bundle remains axiomatic; a constructive witness built from
      `Penalty.admits` would close the §6.5 oracle the same way
      v5 closed §6.2 / §6.3 / §6.4.
- [ ] Mechanise the linter's no-sentinel-propagation invariant as
      a `Penalty.wellFormed` predicate, tightening the satisfies
      bundle to require it.
- [ ] Cross-library `apply_scope` (the case-law differential
      testing already restricts to in-module sections; this is a
      v6-stretch item, not a release blocker).
- [ ] **Python-side faithfulness, structural diff — full corpus.**
      PoC shipped on the four smoke fixtures via
      `mechanisation/scripts/ExportSpec.lean` +
      `scripts/verify_structural_diff.py` +
      `make verify-structural-diff`; surfaces two documented
      structural divergences between the Lean spec and the
      Python `Z3Generator` (leaf-bicond omission; per-exception
      `_fires` suffix only on defeat-bearing exceptions).
      Remaining work: extend the harness from the four smoke
      fixtures to the 524-statute corpus. Needs a Lean-side JSON
      statute-loader (or a per-statute codegen that emits one
      `.lean` file per encoded `statute.yh`) so Lean
      `encodeStatute` can run on the whole corpus, not just
      hard-coded fixtures.
- [ ] **Generator-emit consolidation.** Reconcile the two
      structural divergences the PoC harness surfaced — either
      have the Python `Z3Generator` emit the leaf-bicond family
      and a uniform `_fires` suffix, OR adjust the Lean
      `Generator.encodeStatute` spec to drop the leaf bicond and
      conditionalise the `_fires` suffix on defeat-bearing
      exceptions. The former is cleaner for downstream Z3
      tooling; the latter avoids touching the kernel-checked
      spec. Decision pending.

---

## §7.6 — LLM benchmark `[x]`

Closed. Headline state: full 205-fixture runs across three
OpenAI models (gpt-4o-mini, gpt-4o, o3-mini) × four prompt
variants (baseline / polarity / polarity-soft /
polarity-conditional). `polarity-conditional` is the only
Pareto-improving variant on gpt-4o-mini (T1 48.8% / T2 exact
37.1% / F1 0.699 / T3 93.7%). The polarity-negative collapse on
gpt-4o-mini reproduces on o3-mini (despite reasoning-token spend)
but *not* on gpt-4o — the cross-model split is itself a
benchmark finding, presented in §7.6's cross-model paragraph.

Iteration history (v0 closed-vocab fix → cross-model runs →
polarity variants → conditional routing) lives in git log
(commits `ac8570b0..bbdef134`); paper §7.6 carries the
publishable summary. No open work.

---

## §7.8 — Case-law differential testing `[~]`

n=38 fixtures shipped with three scorers (recommend / contrast /
constrained-contrast). Headline numbers wired into paper §7.8:
top-1 44.7%, top-3 47.4%, MRR 0.461, contrast F1 0.239,
constrained-contrast consistency 100% (n=25). v2 expansion
(commits `e8f37c3e..3e7f3dc6`) added 8 fixtures covering s392 /
s394 robbery, s425 mischief, s447 criminal trespass, and s506
criminal intimidation; chapter XXII intimidation now first-class
in the corpus. Open work:

- [ ] **Further sample growth.** Chapter II (state offences) and
      chapter XX (marriage offences) remain absent from the
      corpus — neither has substantial publicly-reported SG
      Penal Code case-law (chapter II offences are typically
      prosecuted under the Internal Security Act / repealed
      Sedition Act; chapter XX bigamy cases are typically
      prosecuted via the Women's Charter rather than s494 PC).
      Chapter XXIII s509 (insulting modesty) and s363 / s363A
      kidnapping (most kidnapping cases use the Kidnapping Act
      1961, not Penal Code ss363-367) similarly thin. Realistic
      scope: target s363A kidnapping for ransom under PC, and
      any s509 outrage-of-modesty cases reported on eLitigation.
- [ ] Inter-rater reliability on the curated fact patterns. A
      second curator (human, not LLM) extracts facts from the
      same judgments independently; compute κ score for §7.8's
      threats-to-validity caveat. Cannot be done by Claude as
      the second curator (defeats the inter-rater claim);
      requires user action.

---

## §8 — Cross-jurisdiction comparative encoding `[ ]`

The IPC scraper (`scripts/scrape_indiacode.py`) is committed and
fixture-tested. Open work:

- [ ] **First IPC scrape run** (your action). One ~50-minute
      command: `python scripts/scrape_indiacode.py act --out
      library/indian_penal_code/_raw/act.json` against the
      AdvocateKhoj backend. Spot-check the first few section
      JSONs to confirm parser-shape assumptions hold against the
      live HTML.
- [ ] Encode at full coverage (511 IPC sections) using the
      agent-dispatch shape from Phase D. The long pole — months
      of agent runs.
- [ ] Comparative analysis tool: `yuho refs --compare-libraries`
      emitting SCC overlap, divergent amendment paths, sections
      renumbered / added / repealed.
- [ ] **Paper §8 prose** writing the comparative findings.

---

## Direction B — General-defence `defeats` edges `[x]`

Closed. 1253 edges across 147 sections (28% of corpus) using 22
distinct Chapter IV standalone general defences. Doctrinal-
fidelity audit (commits `4f0ba0c9..f1155a9d`) removed 75
misclassified edges; ss98/s101/s104 conditions subsequently
folded into ss96/s97/s100/s103/s106 elements (commit `e982ccd7`).
Defeats-edge structural-coverage sweep at 91.1% SAT under
`yuho narrow-defence`. Per-defence breakdown + cluster coverage
table preserved in paper §7.5 + git log (commits
`90c3c8ef..d0a9c971` for cluster batches,
`4f0ba0c9..f1155a9d` for the audit). No open work.

---

## Research paper polish `[~]`

arXiv-attributed acmart `manuscript` mode for now; AI&L
documentclass swap on submission day. Outstanding pre-submission
hardening:

- [ ] **Manual read-through pass.** Read the rendered PDF cover-
      to-cover, mark places where prose drifts, claims need a
      citation, or a paragraph buries the lede. Add detail where
      missing (especially in evaluation §5 and limitations §11)
      but stay tight — no padding. (User action.)
- [ ] **§6.6 / §11 staleness audit.** A v4-shipped item (G8/G14
      sentinels) was still listed as "out of scope" in §6.6 prose
      until 2026-04-28; the v5 sweep caught it but did not
      audit the rest of §6 / §11 / §7 for similar drift. Read
      every "remaining gap" / "future work" / "out of scope"
      sentence and confirm it's still accurate. (User action;
      the same sweep doubles as the manual read-through above.)
- [ ] **Blog-post transpilation.** Hand the rendered paper to
      Claude with a transpilation prompt; output to
      `paper/blog/yuho.md`.
- [ ] **External-reader pass on the full PDF.** Catches drift
      both author and AI miss.

---

## Hardening `[~]`

Items worth keeping under attention even though there is no
defense per se. Consolidates user-action work surfaced during
the §6.6 v5 sweep on 2026-04-28 and the 2026-04-28 followup
that closed smoke-test expansion + dangling-ref + §6.6 prose +
Range ops + the structural-diff PoC.

- [ ] **Run `make paper-reproduce` end-to-end periodically.**
      Confirms the repo still reproduces every empirical claim.
- [ ] **Inter-rater reliability for §7.8.** See §7.8 above —
      tracked there. User action.
- [ ] **Mermaid `--shape verbose` audit.** See *Mermaid
      flowchart richness* below — flagged for HUMAN AUDIT, not
      removed from TODO. User action.

---

## Reproducibility — Zenodo deposit `[ ]`

Dockerfile + Makefile + REPRODUCE.md shipped. Only the Zenodo DOI
remains:

- [ ] Submission-day plumbing: zip the v1.0 corpus + benchmark
      fixtures + AKN XSD + Lean mechanisation, upload to Zenodo,
      cite the DOI in `paper/REPRODUCE.md`. Triggered on paper
      submission; nothing to do until then.

---

## Risk register

| Risk | Mitigation |
|---|---|
| External counsel access not available | L3 stays author-stamped; §11 carries the explicit caveat that external review is not part of this paper's claim |
| IPC text access blocked (paywall, robots.txt change) | Switch to the Bangladeshi PC 1860 (also Anglo-Indian lineage, public-domain text) |
| AI&L editorial rejection | Re-target *Formal Aspects of Computing* (legal-tech amenable) or ICAIL (page budget tighter but acceptable) |
| Panellist presses on residual oracle scope | §6.6 + §11 v5 prose already frames the discharge: conviction-layer oracle gone, residual narrowed to (i) CrossSMTModel raw-label refactor (v6) and (ii) Python-side faithfulness, with `make verify-bulk-contrast` as the differential check today |

---

## Long-tail / stretch

### VS Code extension marketplace publish `[ ]`

The extension itself is feature-complete. Remaining work is publishing.

- [ ] Marketplace publish (stretch).

### Akoma Ntoso transpiler hardening `[ ]`

Structural transpiler ships and validates 524/524 against the
vendored OASIS XSD. Further extension is on-demand:

- [ ] Decision criterion before further extension (richer FRBR
      hierarchy, full `<componentRef>` graph): a named external
      user asks for it.

### Mermaid flowchart richness `[~]` — **FLAGGED FOR HUMAN AUDIT**

v1 shipped (commit `<this-commit>`): the four sub-items below are
implemented behind `--shape verbose` in
`src/yuho/transpile/mermaid_transpiler.py`. The task is **NOT
removed from TODO** by author request: the verbose shape is a
mechanical rewrite of the existing statute shape and needs human
audit before being relied on for documentation, teaching, or
reviewer-facing rendering.

What v1 does:
- Each element rendered as a labelled decision diamond
  (`{<element>?}`) with explicit `yes` (continue to next
  element) and `no` (dotted edge to a single shared "No
  offence made out" sink) edges.
- Exceptions rendered as a priority-ordered chain of
  diamonds (`{<exception> fires?}`), each with `yes` →
  exception outcome, `no` (`continue`) → next guard /
  penalty.
- Per-conditional penalties (`penalty when <cond>`)
  rendered as a diamond branch off the `when` clause
  before the penalty rectangle. Unconditional penalties
  fall through to the rectangle directly.
- Opt-in via `--shape verbose` on `yuho transpile -t
  mermaid` (also threaded through the CLI in
  `src/yuho/cli/commands/transpile.py` + main.py's
  `--shape` choice list).

**Audit checklist (HUMAN):**
- [ ] Diamond labels — confirm doctrinal fidelity for long
      element descriptions; some labels may need a tooltip
      rather than an inline glyph (Mermaid does not natively
      support tooltips on diamonds).
- [ ] Exception priority chain — currently rendered in
      source order. The AST visitor does NOT yet auto-sort
      by the `priority` field on exception blocks. Audit
      output against sections that use explicit priorities
      (e.g. s300 carries Exceptions 1-7 in priority order
      already, but newer hand-edited sections might diverge).
- [ ] Penalty-conditional rendering — verify the AST
      attribute access in `_transpile_statute_verbose`
      (`pen.when_condition` then fallback `pen.when`) actually
      reads the `when` clause from the encoded library.
      Spot-check on a multi-penalty section (s404 carries
      `penalty when clerk_or_servant_case`; s302 has unconditional
      penalty).
- [ ] Mermaid render — run the verbose output through `mmdc`
      / the explorer site and confirm no syntax errors / no
      orphaned nodes. The current 28 Mermaid unit tests
      cover the default `statute` shape only.

Once the audit is complete, this section can be removed.

### Test-suite backlog `[ ]`

The suite is green at 4937. 82 sections carry behavioural-test
companions; 442 sections are pure-interpretation provisions where
structural parse + lint coverage is the appropriate bar.

- [ ] **442 sections without behavioural companions.** Author
      per-section companions opportunistically when an offence
      gains structural complexity that warrants behavioural
      testing.

---

## Notes for fresh contributors

- **Hypothesis dep.** Already declared in `pyproject.toml` under the
  `[dev]` extras group. To run the property-based tests
  (`tests/test_properties.py`, `tests/test_statutes.py`), install
  with: `pip install -e .[dev]`. CI configurations should pin to the
  `[dev]` extra so the property suite participates in the test run.

- **Lean toolchain.** `mechanisation/` requires Lean 4.10.0+ via
  `elan`. Install with `curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh | bash`,
  then `cd mechanisation && lake build`.

---

## Deferred — Phase 2a (Historical versions)

The Penal Code 1871 has accumulated 150+ years of amendments. Yuho
currently encodes only the current version of each section. Phase
2a extends Yuho into a **diachronic** legal artefact: every section
carries every historical version, and the toolchain answers "what
did the law look like on date X?" temporally.

**Scope:** every encoded section gets every historical version
since 1872. `yuho check --as-of 1995-06-15 my_facts.yh` and friends
become first-class queries.

### Scrape + ingest

The v0 scrape ships (`scripts/scrape_sso.py historical-list /
historical / historical-bulk`); per-Act snapshots land under
`_raw/historical/<act>/<YYYYMMDD>.json` with a sibling
`historical_index.json`. Remaining work:

- [ ] Build a `historical_index.json` mapping `(section, valid-date)
      → raw_path` so re-encoding can iterate snapshots in
      chronological order.
- [ ] Identify the canonical "current" snapshot date so the
      existing `_raw/act.json` doesn't duplicate the latest
      historical entry.

### Grammar (versioned blocks)

- [ ] Add `version <date> { definitions / elements / penalty /
      illustrations / exceptions }` block to `grammar.js`.
- [ ] AST: extend `StatuteNode` with `versions: Tuple[VersionedBlock,
      ...]`.
- [ ] Builder: when multiple `version` blocks are present, populate
      `versions` and leave the top-level fields empty. Lint check
      for contiguous effective-date ranges.
- [ ] Update parser tests + `tests/test_versioned_blocks.py`.

### Re-encoding pipeline

- [ ] Build `paper/reproducibility/historical_reencode.py`: given
      the `historical_index.json`, dispatch agents to re-encode
      each `(section, date)` snapshot as a `version` block.
- [ ] L3-equivalent fidelity audit per version: extend the 11-point
      checklist with an additional "preserves 1872-era spelling and
      drafting style" check.
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
the elements light up as the student supplies fact values; the
verdict updates live.

- [ ] Per-section JS fact-builder component: parses the section's
      element list from the existing JSON corpus, renders boolean /
      enum / numeric inputs, calls the in-browser evaluator (compile
      `StatuteEvaluator` to Pyodide or write a tiny TS port).
- [ ] Worked-example walkthrough per section: takes the canonical
      illustrations from the `.yh` source, plays them through the
      fact-builder one step at a time. Mode toggle: "show me how
      it gets to the answer" vs "let me try myself first".
- [ ] If Phase 2a lands first: integrate the per-section timeline
      so a student can replay the same fact pattern against the
      law as it stood in 1872, 1985, 2008, 2024 — directly visible
      doctrinal drift.
- [ ] **Paper claim:** "Interactive structural pedagogy for
      common-law penal codes". Co-author with a law-school educator
      who can run a classroom trial; report measured learning
      outcomes vs textbook control.

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
