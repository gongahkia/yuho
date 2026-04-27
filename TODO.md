# Yuho — Outstanding Work

Authoritative backlog. Positioning is deliberately narrow:
**a robust DSL + cohesive proof of concept for Singapore criminal law
(Penal Code)**, not a general legal-tech platform.

Primary audience: **researchers, law students, and legal engineers**.
Secondary audience: practising lawyers and government law drafters.
Third tranche: AI-tool builders who need grounded legal corpora and
benchmarks.

Status key: `[ ]` pending · `[~]` in progress · `(def)` deferred.

Current snapshot (2026-04-27): **4937 unit tests green · 524 sections at
L1+L2 · 524 L3 author-stamped · §4 + §6 paper sections shipped (formal
semantics + soundness theorem with 5 lemmas + 8 sanity-witness tests) ·
§6.6 partial Lean 4 mechanisation kernel-checked (Lemmas 6.2 + 6.4) ·
§7.8 case-law differential testing (n=30, three scorers) · §7.6 LLM
benchmark with full 205-fixture GPT-4o-mini + GPT-4o cross-model
baselines + 3-way prompt-variant comparison (baseline / polarity /
polarity-soft; polarity-soft is near-Pareto on gpt-4o-mini) · Direction B
defeats-edge coverage at 610 edges across 147 sections (28% of corpus,
15 distinct general defences spanning the full Chapter IV regime
including the entire ss97-s106 private-defence family; defeats-edge
structural-coverage sweep (387/610 = 63.4% SAT, finding: ss95-s106
need element decomposition to unblock the rest)) · 32-page smoke PDF ·
`make paper-reproduce` end-to-end including Lean kernel-check.**

Completed history (Phases A–D, the rigor-hardening trench, mechanisation
v1, case-law differential testing, the LLM-benchmark closed-vocab fix,
TikZ figure rewrite, Z3 hookup, AKN OASIS XSD validation, and the rest)
lives in git log + `docs/PHASE_*` notes, not here.

---

## §6.6 — Lean 4 mechanisation `[~]`

v1 shipped at `mechanisation/`: Lemma 6.2 (element correspondence) +
Lemma 6.4 (exception correspondence) + composed corollary
`partial_conviction_correspondence`, all kernel-checked under Lean
4.10.0. Paper §6.6 documents the boundary; §11 Limitations carries
the partial-mechanisation caveat.

Open follow-ups (deferred to v2):

- [ ] Mechanise Lemma 6.3 (element-graph correspondence) — the
      structural twin of Catala's bisimulation lemma; ~2–3
      person-months.
- [ ] Mechanise Lemma 6.5 (penalty correspondence) — Yuho-specific,
      requires lifting range-arithmetic into Lean; ~2 person-months.
- [ ] Mechanise the cross-section composition step of Theorem 6.1
      (`apply_scope` / `is_infringed` dedupe simulation) — ~2–3
      person-months.
- [ ] Discharge the oracle assumption by porting Yuho's Python
      `Z3Generator` to Lean and proving its functional equivalence
      to a verified specification.

---

## §7.6 — LLM benchmark hardening `[~]`

v0 + closed-vocab fix + GPT-4o-mini full baseline + GPT-4o cross-
model baseline shipped (gpt-4o-mini: T1=43.9% / T2=32.7% /
F1=0.676 / T3=94.1%; gpt-4o: T1=60.5% / T2=6.8% / F1=0.317 /
T3=98.0% on n=205). Paper §7.6 has headline numbers + three
findings + cross-model paragraph. Open work:

### Polarity-negative collapse (benchmark-design weakness)

The full GPT-4o-mini run surfaced a real benchmark-design issue: on
the 30 polarity-negative fixtures (scenarios where the ground-truth
satisfied-elements set is empty), accuracy collapses:

| Metric | Whole corpus (n=205) | Polarity-negative slice (n=30) |
|---|---|---|
| T1 (section identification) | 43.9% | 33.3% |
| T2 (element-set F1) | 0.676 | 0.056 |
| T3 (exception citation) | 94.1% | 70.0% |

The model is systematically biased toward producing *some* satisfied
elements rather than identifying that none fire. This is itself a
finding worth keeping in §7.6 (it informs downstream legal-AI work
on structural-reasoning prompts), but it also flags a benchmark-
design weakness we should fix.

**Update (post gpt-4o run):** the polarity-negative collapse does
*not* reproduce on gpt-4o (T2 F1 0.380 on the 30 negative-polarity
fixtures, slightly above the corpus mean 0.317). So the collapse
is a **gpt-4o-mini-specific artefact**, not a benchmark-wide
structural property. The benchmark itself surfaces this cross-
model split — a useful discriminator. The polarity-priming /
chain-of-thought work below now targets the gpt-4o-mini failure
mode specifically, not the benchmark as a whole.

