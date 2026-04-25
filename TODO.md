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

Current snapshot: **524/524 L1+L2 green · 122 L3 stamped · all 14
grammar gaps (G1–G14) closed or deferred to tooling.**

Completed history (Phases A–D, L3 flag fixes, MCP expansion, LSP buff-up,
VS Code extension v0.2, DOCX transpile target, fidelity diagnostics) lives
in git log + `doc/PHASE_*` notes, not here.

---

## Next session — priority queue

### Recommended near-term sequence `[~]`

Revised after audience clarification: practical usefulness first, then
novelty / interestingness. The Word add-in is still valuable, but is now a
later practitioner-facing surface rather than the next keystone task.

- [ ] **G10 cross-section resolver.** Keystone. Unblocks LSP goto-definition,
      Tarjan SCC, `IS_INFRINGED`, cross-reference explorer pages, and stronger
      paper claims about multi-section reasoning.
- [ ] **Penal Code explorer — split into three artefacts sharing one corpus.**
    - [ ] **2a. Enriched JSON corpus.** Per-section: raw SSO text, `.yh`, controlled English, Mermaid SVG, metadata, badges, flags, SSO anchor. Single source of truth; both UIs read from this.
    - [ ] **2b. Browser extension v0.** Headline product demo. Content script on `sso.agc.gov.sg/Act/PC1871*` that overlays a side-by-side Yuho panel and pop-up explanations on hover. Highest demo leverage.
    - [ ] **2c. Static explorer site.** Citable URLs, downloadable bundles, search-indexable. Reuses the same JSON corpus. Lower priority — extension covers the headline demo; site is the research artefact tail.
- [ ] **Yuho benchmark pack.** Generate reusable tasks from the encoded corpus:
      citation grounding, penalty extraction, offence-element classification,
      exception application, cross-reference lookup, and temporal-validity
      questions. Output should be JSONL + README + evaluation harness.
- [ ] **Scenario / fact-pattern simulator.** Small YAML/JSON fact format plus
      worked examples for representative offences (e.g. cheating, theft,
      culpable homicide, murder, abetment, common intention). Research and
      teaching demo only; no legal-advice posture.
- [ ] **Provenance and fidelity ledger.** Per-section metadata for raw SSO
      hash, scrape date, Yuho version, encoding commit, L1/L2/L3 state, flags,
      and known caveats. Makes the corpus citable and auditable.
- [ ] **Grounded AI answer verifier.** MCP / CLI workflow that refuses or
      downranks answers not grounded in raw SSO anchors, encoded AST nodes, or
      generated English fragments. Useful for AI-tool builders later, but
      framed as research infrastructure.
- [ ] **Paper methodology hardening.** Tie the paper evaluation to reproducible
      scripts: SLOC stats, coverage stats, diagnostic hit-rate, encoding
      throughput, gap-frequency chart, benchmark generation.
- [ ] **Practitioner-facing surfaces.** Word add-in, VS Code Marketplace,
      AppSource, and polished lawyer workflows after the explorer and research
      artefacts are credible.

### Repository restructure + documentation overhaul `[x]`

Bring the repo's presentation layer to PAR. Done.

