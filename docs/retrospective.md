# Yuho — retrospective

Consolidated lessons from Phases A through D of the encoding effort.
Written after L3 reached 524/524 sections at human-verified tier.

This is an honest retrospective: what worked, what didn't, what we'd do
differently. Audience: future contributors, paper readers wanting the
backstory, and anyone considering encoding a different statute family
under Yuho.

---

## Phases at a glance

| Phase | What it was | Result |
|---|---|---|
| A — Ingestion | Playwright scrape of SSO; structured `_raw/act.json` per Act. | 500 SG Acts indexed; Penal Code 1871 fully scraped (524 sections). |
| B — Coverage harness | L1 / L2 / L3 dashboard; per-section `metadata.toml` for L3 stamps. | Mechanical L1+L2 reporting in CI. |
| C — Expressiveness probe | Mass-encode all 524 sections; surface grammar gaps. | 524/524 L1+L2; 14 gap entries (G1–G14) catalogued. |
| D — Grammar refactor + L3 sweep | Close grammar gaps; agent-driven re-encoding; L3 review dispatcher. | 524/524 L3-stamped at human-verified tier. |

For per-section provenance see [`/library/penal_code/_ledger/LEDGER.md`](../library/penal_code/_ledger/LEDGER.md).
For per-gap detail see [`researcher/phase-c-gaps.md`](researcher/phase-c-gaps.md).

---

## What worked

### 1. Grammar gaps as a first-class artefact

Instead of patching the parser ad-hoc whenever an encoding failed, every
parser limitation was logged as a numbered gap with a representative
section, a workaround used in the meantime, and an eventual fix
classification. The 14-gap catalogue made it possible to prioritise:
which gaps blocked many sections vs which were one-off; which were
genuine grammar issues vs lint-layer issues; which were resolvable in
the parser vs which only the diagnostic layer should catch.

The classification mattered: G2 (colons in `///` doc comments) and G7
(no decomposition for long interpretation sections) were originally
flagged as grammar problems, but on closer reading turned out not to
be gaps at all. Conflating "the parser rejected this" with "the
grammar needs an extension" leads to grammar bloat with no
corresponding gain in fidelity. The catalogue forced a second look
before any extension landed.

### 2. Three-tier coverage with a real human pass

L1 (parses) and L2 (lints + fidelity diagnostics) are mechanical and
correctly automatable. The honest add was L3: a structured 11-point
human checklist that covers what mechanical checks cannot
(illustration completeness, marginal-note matching, no fabrication of
penalty facts, faithful disjunctive/conjunctive English, sane
amendment lineage). Without the L3 tier, the project would have
shipped 524 L2-passing encodings with high fabrication rates and no
auditable claim of fidelity.

### 3. Agent-driven encoding + dispatcher

Phase D's core mechanism was a dispatcher that renders a structured
prompt per section and invokes an agentic coder
(`gpt-5.4` `high`) on each. Three flavours:

- **Re-encoder** (`scripts/phase_d_reencode.py`) — given a section, produce a clean encoding from the canonical text + the gap-aware grammar.
- **L3 reviewer** (`scripts/phase_d_l3_review.py`) — given a section's encoding, run the 11-point checklist and STAMP or FLAG.
- **Flag-fixer** (`scripts/phase_d_flag_fix.py`) — given a `_L3_FLAG.md`, apply the minimum edit that addresses the flag.

This let the project move from 122 L3-stamped sections at the start of
the dispatcher era to 524 with about four hours of compute. The same
work by hand would have taken weeks.

### 4. Per-section progress logs with `--resume`

Every dispatcher writes append-only JSONL of its decisions and supports
`--resume` against the same file. This made multi-hour runs robust to
crashes, allowed mid-flight kills, and gave a clean per-section audit
trail that fed straight into the provenance ledger.

### 5. Fidelity diagnostics over canonical scrape

