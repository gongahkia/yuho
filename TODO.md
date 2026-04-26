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
- [ ] Verify all `\cite{}` keys resolve cleanly. Some bib entries carry
      TODO notes — confirm canonical citations for `lam4`, `lexscript`,
      `ldoc`, `hammond1983rights`. Fix the two bibtex warnings.
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

## Evaluator-side semantics of `apply_scope` `[ ]`

`apply_scope(<section_ref>, ...args)` is shipped at the AST + resolver
layer (it lifts to `ApplyScopeNode`, the resolver gates with
`can_apply_scope`, the lint flags unresolved references). The evaluator-
side semantics is still a structural pre-condition rather than a real
scope invocation that returns bindings.

- [ ] Element-graph executor that consumes a `ApplyScopeNode`, evaluates
      the named section's element graph against a fact pattern, and
      returns the set of bound element states (which the calling section
      can then compose with its own elements).
- [ ] Type-check pass: when `apply_scope` is composed inside a parent
      statute, verify the parent's element shape is compatible with the
      base section's required inputs.
- [ ] Z3 backend hookup: model `apply_scope` as an inlined sub-formula
      so prioritised-rewriting at the parent retains the base's exception
      hierarchy.

---

## Akoma Ntoso transpiler — schema validation `[ ]`

The structural transpiler is shipped (`yuho transpile -t akomantoso`)
and its output passes `xmllint --noout`. Full OASIS schema validation
against the AKN 1.0 XSD is the next-level confidence step.

- [ ] Validate output against the OASIS XSD schema (`xmllint --schema
      akoma-ntoso-1.0.xsd ...`).
- [ ] Add a CI job that round-trips the entire encoded library through
      the AKN transpiler and asserts every emitted document is
      schema-valid.
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