- [x] Audit current top-level layout — proposal at `docs/researcher/restructure-proposal.md` with current vs proposed tree, blast radius per move, and commit sequence A–J.
- [x] **Commit A** — `LICENSE`, `CITATION.cff` added at root.
- [x] **Commit B** — `src/pyproject.toml` → `pyproject.toml` at root. Hatch hook updated. CI workflows updated (`ci.yml`, `release.yml`, `integration.yml`). VS Code README install command updated.
- [x] **Commit C** — `doc/` → `docs/` rename. Symlink `doc -> docs` retained for back-compat with the running L3 dispatcher (`scripts/phase_d_*.py` TEMPLATE_PATH was bound at module load and would fail without the symlink). Symlink can be removed once dispatcher idle.
- [x] **Commit D** — Audience reorg: `docs/{user,contributor,researcher}/` with kebab-case filenames. PHASE_D prompts kept at `docs/` root for the running dispatcher; will move to `researcher/` after L3 completes.
- [x] `docs/INDEX.md` written, audience-grouped TOC.
- [x] `docs/README.md` rewritten as a stub pointer.
- [x] **Commit E** — `asset/` → `assets/` rename (top-level + docs/asset → docs/assets).
- [x] **Commit F** — empty `packages/` removed.
- [x] **Commit G** — `statutes/` (3 stale demo files) absorbed into `examples/`. All three parse cleanly.
- [x] **Commit H** — Top-level `README.md` rewritten in HF/Catala style: hero block, badge cluster, author link to `gabrielongzm.com`, "What is Yuho?" 3-paragraph pitch, 3-tab quickstart (read/encode/understand), feature matrix, architecture diagram, project status table, BibTeX citation block.
- [x] All internal markdown cross-links rewired to new paths via bulk Python script. `tests/test_local_markdown_links_resolve` passes (all 5 known broken links — `openapi.yaml`, `cookbook/`, `library/`, `.github/CONTRIBUTING.md`, `PORTING_GUIDE.md` — manually fixed).
- [x] Tests touched by restructure all pass: `test_docs_contract::test_dsl_docs_cover_new_constructs`, `test_docs_contract::test_local_markdown_links_resolve`, `test_cli_transpile`. Pre-existing `test_documented_cli_commands_exist` failure (CLI commands documented but not implemented: `api`, `explain`, `playground`, `static-site`, etc.) is unrelated to restructure.
- [x] Tests fixed: `tests/test_cli_transpile.py` — added DOCX mock to handle the new transpile target.

Outstanding (deferred):
- [ ] Once L3 dispatcher idle: move `docs/PHASE_D_*PROMPT.md` to `docs/researcher/phase-d-*.md` with kebab-case; remove `doc -> docs` symlink.
- [ ] Render `paper/figures/architecture.mmd` to `docs/architecture.svg` (requires `mmdc`).
- [ ] Write `docs/retrospective.md` consolidating PHASE_C_REVIEW + PHASE_D_*PROMPT lessons-learned.
- [ ] Pre-existing `test_documented_cli_commands_exist` — the CLI reference documents commands not implemented in `cli.commands`. Either implement them or trim the doc.
- [ ] `CLAUDE.md` symlink at root works for local user but breaks for other contributors. Either unsymlink + plain-file with a note, or `.gitignore` it.
- [ ] Phase-D progress JSONL files at root — should move under `library/penal_code/_coverage/` or a new `state/` dir for tidiness.

### Research paper (LaTeX) `[~]`

arXiv preprint, attributed, acmart `manuscript` mode. Full first draft
landed; outstanding work is empirical methodology runs and submission
hardening.

All 8 sections drafted (1,464 prose lines total under `paper/sections/`):
intro 118, background 160, design 294, implementation 249, evaluation 226,
related 254, limitations 108, conclusion 55.

Outstanding before submission:
- [ ] **Manual read-through pass.** Read the rendered PDF cover-to-cover, mark places where prose drifts, claims need a citation, or a paragraph buries the lede. Add detail where missing (especially in evaluation §5 and limitations §7) but stay tight — no padding. Aim: every paragraph earns its place.
- [ ] **Switch to two-column layout.** Current build is single-column smoke (`article`) plus single-column acmart `manuscript`. For density and venue-readiness, swap `main.tex` documentclass to `\documentclass[sigconf]{acmart}` (two-column ACM conf style). This gets `table*` to span both columns, tightens line lengths, and roughly halves page count. Re-check Figure 1 fit at narrower column width; may need `\begin{figure*}` for the s415 listing.
- [ ] **Blog-post transpilation.** Hand the rendered paper to Claude with the prompt: *"Transpile this paper into a markdown blog post for gabrielongzm.com. Target ~1500 words. Keep the thesis (statute-as-source-of-truth + the 14-grammar-gaps argument), drop the implementation SLOC tables, drop the methodology threats-to-validity, keep one worked example (s415), keep the Catala/lam4/LexScript comparison as prose not table. Conversational tone, link to the GitHub repo, embed coverage stats inline."* Output to `paper/blog/yuho.md`.
- [ ] **Evaluation methodology runs** — fill the `\todo{}` placeholders in `evaluation.tex`:
    - Fidelity diagnostic hit-rate methodology (re-run 4 diagnostics over all 524 sections, spot-check 30 warnings per check)
    - Encoding throughput numbers (median + p95 wall-clock; reconstructable from git timestamps + `.phase_d_l3_progress.jsonl`)
    - Gap-trigger frequency bar chart (source data in `doc/PHASE_C_GAPS.md`)
