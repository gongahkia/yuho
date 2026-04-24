# Yuho — Outstanding Work

Authoritative backlog. Consolidates the old `roadmap.md` (phases A–D + deferred
Phase 2) and the Phase D sweep follow-ups. Positioning is deliberately
narrow: **a robust DSL + cohesive proof of concept for Singapore criminal
law (Penal Code)**, not a general legal-tech platform.

Status key: `[x]` done · `[~]` in progress · `[ ]` pending · `(def)` deferred.

---

## Completed phases (history)

### Phase A — Ingestion `[x]`
- [x] Playwright scraper at `scripts/scrape_sso.py` (`index` + `act` subcommands)
- [x] `library/_index/sso_acts.json` — 500 current SG Acts
- [x] `library/penal_code/_raw/act.json` — Penal Code 1871, 524 sections

### Phase B — Coverage harness `[x]`
- [x] `scripts/coverage_report.py` — L1 / L2 / L3 dashboard
- [x] `library/penal_code/_coverage/{COVERAGE.md,coverage.json}`
- [x] L3 signoff via `metadata.toml [verification]`

### Phase C — Expressiveness probes `[x]`
- [x] Mass encoding of all PC sections (524/524 L1+L2 green)
- [x] Findings captured in `doc/PHASE_C_GAPS.md` (G1–G12) and
      `doc/PHASE_C_REVIEW.md` (section-level notes)

### Phase D — AST + grammar refactor (grammar side) `[x]`
- [x] G1  element_group accepts preceding doc comments
- [x] G2  colons in `///` — not a gap (closed)
- [x] G3  multi-letter section suffix (376AA, 377BO, …)
- [x] G5  subsection nesting (`subsection (1) { … }`)
- [x] G6  multiple `effective <date>` clauses
- [x] G7  not a gap (flat `definitions` already works; G5 covers nesting)
- [x] G8  `penalty or_both / alternative / cumulative` + `fine := unlimited`
- [x] G9  conditional `penalty when <ident> { … }` branches
- [x] G10 not a grammar gap (`referencing`, `subsumes`, `amends` already parse)

---

## Active work

### Phase D sweep (running) `[~]`

Codex re-encodes every non-L3 section using the strict Phase D prompt
+ new primitives. Launched at `medium` reasoning, parallel 8.

- Dispatcher: `scripts/phase_d_reencode.py`
- Prompt: `doc/PHASE_D_REENCODING_PROMPT.md`
- Progress log: `.phase_d_progress.jsonl` (resume-safe)
- Monitor: one line per section completion

Re-run (or resume) command:

```bash
.venv-scrape/bin/python scripts/phase_d_reencode.py --all-remaining \
    --dispatch --parallel 8 --retries 1 --timeout 900 \
    --reasoning medium \
    --progress .phase_d_progress.jsonl --resume
```

### After the sweep lands `[ ]`

- [ ] Re-run `coverage_report.py`; confirm 524/524 L1+L2 green.
- [ ] Review `.phase_d_progress.jsonl` for `status: failed` entries; re-dispatch
      individually, bump to `--reasoning high` if they fail twice.
- [ ] Spot-check 20–30 random encodings against `_raw/act.json` (illustrations
      preserved, no fabricated fine caps, correct subsection shape, right
      `all_of` vs `any_of`).
- [ ] Single bulk commit for the sweep (`phase D wave 2 — bulk re-encoding`).

### L3 review — auto-stamp via heuristics + agents `[ ]`

Goal: lift L3 from 40 to 400+. Use high-reasoning agents (Opus / GPT-5.5 xhigh)
to read each encoded section against `_raw/act.json` and stamp when safe.

- [ ] Write a per-section reviewer prompt that outputs either
      `stamp` (faithful) or `flag` (ambiguous) with reasons.
- [ ] Dispatch in parallel. Progress-tracked the same way as the encoding sweep.
- [ ] Heuristic auto-stamp (simple definitions, ≤3 canonical illustrations,
      single-sentence statute text).
- [ ] Manual / human review for everything flagged.

### G13 grammar fix — default-logic exception priority `[ ]`

