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
- [ ] Run `scrape_sso.py index` → commit `library/_index/sso_acts.json`
- [ ] Run `scrape_sso.py act --act-code PC1871` → commit `library/penal_code/_raw/act.json`
- [ ] Validate parser output on PC: section count sanity (~599 anchors on SSO), illustration presence on known sections (s378, s415), amendment markers captured

## Phase B — Coverage harness

Three-layer coverage per section:

| Layer | Criterion | Automatable |
|-------|-----------|-------------|
| L1 parse | `.yh` encoding parses cleanly via tree-sitter | yes |
| L2 typecheck | `yuho check` passes (scope, type inference, exhaustiveness) | yes |
| L3 verified | human has signed off encoding matches statute text | manual |

Deliverables:

- [ ] `scripts/coverage_report.py` — walks `library/penal_code/_raw/act.json` + `library/penal_code/s*/statute.yh`, emits per-section `{L1, L2, L3}` status
- [ ] L3 signoff via YAML frontmatter in each `.yh` file (`@verified-by`, `@verified-on`)
- [ ] `library/penal_code/_coverage/COVERAGE.md` (human dashboard) + `coverage.json` (machine)
- [ ] `doc/PENAL_CODE_COVERAGE.md` — narrative methodology doc

## Phase C — Expressiveness probes

Intentionally encode the *hard* PC sections first; failures drive the
refactor scope. Hardness list:

- [ ] Deeming provisions ("shall be deemed to…")
- [ ] Presumptions — rebuttable vs irrebuttable, burden shift
- [ ] Proviso clauses — scoped exceptions inside sections
- [ ] Cross-section refs (s300 exceptions reference s299; s304A ↔ s304)
- [ ] Mens rea gradient (intention / knowledge / rashness / negligence)
- [ ] Punishment lattices (death / life / term / fine / caning, alternative vs cumulative)
- [ ] Defences vs exceptions vs explanations (PC distinguishes all three)

Each probe that fails becomes a concrete AST/type gap → input for Phase D.

## Phase D — AST & type-system refactor

Defer scoping until Phase C gap list exists. Placeholder sub-items
(to be rewritten once Phase C data is in):

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