- [ ] Render Mermaid figures to PDF (requires `mmdc`), inspect, and tune layouts.
- [ ] Verify all `\cite{}` keys resolve cleanly. Some bib entries carry TODO notes — confirm canonical citations for `lam4`, `lexscript`, `ldoc`, `hammond1983rights`. Fix the two bibtex warnings (`ldoc` missing author/key for sort; `jackson2002alloy` has redundant volume+number).
- [ ] `scripts/repo_stats.py` — emit SLOC-per-layer JSON so the implementation Table 1 can be auto-regenerated rather than hand-typed.
- [ ] External-reader pass on the full PDF; tighten phrasing and integrate cross-references where the prose has drift between sections.
- [ ] Decide final venue (currently arXiv-attributed, `manuscript,nonacm` mode). For ICAIL/JURIX retargeting, swap documentclass per `paper/README.md`.

---

## Public Penal Code explorer `[ ]`

Research / education product surface. This should be the main product demo
before the Word add-in because it makes the corpus inspectable without asking
readers to install editor tooling.

- [ ] Static index page listing all 524 encoded PC sections with title, section
      number, offence / interpretation / punishment shape where known, and
      L1/L2/L3 badges.
- [ ] Per-section page: raw SSO text, encoded `.yh`, controlled English,
      Mermaid diagram, source metadata, SSO deep-link, L3 stamp / flag status.
- [ ] Coverage dashboard page regenerated from
      `library/penal_code/_coverage/coverage.json`.
- [ ] Gap / review notes linked from affected sections.
- [ ] Cross-reference graph page (blocked on G10).
- [ ] Download bundle: JSON corpus, benchmark JSONL, and citation metadata
      once the benchmark pack exists.

## Yuho benchmark pack `[ ]`

Research artefact for evaluating legal reasoning over Singapore statutory
text. This complements the DSL paper and gives external AI / legal-tech users
a concrete reason to use the corpus without turning Yuho into a chatbot.

- [ ] Generate citation-grounding tasks: given a question or claim, identify
      the supporting Penal Code section / subsection / illustration anchor.
- [ ] Generate penalty-extraction tasks: imprisonment range, fine cap /
      unlimited fine, caning, alternative vs cumulative vs `or_both`.
- [ ] Generate element-classification tasks: actus reus, mens rea,
      circumstance, burden qualifier, exception, illustration.
- [ ] Generate cross-reference tasks once G10 lands: "which sections reference,
      subsume, amend, or extend section N?"
- [ ] Generate temporal-validity tasks after Phase 2a begins: "was section N
      in force on date D?" / "what changed between versions?"
- [ ] Ship dataset card, limitations, non-legal-advice disclaimer, and a small
      scorer so paper results are reproducible.

## Scenario / fact-pattern simulator `[ ]`

Teaching and research demo for executable statutes. Keep the format narrow and
honest: structured facts in, Yuho-derived element / exception report out.

- [ ] Define a minimal JSON/YAML fact-pattern schema with parties, acts,
      mental-state facts, circumstances, dates, and claimed exceptions.
- [ ] Add worked fixtures for 5-8 representative offences.
- [ ] Expose a CLI command or MCP tool that reports satisfied / unsatisfied
      elements with links back to source spans.
- [ ] Avoid probabilistic prediction or legal-advice language; output should be
      a trace over the encoded statute, not a legal conclusion.

## Provenance and fidelity ledger `[ ]`

Make the corpus citable, auditable, and defensible as a research artefact.

- [ ] Per-section ledger row: raw SSO source hash, scrape date, SSO anchor,
      Yuho version, encoding commit, encoder / reviewer metadata where known.
- [ ] Carry L1/L2/L3 state, current flags, known caveats, and grammar-gap
      dependencies.