New gap identified from studying Catala (Apache-2.0). SG Penal Code uses
prioritised provisos heavily — s300 Exception 1 (grave provocation)
overrides the base murder definition and has its own sub-provisos.
Yuho's current `exception` block is flat, no priority DAG, no conflict
resolution semantics. This is Catala's `label e1` / `exception e1
definition` pattern with prioritised rewriting based on Prof. Sarah
Lawsky's default-logic formalisation of statutes.

Inspect first: `src/yuho/ast/nodes.py` already lists `priority: int` and
`defeats: str` on `ExceptionNode` — verify whether these are actually
wired into (a) the grammar, (b) the semantic analyzer, (c) the Z3
encoder. If partially wired, finish the job; if grammar-only, build the
rest.

- [ ] Confirm `exception { priority <N> defeats <name> }` parses.
- [ ] Semantic analyzer: build the exception DAG per statute, detect cycles.
- [ ] Z3 encoder: emit default-logic-style exception priority so "no two
      unrelated exceptions fire simultaneously" is verifiable.
- [ ] Doc: walk through s300 Murder as the worked example.

### G12 grammar fix — mixed cumulative + alternative penalties `[ ]`

Sections like s420, s115, s325 need "imprisonment X AND ALSO fine or caning or
both." Current workaround: two sibling penalty blocks + `supplementary` strings.
Fix direction: nested penalty combinators, e.g.

    penalty cumulative {
      imprisonment := 0 years .. 10 years;
      or_both {
        fine := unlimited;
        caning := 0 .. 24 strokes;
      }
    }

- [ ] Extend `penalty_block` grammar for nested combinators.
- [ ] Extend `PenaltyNode` to carry the nested structure (or a list of
      sub-penalties with their own combinators).
- [ ] Re-encode the ~50 affected sections using the new syntax.

---

## Expansions — things we are keeping and want to make better

### MCP server expansion `[ ]`

Now the primary AI-integration surface (absorbs what the cut LLM module used
to do; MCP clients own the LLM, Yuho exposes structured data + prompts).

- [ ] Audit current MCP tools in `src/yuho/mcp/server.py`. Document each.
- [ ] Add tools for the full Phase C workflow so external agents can encode
      + verify a new statute end-to-end: `yuho_propose_encoding`,
      `yuho_check_encoding`, `yuho_preview_transpile`.
- [ ] Expose library search / navigation tools: find by SSO anchor, list
      sections citing a given section, fetch canonical raw text alongside
      encoded AST for side-by-side reads.
- [ ] Resources for the Phase D strict prompt + grammar spec so clients can
      self-onboard.
- [ ] Rich prompts covering: encode-from-English, explain-encoding,
      find-fidelity-issues, recommend-L3.
- [ ] Add the cross-section-reference resolver here once G10 semantic
      hookup lands.
- [ ] Integration test: drive a Codex Cloud / Claude session purely via MCP
      to re-encode a fresh PC section, end-to-end.

### LSP buff-up `[ ]`

Editor experience is a keeper. Extend after the sweep settles so the
diagnostics reflect the new grammar primitives.

- [ ] Inlay hints — effective-date range, burden qualifier, mens rea type,
      element count, illustration count.
- [ ] Hover — show canonical SSO URL + excerpt from `_raw/act.json` for the
      section under cursor.
- [ ] Code lens inline per statute — "L1 ✓ L2 ✓ L3 ?" with click-to-open
      coverage dashboard.
- [ ] Cross-file rename (`s415` across the library).
- [ ] Goto-definition into `referencing` / `subsumes` / `amends` targets
      once G10 lands.
- [ ] Diagnostic: illustration-count mismatch vs raw (G4 tooling lint).
- [ ] Diagnostic: `all_of` used where statute text says "or" (G11 tooling lint).
- [ ] Diagnostic: fabricated fine cap (statute says "with fine" + encoding
      uses numeric money range instead of `unlimited`).

### VS Code extension expansion `[ ]`

Primary editor. Neovim plugin was cut in the endpoint trim.

- [ ] Snippets for each statute shape: offence, pure punishment,
      interpretation, subsection block.
- [ ] Command: "Open SSO page for this section" (uses the anchor from
      `/// @meta source=...`).
- [ ] Command: "Run yuho check on this file" with inline errors.
- [ ] Command: "Transpile to Mermaid → preview side panel."
- [ ] Tree view: library browser sorted by section number with L1/L2/L3
      badges.
- [ ] Status bar indicator: coverage summary for the open workspace.
- [ ] Marketplace publish — stretch goal.

### Microsoft Word extension `[ ]`

Lawyers live in Word. A Word add-in that lets a drafter hover over a
Yuho-encoded citation or drop in a rendered statute block makes Yuho
useful inside the editor real practitioners use.

- [ ] Office Add-in (JavaScript/TypeScript) targeting Word desktop + web.
- [ ] Ribbon command: "Insert encoded statute" — open a picker over the
      local library, insert the English transpilation as formatted text
      plus a footnote link to the SSO anchor.
- [ ] Context menu on a SG Penal Code citation (e.g. "s415") →
      hover card with marginal note, penalty range, illustrations
      count, and SSO link.
- [ ] Side panel: search/browse the library by section number, title,
      or element keyword, with per-section L1/L2/L3 badges.