Four lint passes that compare the encoded AST to `_raw/act.json` — illustration count, fabricated fine cap, fabricated caning range, disjunctive-connective mismatch — caught the most common encoding errors before they reached L3. They also acted as evidence in the paper: gaps that looked like grammar issues turned out to be diagnostic-layer issues, and the same fidelity check that was the root cause was also the fix.

### 6. Single source of truth + radial UIs

The encoded `.yh` file is canonical. Everything else (English, LaTeX, Mermaid, Alloy, DOCX, JSON corpus, browser extension data, static site, ledger, benchmark) regenerates from it. This kept downstream surfaces in sync without manual labour: rebuild corpus, downstream artefacts cascade.

---

## What didn't work

### 1. Initial under-investment in the L3 reviewer prompt

Early L3 review runs flagged sections for problems the reviewer prompt
didn't actually contain. The fix was to make the 11-point checklist
mechanical: numbered checks, explicit pass/fail criteria per check,
explicit reference encodings (s415 cheating, s300 murder) as the gold
standard, and a strict report format. Once the prompt was tightened,
flag rates stabilised and re-runs were largely deterministic.

Lesson: an agentic reviewer is only as reliable as its checklist.
Spend time on the prompt; you'll spend more time triaging if you
don't.

### 2. Fabricated penalty caps

The single most common fidelity error during Phase C and early Phase D
was an encoder reading "with fine" or "liable to caning" in the
canonical text and inventing a numeric range to fit the grammar
(e.g. `caning := 0 .. 24 strokes`). This was the motivating use case
for the G8 (`fine := unlimited`) and G14 (`caning := unspecified`)
sentinels, and for the matching fidelity diagnostics. Once the grammar
supported "I genuinely don't know the cap because the statute doesn't
say one", encoders stopped fabricating.

Lesson: if your DSL doesn't have a way to say "the source text is
silent", encoders will fill the silence with invention.

### 3. Effective-date confusion across the [15/2019] cluster

The Criminal Law Reform Act 2019 (Act 15 of 2019) commenced on either
2019-12-31 or 2020-01-01 depending on which provision and which
authoritative source you read. Early Phase D encodings used
2019-12-31 across the board; the L3 reviewer pushed back on this with
"repo-local precedent treats Act 15 of 2019 commencement as
2020-01-01". The fix was a sweep over the affected sections plus a
note in the encoding conventions that all `[15/2019]` provisions use
`effective 2020-01-01`.

Lesson: amendment dates in penal codes are messy and authoritative
sources sometimes disagree. Pick a convention, document it, and
enforce it via the L3 prompt.

### 4. Empty subsections survived earlier reviews

Many sections shipped Phase C with `subsection (N) { }` blocks that
were structurally present but textually empty when the canonical
statute had substantive content under that subsection number. L1 and
L2 happily passed these because the encoding parsed and lint had no
way to know subsection (N) should have content. Only L3 caught them.

Lesson: structural-presence checks are not the same as
content-faithfulness checks. We added an "empty subsection"
diagnostic late in Phase D; it should have been there from L2 day one.

### 5. Flag-fix dispatcher needed multiple iterations on the prompt

The first flag-fix prompt was too laissez-faire and would re-encode
whole sections when the flag asked for a small edit. Later prompts
were tightened to require minimum edits and to enumerate the canonical
no-fabrication rules (the unlimited / unspecified sentinels, the
nested-combinator pattern for "any combination of punishments", the
verbatim-from-act.json rule for missing limbs). After the tighter
prompt landed, the dispatcher's `FIXED` rate jumped to ~100% with
zero `ERROR` outcomes.

Lesson: agentic patchers need bounded prompts. Tell them what *not*
to do as explicitly as what *to* do.

### 6. CLI doc divergence

The CLI reference in `docs/user/cli-reference.md` documents a number
of commands (`api`, `explain`, `playground`, `static-site`,
`webhook`, `workspace`) that were never implemented in
`src/yuho/cli/main.py`. The doc-contract test catches this; the doc
needs trimming. Recorded as outstanding in `todo.md`.

Lesson: do CLI doc generation from the actual command tree if you
can. Hand-written CLI docs drift.

