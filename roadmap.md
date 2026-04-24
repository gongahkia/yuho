# Yuho Revamp Roadmap

Tracks the current deep-refactor effort: prove Yuho can model the entire
Singapore Penal Code end-to-end, then use the resulting gap analysis to
drive an AST + type-system refactor. Vision pivot to broader SG law is
deferred until PC coverage is complete.

## Phase A — Ingestion

- [x] Feasibility probe of sso.agc.gov.sg (server-rendered, 6s crawl-delay, lazy-load)
- [x] Write generic SSO scraper using Playwright → `scripts/scrape_sso.py`
  - `index` subcommand: list all current Acts (metadata only)
  - `act` subcommand: scrape one Act's whole document into structured JSON
- [x] Run `scrape_sso.py index` → committed `library/_index/sso_acts.json` (500 Acts)
- [x] Run `scrape_sso.py act --act-code PC1871` → committed `library/penal_code/_raw/act.json` (524 sections, 811 KB)
- [x] Validate parser output: s415/s300/s378/s499 structure confirmed; `valid_date` extraction needs tightening (deferred)

## Phase B — Coverage harness

Three-layer coverage per section:

| Layer | Criterion | Automatable |
|-------|-----------|-------------|
| L1 parse | `.yh` encoding parses cleanly via tree-sitter | yes |
| L2 typecheck | `yuho check` passes (scope, type inference, exhaustiveness) | yes |
| L3 verified | human has signed off encoding matches statute text | manual |

Deliverables:

- [x] `scripts/coverage_report.py` — walks `library/<act>/_raw/act.json` + `library/<act>/s*/statute.yh` pairs, emits per-section `{L1, L2, L3}` status
- [x] L3 signoff via existing `metadata.toml` `[verification].last_verified` (reused existing convention; no new frontmatter)
- [x] `library/penal_code/_coverage/COVERAGE.md` (human dashboard) + `coverage.json` (machine)
- [ ] `doc/PENAL_CODE_COVERAGE.md` — narrative methodology doc (deferred to Phase C writeup)

Current snapshot after Phase C: 524 raw / 524 encoded = 100%; all 524 are
L1+L2 green, with 25 L3 human-verified encodings retained as the gold set.
Data-quality issues surfaced by the harness: `s503_criminal_breach_of_trust/`
dir mis-named (actual s503 is Criminal Intimidation); `s395_dacoity/` dir name
is technically stale (s395 punishes gang-robbery; dacoity defined in s391).

## Phase C — Expressiveness probes

Phase C is complete. The original selective probe plan was replaced by mass
encoding of all remaining Penal Code sections, using the full statute as the
expressiveness probe. Coverage now stands at 524/524 sections L1+L2 green; new
machine-drafted encodings remain unverified at L3 until human review.

Findings are tracked in `doc/PHASE_C_GAPS.md`; spot-check notes for future L3
review are tracked in `doc/PHASE_C_REVIEW.md`.

Completed probe coverage:

- [x] Deeming provisions ("shall be deemed to…")
- [x] Presumptions — rebuttable vs irrebuttable, burden shift
- [x] Proviso clauses — scoped exceptions inside sections
- [x] Cross-section refs (s300 exceptions reference s299; s304A ↔ s304)
- [x] Mens rea gradient (intention / knowledge / rashness / negligence)
- [x] Punishment lattices (death / life / term / fine / caning, alternative vs cumulative)
- [x] Defences vs exceptions vs explanations (PC distinguishes all three)

The resulting AST/type gaps are now direct inputs for Phase D.

## Phase D — AST & type-system refactor

Ready to scope from `doc/PHASE_C_GAPS.md` plus any further findings that appear
during L3 review:

- [ ] Audit `src/yuho/ast/nodes.py` against gap list
- [ ] Refactor type system to cover missing shapes
- [ ] Update transpilers to consume revised AST
- [ ] Regression pass against full test suite

## Phase 2 (deferred) — Historical versions

Current scrape captures only the present in-force text. Amendments are
detected as markers but historical versions themselves are not fetched.
Future work:

- [ ] Extend `scrape_sso.py` with `--historical` flag → enumerate `/Act/<CODE>/Historical/<DATE>` snapshots
- [ ] Store each historical snapshot separately under `_raw/historical/<date>.json`
- [ ] Extend Yuho grammar's `effective` semantics to model version lineage (already partial)
- [ ] Coverage harness extension: per-(section, valid-date) tracking

## Phase 2 (deferred) — Vision pivot

Only after PC coverage hits high L3 %. Expand beyond criminal law:

- [ ] Evidence Act (EA1893)
- [ ] Contract Law (common law; no single statute)
- [ ] Constitution (CONS1963)
- [ ] Civil remedies, equitable doctrines — require AST shapes not yet in Yuho
