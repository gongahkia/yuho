# Yuho — Outstanding Work

Authoritative backlog. Positioning is deliberately narrow:
**a robust DSL + cohesive proof of concept for Singapore criminal law
(Penal Code)**, not a general legal-tech platform.

Status key: `[x]` done · `[~]` in progress · `[ ]` pending · `(def)` deferred.

Current snapshot: **524/524 L1+L2 green · 118 L3 stamped · all 14
grammar gaps (G1–G14) closed or deferred to tooling.**

---

## Completed phases (history)

### Phase A — Ingestion `[x]`
- Playwright scraper at `scripts/scrape_sso.py` (`index` + `act` subcommands).
- `library/_index/sso_acts.json` — 500 current SG Acts.
- `library/penal_code/_raw/act.json` — Penal Code 1871, 524 sections.

### Phase B — Coverage harness `[x]`
- `scripts/coverage_report.py` — L1 / L2 / L3 dashboard.
- `library/penal_code/_coverage/{COVERAGE.md,coverage.json}`.
- L3 signoff via `metadata.toml [verification]`.

### Phase C — Expressiveness probes `[x]`
- Mass encoding of all PC sections (524/524 L1+L2 green).
- Findings in `doc/PHASE_C_GAPS.md` and `doc/PHASE_C_REVIEW.md`.

### Phase D — grammar + semantic refactor `[x]`
All 14 gaps addressed:

| Gap | Status | Artefact |
|---|---|---|
| G1 | fixed | doc comments before `element_group` |
| G2 | not-a-gap | colons in `///` parse fine |
| G3 | fixed | multi-letter section suffix (376AA, 377BO, …) |
| G4 | deferred | illustration-count validator — see tooling below |
| G5 | fixed | `subsection (N) { … }` nesting |
| G6 | fixed | multiple `effective <date>` clauses |
| G7 | not-a-gap | flat `definitions` is sufficient; G5 covers nesting |
| G8 | fixed | `penalty or_both / alternative / cumulative` + `fine := unlimited` |
| G9 | fixed | `penalty when <ident>` conditional branches |
| G10 | not-a-gap | grammar already parses `referencing`/`subsumes`/`amends` |
| G11 | deferred | `all_of`/`any_of` sanity check — see tooling below |
| G12 | fixed | nested penalty combinators |
| G13 | fixed | exception-priority DAG + Z3 prioritised-rewriting |
| G14 | fixed | `caning := unspecified` |

### Phase D — sweep + re-encoding + L3 `[x]`
- Re-encoded all 484 non-original sections via Codex (`scripts/phase_d_reencode.py`).
- L3 auto-reviewer (`scripts/phase_d_l3_review.py`) stamped 118 sections.
- Flag-fix dispatcher (`scripts/phase_d_flag_fix.py`) rewrote flagged sections
  using the new grammar primitives (G14 + G12).
- G12 migration script (`scripts/migrate_g12_workaround.py`) collapsed 19
  two-sibling-penalty-block workarounds into nested form.

---

## Active work

### Remaining L3 flags `[ ]`

4 sections still flag on audit despite the grammar fixes. These are
genuine content issues, not grammar gaps:

- [ ] **s304C** — missing amendment effective date (G6-shape issue in the data).
- [ ] **s376** — subsection (3) `or_both` vs canonical "or"; subsection (4) needs explicit `any_of` per s375 gold-standard.
- [ ] **s376H** — still missing subsection (2)(a) penalty branch.
- [ ] **s377BD** — `_raw/act.json` subsection (1)(b) still truncated; earlier scraper fix didn't cover this shape. Needs scraper re-patch + re-encode.

Fix path: manual edit for the first three; scraper patch + re-scrape for s377BD.

### L3 review — deprioritised long tail `(def)`

~400 shorter / simpler sections still unreviewed. Most are
single-sentence interpretation sections where the encoding is a
faithful mirror and the bug surface is small.

- [ ] (def) Revisit when L3 matters for a concrete deliverable.
      Command: `phase_d_l3_review.py --all-unstamped --dispatch --reasoning medium --parallel 8`.

---

## Expansions — things we are keeping and want to make better

### MCP server expansion `[ ]`

Primary AI-integration surface.

- [ ] Audit current MCP tools in `src/yuho/mcp/server.py`. Document each.
- [ ] Add tools for the full Phase C workflow so external agents can encode + verify a new statute end-to-end: `yuho_propose_encoding`, `yuho_check_encoding`, `yuho_preview_transpile`.
- [ ] Expose library search / navigation tools: find by SSO anchor, list sections citing a given section, fetch canonical raw text alongside encoded AST for side-by-side reads.
- [ ] Resources for the Phase D strict prompt + grammar spec so clients can self-onboard.
- [ ] Rich prompts covering: encode-from-English, explain-encoding, find-fidelity-issues, recommend-L3.
- [ ] Integration test: drive a Codex Cloud / Claude session purely via MCP to re-encode a fresh PC section, end-to-end.

### LSP buff-up `[ ]`