- [ ] Live check: paste a Yuho snippet into Word, the add-in streams
      it to `yuho check` and marks errors inline.
- [ ] Stretch — "Convert statute citation → Yuho skeleton" button that
      drafts a statute block the practitioner can refine.
- [ ] Office.js app manifest + Microsoft AppSource publish (stretch).

### Remaining tooling gaps `[ ]`

- [ ] **G4** illustration-count validator — `yuho check` fails lint when an
      encoded section has strictly fewer illustrations than
      `_raw/act.json` has canonical illustrations for that section.
- [ ] **G11** `all_of` / `any_of` sanity — compare statute's English "or" /
      "and" connectives against the element-group combinator. LLM judge
      via MCP client or pattern-match near element markers.
- [ ] **G10** semantic hookup for cross-section references. Resolver walks
      `referencing` / `subsumes` / `amends` edges so queries like "all
      sections that extend s415" become answerable.
- [ ] Sub-linter: if raw text says "with fine" without a number, encoding
      must use `fine := unlimited` (prevents fabricated-cap regressions).

### Ideas borrowed from other legal DSLs `[ ]`

Discovered while auditing LexScript, Intellect, lam4, LDOC, Catala.

- [ ] **Tarjan SCC + BFS over the statute reference graph** (LexScript,
      MIT). Catches unreachable exception branches and cyclic cross-refs.
      Unlocks after G10 gives us a real graph to traverse.
- [ ] **DOCX transpile target** (LDOC, unlicensed — concept only).
      Generates a formatted Word-compatible statute summary: elements as
      headings, penalty + illustrations as numbered clauses, SSO footnote
      anchors. Complements the Word extension work; probably the cleanest
      way to ship Word support is "DOCX transpiler + Word add-in that
      calls `yuho transpile --target docx`."
- [ ] **Named-norm references / `IS_INFRINGED` predicate** (lam4,
      Apache-2.0). Lets `s107` abetment express "if `s299` IS_INFRINGED,
      then ..." in grammar, not doc comments. Composes with G10.
- [ ] **Scope composition** (Catala, Apache-2.0). Callable statute scopes
      so s34 common intention and s107 abetment can wrap arbitrary base
      offences as functions rather than flat text references.
- [ ] **LSP "did-you-mean" for unknown directives** (LDOC). Low-cost
      usability win; slots into the LSP buff-up tasks.
- [ ] **Aggregate-all-errors compilation** (LexScript). Yuho currently
      short-circuits on first parse error; LexScript walks the tree,
      emits every diagnostic, and only fails after. Better UX for
      editors.

### Outreach / collaboration `[ ]`

- [ ] File an issue / email SMU CCLAW about lam4 collaboration. Yuho +
      SG Penal Code corpus could feed their solver work; shared
      `IS_INFRINGED` / named-norm surface convention for interoperability.
      Physically adjacent (Singapore).
- [ ] File an issue on arismoko/LDOC asking for an SPDX license header
      so any future code-borrowing is safe.

---

## Deferred — run only after everything above is stable

### Documentation site `(def)`

Final polish. Static HTML site built from the committed library.

- [ ] Index page listing all 524 encoded PC sections with L1/L2/L3 badges.
- [ ] Per-section page: raw statute text + encoded `.yh` (syntax-highlighted)
      + Mermaid diagram + English transpilation + SSO deep-link.
- [ ] Cross-reference graph page (needs G10).
- [ ] Coverage dashboard page.
- [ ] Gap / review notes linked from affected sections.

### Phase 2a — Historical versions `(def)`

Current scrape captures the present in-force text only. Amendments are
tagged but historical versions aren't fetched.

- [ ] Extend `scrape_sso.py` with `--historical` flag. Enumerate
      `/Act/<CODE>/Historical/<DATE>` snapshots.
- [ ] Store each historical snapshot under
      `library/<act>/_raw/historical/<date>.json`.
- [ ] Extend AST's `effective_dates` semantics to thread version lineage
      (grammar already supports multiple `effective` clauses; semantic
      analyzer needs to make them first-class).
- [ ] Coverage harness extension — per `(section, valid-date)` rows.
- [ ] Temporal query support: "what did s300 look like in 1995?"

### Phase 2b — Vision pivot `(def)`

Only after PC L3 coverage is high and the tooling is battle-tested.

- [ ] Evidence Act (EA1893)
- [ ] Criminal Procedure Code
- [ ] Constitution (CONS1963)
- [ ] Contract Law (no single statute — common law plus the Misrepresentation
      Act, Contracts (Rights of Third Parties) Act, etc.)
- [ ] Civil remedies and equitable doctrines — will require AST shapes
      Yuho doesn't have yet.