**Iterative refinement history of the LLM benchmark** — useful
context for the §7.6 paragraph and for any future benchmark-design
audit:

1. **v0 (commit `ac8570b0`)**: 22 hand-authored fixtures + open-
   vocabulary T2 prompt asking the LLM to "list satisfied element
   names as snake_case identifiers". Spot-check on n=5 (gpt-4o-
   mini) yielded T2 F1 ≈ **0.07** — catastrophic.
2. **Diagnosis**: open-vocabulary T2 was conflating two distinct
   capacities — structural legal reasoning ("does this scenario
   satisfy these elements?") with naming-convention recall ("can
   you guess Yuho's private snake_case identifiers?"). The latter
   is unrelated to legal capability and dragged down the metric.
3. **Closed-vocabulary fix (commit `345909a0`)**: T2 prompt now
   presents the section's encoded element names as a closed list
   ("the encoded section's structural elements are: [a, b, c, …]")
   and asks the model to return a subset. Predictions outside the
   vocab are filtered.
4. **Re-run on n=10**: T2 F1 lifted **0.07 → 0.627**.
5. **Full n=205 run (commit `ec91405a`)**: T1=43.9% / T2=32.7%
   exact / F1=0.676 / T3=94.1%. Paper §7.6 rewritten with the real
   numbers + three observations.
6. **Polarity-negative finding (gpt-4o-mini)**: the model
   collapses on negative-polarity fixtures (T2 F1 0.056).
7. **Cross-model run (gpt-4o, commit `2048c677`)**: the collapse
   does *not* reproduce on gpt-4o (T2 F1 0.380 on the same slice).
   Reframed: the failure mode is model-specific, not benchmark-
   wide. Polarity-priming work targets the gpt-4o-mini regime
   specifically.
8. **Polarity-variant prompts (commits `6b4210bc` /
   `f8712594` / `7f42a11d` / `1392b418`)**: shipped polarity
   priming + optional `# ruled out:` CoT preamble + `none` T1
   option as `--prompt-variant polarity`. Paired n=205 gpt-4o-
   mini run vs baseline: substantial lift on the n=30 polarity-
   negative slice (T1 33.3% → 60.0%, T2 F1 0.052 → 0.267) but a
   regression on the positive-case corpus (T2 F1 0.678 → 0.420).
   Not a Pareto improvement.
9. **Polarity-soft variant (commits `fc0d90b7` / `1472d1cd`)**:
   dropped the `# ruled out:` CoT invitation, kept priming +
   `none`. Near-Pareto on gpt-4o-mini: captures essentially the
   full negative-slice gain (T1 33.3% → 56.7%, T2 F1 0.052 →
   0.267) at minimal positive-corpus cost (T2 F1 0.678 → 0.625,
   $-0.053$; T2 exact 32.2% → 33.7%, $+1.5$pp; T3 93.2% → 94.1%,
   $+0.9$pp). The polarity-variant regression came from the CoT
   path encouraging over-exclusion, not from the priming itself.
   §7.6 now a 3-way table.

Polarity-negative work shipped:

- [x] **Polarity-priming in the T2 prompt.** Foregrounded the
      empty-set case explicitly. Lifts negative-slice F1 from
      0.052 → 0.267.
- [x] **Chain-of-thought scaffolding for negative cases.**
      Optional `# ruled out:` preamble; parser extracts the last
      JSON array. Combined with the priming above.
- [x] **Polarity-aware T1 prompting.** `none` is now a permitted
      reply; scorer accepts it for polarity-negative fixtures.
      Lifts negative-slice T1 from 33.3% → 60.0%.
- [x] Re-ran benchmark; §7.6 now reports both variants side-by-
      side with the calibration-tradeoff finding.

Open follow-ups (deferred):

- [ ] **Conditional polarity prompting.** Route polarity-
      negative scenarios through the v2 prompt and positive-case
      scenarios through v1 — but this requires fixture knowledge
      at inference time, which the model doesn't have. Could be
      approximated with a cheap pre-classifier that decides
      whether to invoke the priming prompt; experimental.
- [x] **Soften the CoT invitation.** Shipped as
      `--prompt-variant polarity-soft`: priming + `none` T1, no
      CoT. Confirmed the hypothesis — the `# ruled out:` CoT path
      caused the polarity-variant positive-corpus regression, not
      the priming itself. Polarity-soft captures essentially the
      full negative-slice gain (+0.215 T2 F1, +23.4pp T1 over
      baseline) at a fraction of the positive-corpus cost
      (T2 F1 -0.053; T2 exact +1.5pp; T3 +0.9pp). §7.6 promoted
      to a 3-way table covering baseline / polarity / polarity-
      soft.

### Additional model baselines (OpenAI only)

User has an OpenAI org key but not Anthropic. Run additional OpenAI
models to test cross-model generalisation:

- [x] **GPT-4o.** Shipped — `evals/results-gpt-4o-full.json`.
      T1 60.5% / T2 6.8% / F1 0.317 / T3 98.0% on n=205. Paper
      §7.6 has the cross-model paragraph; polarity-negative
      collapse is gpt-4o-mini-specific (see update note above).
- [x] **GPT-4o-mini + polarity-priming** combined run shipped
      as the `--prompt-variant polarity` paired comparison
      (results-gpt-4o-mini-polarity.json + §7.6 paired-variant
      paragraph). Lifts the negative slice as targeted but
      regresses positive-case F1 — see the iterative-history
      entry #8 above.
- [ ] **o1-mini** or **o3-mini** if the user wants to test
      reasoning-model performance — a real apples-to-apples for
      structural reasoning.

---

## §7.8 — Case-law differential testing `[~]`

n=30 fixtures shipped with three scorers (recommend / contrast /
constrained-contrast). Headline numbers wired into paper §7.8:
top-1 43.3%, MRR 0.450, contrast F1 0.219, constrained-contrast
consistency 100%. Open work:

- [ ] **Grow case-law sample via manual LawNet / SLW research.**
      Chapter II (state offences), chapter XX (marriage), chapter
      XXII (intimidation — s506 / s509), s392 / s394 robbery,
      s425 mischief, s441 criminal trespass, s363 / s363A
      kidnapping are underrepresented or missing. The agent
      flagged these as ones where reported SG case-law is
      genuinely thin or where citation accuracy needs LawNet
      verification by a human curator.
- [ ] Inter-rater reliability on the curated fact patterns. A
      second curator (human, not LLM) extracts facts from the
      same judgments independently; compute κ score for §7.8's
      threats-to-validity caveat.

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

## Direction B — General-defence `defeats` edges (full coverage) `[~]`

v3 ships **610 edges across 147 sections** (28% of the 524-section
corpus) using **15 distinct Chapter IV general defences**. Per-
defence breakdown:

| Defence | Sections covered |
|---|---|
| s79 (mistake of fact) | 146 |
| s84 (unsoundness of mind) | 143 |
| s97 (private defence of body OR property) | 57 |
| s80 (accident in lawful act) | 52 |
| s98 (private defence against unsound-minded aggressor) | 32 |
| s96 (private defence — general) | 31 |
| s85 (intoxication when a defence) | 29 |
| s86 (effect of intoxication when established) | 29 |
| s104 (non-deadly property defence) | 23 |
| s101 (non-deadly body defence) | 20 |
| s100 (deadly-assault body defence) | 12 |
| s106 (deadly defence with risk to innocent) | 12 |
| s81 (greater-harm avoidance / necessity) | 11 |
| s103 (deadly property defence) | 7 |
| s95 (act causing slight harm / de minimis) | 6 |

Cluster-level coverage:

- **Homicide** (10 sections, s299-s308): s79, s80, s84, s96, s100
- **Hurt** (20 sections, s319-s338): s79, s80, s84, s96
- **Property** (23 sections, s378-s420): s79, s80 (v0 only on s378), s84
- **Sexual offences + outrage of modesty** (22 sections,
  s354-s377BL): s79, s84
- **Kidnapping / abduction / slavery** (17 sections, s359-s374): s79, s84
- **Mischief + house-breaking + criminal trespass** (20 sections,
  s425-s462): s79, s80, s84
- **Forgery + intimidation / public-order** (12 sections, s463-s506):
  s79, s84
- **Abetment + defamation + attempt** (21 sections, s107-s120,
  s499-s502, s511): s79, s84

Edges deployed via the idempotent
`scripts/add_general_defence_edges.py` helper; commit history
`90c3c8ef..4f4110df` walks the cluster batches.

- [x] **s84 unsoundness-of-mind onto every major offence cluster.**
      143 sections covered (universal-applicability defence; missing
      sections are pure definitions and regulatory provisions where
      the defence is moot).
- [x] **s79 mistake-of-fact onto every mens-rea-bearing offence
      cluster.** 146 sections covered.
- [x] **s80 accident onto major actus-reus-bearing clusters.**
      52 sections (homicide, hurt, mischief, v0 sample).
- [x] **s96 private defence onto homicide + hurt clusters.** 31
      sections (the doctrinally relevant range; s100 deadly-assault
      sub-edge present on the homicide cluster only).
- [x] **s85, s86 intoxication onto specific-intent offences.**
      29 sections covered (homicide-with-intent, theft, robbery,
      CMA/CBT, cheating, forgery, abetment of specific-intent
      offences). Strict-liability and recklessness-based offences
      excluded by design.
- [x] **s95 trifling-harm onto hurt-family offences.** 6 sections
      covered (s319-s324). De minimis defence.
- [x] **s81 (necessity / greater-harm avoidance)** onto property
      + mischief clusters. 11 sections covered (theft, mischief
      variants).
- [x] **ss97-s106 private-defence family.** Per-defence
      doctrinal mapping shipped. s97 (broadest, 57 sections),
      s98 (against unsound aggressor, 32 sections), s101 (non-
      deadly body, 20 sections), s103 (deadly property, 7
      sections), s104 (non-deadly property, 23 sections), s106
      (deadly with risk to innocent, 12 sections). s99
      (constraint, not defence) and s102/s105 (timing
      qualifiers, not standalone defences) deliberately omitted
      per doctrine.

Open follow-ups:

- [x] **Defeats-edge structural-coverage benchmark** (commit
      `f1cb7cac`). New scorer at
      `evals/case_law/score_defeats_coverage.py` runs
      `yuho narrow-defence` over every (offence, defence) edge
      in the corpus. Headline: 387/610 = 63.4% SAT. Element-
      bearing defences (s79/s80/s81/s84/s85/s86/s100) clear at
      90–100%; the rest of the private-defence family
      (s95/s96/s97/s98/s101/s103/s104/s106) sits at 0% because
      those sections were encoded as pure-definition sections
      during Phase D, with no `elements {}` block. Reported
      honestly in §7.6.

- [ ] **Encode structural elements for ss95-s106 private-defence
      sections.** Currently encoded as pure-definition statutes
      with operative-rule prose only. Adding an `elements {}`
      block per section (e.g. for s96: `private_defence_in_play`
      / `act_done_in_exercise_of_right`; for s97: body /
      property choice flag + body-and-property predicates; etc.)
      would unblock the 36.6% UNSAT slice in the defeats-coverage
      sweep without further grammar or library changes. Doctrinal
      decomposition needed; not a mechanical refactor.

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
- [ ] **Blog-post transpilation.** Hand the rendered paper to
      Claude with a transpilation prompt; output to
      `paper/blog/yuho.md`.
- [ ] **External-reader pass on the full PDF.** Catches drift
      both author and AI miss.
- [x] Confirmed canonical citations for `lam4` (JURIX 2023,
      doi:10.3233/FAIA230954), `lexscript`
      (github.com/codeNinja62/LexScript), `ldoc`
      (github.com/arismoko/LDOC); `hammond1983rights` already
      replaced with `sergot1991representation`. Surfaced two
      factual corrections to LexScript (parser tech: participle/Go
      not tree-sitter) and LDOC (source-of-truth posture matches
      Yuho's, not opposed to it) — fixed across intro, background,
      and related-work sections.

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
| §6.3 mechanisation overruns | §6.6 partial mechanisation already shipped; remaining lemmas demote to "future work" pointer in §11 if v2 doesn't land |
| External counsel access not available | L3 stays author-stamped; §11 carries the explicit caveat that external review is not part of this paper's claim |
| IPC text access blocked (paywall, robots.txt change) | Switch to the Bangladeshi PC 1860 (also Anglo-Indian lineage, public-domain text) |
| AI&L editorial rejection | Re-target *Formal Aspects of Computing* (legal-tech amenable) or ICAIL (page budget tighter but acceptable) |
| LLM-benchmark polarity-negative gap remains unfixed | gpt-4o run shows the gap is model-specific (gpt-4o-mini only); §7.6 cross-model paragraph already frames this as a positive discriminator the benchmark surfaces, not a corpus-wide weakness |

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

### Mermaid flowchart richness `(def)`

Per-section flowcharts render structural shape but don't trace
*logic flow* (no decision diamonds, exception-precedence chain,
penalty branches). Deprioritised — ship later.

- [ ] Surface every binary decision point as a labelled diamond
      with explicit `yes` / `no` edges.
- [ ] Render exception precedence as a chain of guards.
- [ ] Show penalty selection branches when multi-penalty (G12)
      is in play.
- [ ] Carry over the schema-shape style; opt-in via
      `--shape verbose`.

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