- [ ] Emit machine-readable JSON and human-readable markdown.
- [ ] Surface ledger data in the explorer, MCP resources, and paper stats.

## Grounded AI answer verifier `[ ]`

Research infrastructure for AI-assisted legal work. The goal is not to build
another legal chatbot; it is to test whether model outputs are grounded in the
encoded corpus and canonical source text.

- [ ] Define an answer schema: claims, citations, source spans, confidence, and
      unsupported-claim diagnostics.
- [ ] Add MCP / CLI checker that validates citations against raw SSO anchors
      and encoded AST nodes.
- [ ] Add refusal / caveat policy for answers with unsupported propositions.
- [ ] Use benchmark-pack tasks as regression tests for the verifier.

## Microsoft Word extension `[ ]`

Practitioner-facing surface. Keep this on the roadmap, but sequence it after
the explorer / benchmark / provenance artefacts because the primary audience
is research and education. DOCX transpile target already landed — Word add-in
can call `yuho transpile -t docx` directly.

- [ ] Office Add-in (TypeScript) targeting Word desktop + web under `editors/word-yuho/`.
- [ ] Ribbon command: "Insert encoded statute" — picker over the local library, inserts English transpilation as formatted text + footnote link to SSO anchor.
- [ ] Context menu on a SG Penal Code citation (e.g. "s415") → hover card with marginal note, penalty range, illustrations count, and SSO link.
- [ ] Side panel: search/browse by section / title / element keyword with L1/L2/L3 badges.
- [ ] Live check: paste a Yuho snippet into Word; add-in streams it to `yuho check` and marks errors inline.
- [ ] Stretch — "Convert statute citation → Yuho skeleton" button.
- [ ] Office.js app manifest + Microsoft AppSource publish (stretch).

## LSP — remaining polish `[ ]`

- [ ] Cross-file rename (`s415` across the library).
- [ ] Goto-definition into `referencing` / `subsumes` / `amends` targets — blocked on G10 semantic hookup.

## VS Code extension — remaining polish `[ ]`

- [ ] Tree view panel: library browser sorted by section number with L1/L2/L3 badges.
- [ ] Marketplace publish (stretch).

## Remaining tooling gaps `[~]`

- [x] **G10** semantic hookup for cross-section references. Done.
    - `src/yuho/library/reference_graph.py` — `ReferenceGraph` data structure, `ReferenceEdge` typed edges (subsumes / amends / implicit), `build_reference_graph()` walks library and emits edges from explicit `subsumes`/`amends` clauses + implicit regex matches over element descriptions / doc comments / case-law holdings.
    - `yuho refs` CLI — query subcommand with `--in` / `--out` / `--kind` / `--transitive` / `--graph` / `--json` flags.
    - 19 tests in `tests/test_reference_graph.py`, all passing.
    - Live graph over the SG Penal Code: 152 nodes, 130 edges (5 subsumes + 125 implicit). Top-referenced: s467, s2, s375, s378, s377BB.
- [ ] Aggregate-all-errors compilation (LexScript pattern) — don't short-circuit on first parse error.

## Ideas borrowed from other legal DSLs `[ ]`

Discovered while auditing LexScript (MIT), lam4 (Apache-2.0), Catala (Apache-2.0).

- [ ] **Tarjan SCC + BFS over the statute reference graph** (LexScript). Catches unreachable exception branches and cyclic cross-refs. Unlocks after G10.
- [ ] **Named-norm references / `IS_INFRINGED` predicate** (lam4). Lets `s107` abetment express "if `s299` IS_INFRINGED, then …" in grammar. Composes with G10.
- [ ] **Scope composition** (Catala). Callable statute scopes so s34 common intention and s107 abetment can wrap arbitrary base offences as functions.

## L3 long tail `(def)`

~400 shorter / simpler sections still unstamped. Most are single-sentence
interpretation sections where the encoding is a faithful mirror and the
bug surface is small.

- [ ] Revisit when L3 matters for a concrete deliverable.
      Command: `phase_d_l3_review.py --all-unstamped --dispatch --reasoning medium --parallel 8`.

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