---

## What we'd do differently

### 1. Build the diagnostic layer before the encoder

Phase D added the four fidelity diagnostics late, after most of the
mass-encoding had already happened with the bad patterns baked in.
Result: hundreds of fabricated penalty caps that had to be swept out
in a flag-fix run. If the diagnostics had been L2 from the start,
they would have failed encoders' first attempt and prevented the
fabrication entirely.

### 2. Make the canonical scrape the absolute single source of truth

For the first half of Phase D the encoder agents had access to the
canonical text *and* to one another's encoded sections (via the
reference good encodings list). When the reference encodings had
errors, those errors propagated. Later runs scoped agents tighter to
`_raw/act.json` only, which reduced cross-contamination. The
reference good encodings are still useful but should be flagged as
"shape only, not text".

### 3. Pre-compute the amendment-date convention table

We discovered `[15/2019]` confusion section-by-section, costing many
flag-fix iterations. A pre-compiled table (Act → commencement-date
canonical answer, sourced once from SSO history) handed to the
encoder upfront would have eliminated the cluster.

### 4. Treat the L3 prompt as a versioned API

The 11-point checklist evolved during Phase D. Sections stamped
under v1 of the checklist may not satisfy v3 of the checklist. We
papered over this with timestamps in `metadata.toml` and a final
sweep, but a versioned prompt with explicit "this stamp was issued
under prompt vN" annotation would have been more rigorous.

### 5. Earlier investment in the corpus + downstream UIs

We held off on building the JSON corpus / browser extension / static
site until after L3 was largely done. With hindsight, the corpus
would have been useful earlier as a debug surface (per-section
side-by-side of canonical / `.yh` / English) that human reviewers
could have used to triage flagged sections faster.

---

## Numbers worth keeping

| | |
|---|---:|
| Sections in scope (Penal Code 1871) | 524 |
| L1 + L2 final | 524 / 524 |
| L3 stamped final | 524 / 524 |
| Grammar gaps catalogued | 14 |
|   resolved in parser | 10 |
|   not-a-gap (parser already worked) | 2 |
|   resolved in lint layer | 2 |
| Implementation SLOC | ~51k (pyproject-counted) |
| Encoded library SLOC | ~23k of `.yh` |
| Phase-D L3 reviewer wall time | ~3.5h (4-way parallel `gpt-5.4` `high`) |
| Phase-D flag-fix dispatcher wall time | ~36 min (4-way parallel) |
| Total agent decisions logged | 484 L3 reviews + 166 flag fixes |

---

## For future statute-family contributors

If you're encoding a statute family other than the SG Penal Code,
read this in order:

1. [`researcher/phase-c-gaps.md`](researcher/phase-c-gaps.md) — every grammar gap, with the offending shape and the fix.
2. [`researcher/phase-d-l3-review-prompt.md`](researcher/phase-d-l3-review-prompt.md) — the 11-point checklist.
3. [`researcher/phase-d-reencoding-prompt.md`](researcher/phase-d-reencoding-prompt.md) — the structured re-encoding prompt.
4. [`researcher/phase-d-flag-fix-prompt.md`](researcher/phase-d-flag-fix-prompt.md) — the minimum-edit flag-fix prompt.
5. [`contributor/porting-guide.md`](contributor/porting-guide.md) — file-level porting steps.

The non-negotiable conventions, distilled:

- Canonical scrape is ground truth. Every encoded clause must be sourced from it.
- "I don't know" is a first-class construct: `fine := unlimited`, `caning := unspecified`. Never invent ranges.
- Disjunctive English (",  or") → `any_of`. Conjunctive English (",  and") → `all_of`. Don't paraphrase the connective.
- Empty subsection blocks are wrong. Either fill them or remove them.
- Effective dates are the amendment commencement dates, not the original 1872 date, when the section was introduced or rewritten by an amendment.
- The L3 stamp is a human-verified claim of fidelity. Don't issue it for an encoding you haven't read end-to-end against the canonical text.