- [ ] Inlay hints — effective-date range, burden qualifier, mens rea type, element count, illustration count.
- [ ] Hover — show canonical SSO URL + excerpt from `_raw/act.json` for the section under cursor.
- [ ] Code lens inline per statute — "L1 ✓ L2 ✓ L3 ?" with click-to-open coverage dashboard.
- [ ] Cross-file rename (`s415` across the library).
- [ ] Goto-definition into `referencing` / `subsumes` / `amends` targets (after G10 semantic hookup).
- [ ] Diagnostic: illustration-count mismatch vs raw (G4 lint).
- [ ] Diagnostic: `all_of` used where statute text says "or" (G11 lint).
- [ ] Diagnostic: fabricated fine cap (statute says "with fine" + encoding uses numeric money range instead of `unlimited`).
- [ ] "Did-you-mean" for unknown directives (idea from LDOC).

### VS Code extension expansion `[ ]`

- [ ] Snippets for each statute shape: offence, pure punishment, interpretation, subsection block.
- [ ] Command: "Open SSO page for this section" (uses the anchor from `/// @meta source=...`).
- [ ] Command: "Run yuho check on this file" with inline errors.
- [ ] Command: "Transpile to Mermaid → preview side panel."
- [ ] Tree view: library browser sorted by section number with L1/L2/L3 badges.
- [ ] Status bar indicator: coverage summary for the open workspace.
- [ ] Marketplace publish — stretch goal.

### Microsoft Word extension `[ ]`

Reach into the editor practitioners actually use.

- [ ] Office Add-in (TypeScript) targeting Word desktop + web.
- [ ] Ribbon command: "Insert encoded statute" — picker over the local library, inserts English transpilation as formatted text + footnote link to SSO anchor.
- [ ] Context menu on a SG Penal Code citation (e.g. "s415") → hover card with marginal note, penalty range, illustrations count, and SSO link.
- [ ] Side panel: search/browse by section / title / element keyword with L1/L2/L3 badges.
- [ ] Live check: paste a Yuho snippet into Word; add-in streams it to `yuho check` and marks errors inline.
- [ ] Stretch — "Convert statute citation → Yuho skeleton" button.
- [ ] Office.js app manifest + Microsoft AppSource publish (stretch).

### Remaining tooling gaps `[ ]`

- [ ] **G4** illustration-count validator — `yuho check` fails lint when an encoded section has strictly fewer illustrations than `_raw/act.json` has canonical illustrations for that section.
- [ ] **G11** `all_of` / `any_of` sanity — compare statute's English "or" / "and" connectives against the element-group combinator. LLM judge via MCP client or pattern-match near element markers.
- [ ] **G10** semantic hookup for cross-section references. Resolver walks `referencing` / `subsumes` / `amends` edges so queries like "all sections that extend s415" become answerable.
- [ ] Fine-cap regression sub-linter: if raw text says "with fine" without a number, encoding must use `fine := unlimited`.
- [ ] Caning regression sub-linter: if raw text says "liable to caning" without a number, encoding must use `caning := unspecified`.
- [ ] Aggregate-all-errors compilation (LexScript pattern) — don't short-circuit on first parse error.

### Ideas borrowed from other legal DSLs `[ ]`

Discovered while auditing LexScript (MIT), lam4 (Apache-2.0), LDOC,
Catala (Apache-2.0).

- [ ] **Tarjan SCC + BFS over the statute reference graph** (LexScript). Catches unreachable exception branches and cyclic cross-refs. Unlocks after G10 gives a real graph to traverse.
- [ ] **DOCX transpile target** (LDOC concept). Generates a formatted Word-compatible statute summary: elements as headings, penalty + illustrations as numbered clauses, SSO footnote anchors. Complements the Word extension work.
- [ ] **Named-norm references / `IS_INFRINGED` predicate** (lam4). Lets `s107` abetment express "if `s299` IS_INFRINGED, then …" in grammar. Composes with G10.
- [ ] **Scope composition** (Catala). Callable statute scopes so s34 common intention and s107 abetment can wrap arbitrary base offences as functions.

---

## Deferred

### Documentation site `(def)`

Final polish. Static HTML site built from the committed library.

- [ ] Index page listing all 524 encoded PC sections with L1/L2/L3 badges.
- [ ] Per-section page: raw statute text + encoded `.yh` (syntax-highlighted) + Mermaid diagram + English transpilation + SSO deep-link.
- [ ] Cross-reference graph page (needs G10).
- [ ] Coverage dashboard page.
- [ ] Gap / review notes linked from affected sections.

### Phase 2a — Historical versions `(def)`

- [ ] Extend `scrape_sso.py` with `--historical` flag. Enumerate `/Act/<CODE>/Historical/<DATE>` snapshots.
- [ ] Store each historical snapshot under `library/<act>/_raw/historical/<date>.json`.
- [ ] Extend AST's `effective_dates` semantics to thread version lineage.
- [ ] Coverage harness extension — per `(section, valid-date)` rows.
- [ ] Temporal query support: "what did s300 look like in 1995?"

### Phase 2b — Vision pivot `(def)`

Only after PC L3 coverage is high and tooling is battle-tested.

- [ ] Evidence Act (EA1893)
- [ ] Criminal Procedure Code
- [ ] Constitution (CONS1963)
- [ ] Contract Law (common law + Misrepresentation Act, Contracts (Rights of Third Parties) Act, etc.)
- [ ] Civil remedies and equitable doctrines — require AST shapes Yuho doesn't have yet.
