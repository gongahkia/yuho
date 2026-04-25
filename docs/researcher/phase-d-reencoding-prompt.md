# Phase D — Strict Re-Encoding Prompt

Copy the block below, replace `{N}` with the PC section number, and
dispatch to a Codex (or Claude) agent with filesystem access. Fixes all
the fidelity problems that the Phase C L3 review surfaced: fabricated
fine caps, missing illustrations, flattened subsections, wrong effective
dates, and `all_of`/`any_of` confusion.

---

## PROMPT

You are re-encoding **Singapore Penal Code 1871 section `{N}`** in Yuho,
fixing a prior low-fidelity draft. The grammar now supports new
primitives that your draft must use.

### Mandatory reads (in order)

1. **Canonical statute text** — `library/penal_code/_raw/act.json`. Find the entry whose `number == "{N}"`. Use every field: `text`, every `sub_items[]` entry (illustrations, explanations, exceptions, headings), every `amendments[]` entry, the `anchor_id`. **Do not paraphrase legal text in ways that change meaning. Do not invent facts.**
2. **Existing draft** — `library/penal_code/s{N}_<slug>/statute.yh` (if present). Treat it as a starting point only. Assume it is wrong until proven otherwise.
3. **Reference encodings (post-D grammar)** — these are known-good hand-verified patterns:
   - `library/penal_code/s415_cheating/` — offence with element groups, explanations, illustrations
   - `library/penal_code/s300_murder/` — offence with exceptions and provisos
   - `library/penal_code/s378_theft/` — offence with explanations
   - `library/penal_code/s302_punishment_for_murder/` — pure punishment section
4. **Grammar spec** — `src/tree-sitter-yuho/grammar.js`. Especially the new primitives described below.

### New grammar primitives you MUST use where applicable

| Pattern in statute text | New grammar primitive |
|---|---|
| multi-letter section suffix (376AA, 377BO, 377BA) | `statute 376AA "..." { ... }` — direct, no decimal workaround |
| multiple numbered subsections (1), (2), (3) with distinct content | `subsection (1) { ... } subsection (2) { ... }` nested in the statute block |
| statute added by amendment (e.g. [15/2019] introduces s377BO) | two `effective` clauses: `effective 1872-01-01 effective 2019-12-31` |
| statute says "with fine" with no dollar cap | `fine := unlimited` — NEVER invent a cap |
| statute says "liable to caning" with no stroke count | `caning := unspecified` — NEVER invent a stroke range, NEVER write `0 .. 0 strokes` |
| statute says "X years, or fine, or both" (typical PC pattern) | `penalty or_both { imprisonment := ...; fine := unlimited; }` |
| statute gives conditional punishment ("if rash, 5yr; if negligent, 2yr") | two sibling penalty blocks with `when`: `penalty when rash_act { ... } penalty when negligent_act { ... }` |
| doc-comment rationale on a group (`all_of` / `any_of`) | `/// rationale\nall_of { ... }` — now valid, don't omit |

### Zero-fabrication rules

These are hard errors if violated:

- **Do NOT invent a fine cap.** If the statute says only "with fine" without a dollar amount, write `fine := unlimited`. Caps of $5,000 / $10,000 / $20,000 / $50,000 that agents invented in the first wave are factually wrong — they must not reappear.
- **Do NOT invent a penalty for sections that have none.** Interpretation / definition sections (e.g. s350 "Criminal force") have NO penalty. Do not add a `penalty { }` block for them. The punishment for criminal force is in s352; that is s352's encoding job, not s350's.
- **Do NOT invent illustrations.** If the statute has zero illustrations, your encoding has zero. If the statute has N illustrations, your encoding has N, each quoting the text verbatim from `_raw/act.json` (via `illustration <label> { "<exact text>" }`).
- **Do NOT invent caning.** Omit `caning := ...` unless the statute explicitly says caning. Conversely, if the statute says "liable to caning" DON'T omit it — encode `caning := <n> strokes` or the right range.
- **Do NOT flatten subsections.** A section with (1) / (2) / (3) must use `subsection (1) { ... } subsection (2) { ... } subsection (3) { ... }`. Do not collapse them into freeform definitions or doc comments.
- **Do NOT confuse `all_of` and `any_of`.** Read the statute's English connectives. "and" / conjunctive lists → `all_of`. "or" / "one or more of" → `any_of`. "or both" is the PC's shorthand for `penalty or_both`. s505 was wrongly encoded as `all_of` in the first wave — agent re-checks the logical structure before committing.
- **Do NOT boilerplate `effective 1872-01-01`** if the section was introduced by a later amendment. The `amendments[]` array in `_raw/act.json` gives the real date. At minimum include both the original 1872 act commencement AND the amendment date.

### Deliverables

Create or overwrite files in `library/penal_code/s{N}_<slug>/`:

1. **`statute.yh`** — the new encoding. Requirements:
   - Header: `/// @jurisdiction singapore`, `/// @meta act=Penal Code 1871`, `/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=<anchor_id>#<anchor_id>`, one `/// @amendment <marker>` per canonical amendment.
   - Top-level: `statute {N} "<marginal_note verbatim>" effective <YYYY-MM-DD> [effective <YYYY-MM-DD>] { … }`.
   - For offences: `elements { all_of / any_of { actus_reus, mens_rea, circumstance } }` + `penalty or_both { imprisonment := 0 ... N years; fine := unlimited; }` or whichever combinator matches. Do not omit the combinator if the statute says "or both" — `or_both` is required.
   - For pure punishment sections: `penalty { ... }` + cross-ref the target offence in a doc comment. No `elements { }` unless the section itself restates them.
   - For interpretation sections: `definitions { term1 := "..."; term2 := "..."; }` — flat, one entry per defined term. Decompose; do not dump whole statute text into one string.
   - For sections with subsections: `subsection (1) { ... } subsection (2) { ... }` nesting. Each subsection gets its own `definitions` / `elements` / `penalty` / `illustrations` as the statute text demands.
   - For illustrations: one `illustration <label> { "<verbatim text>" }` per canonical illustration. Label `(a)`, `(b)` stays as `illustration_a`, `illustration_b` or whatever makes the identifier valid. **Quote the illustration text verbatim from `_raw/act.json`**; do not paraphrase.

2. **`metadata.toml`** — update or create. Must include:

   ```toml
   [statute]
   section_number = "{N}"
   title = "<marginal_note verbatim>"
   jurisdiction = "Singapore"
   version = "2.0.0"

   [encoding]
   depth = "deep"
   revision = "phase-D"

   [contributor]
   name = "agent-reencoding-phase-D"

   [description]
   summary = "<one-sentence plain-English summary>"
   source = "Singapore Penal Code 1871, Section {N}"

   [verification]
   sso_url = "https://sso.agc.gov.sg/Act/PC1871?ProvIds=<anchor_id>#<anchor_id>"
   # Leave last_verified and verified_by UNSET. Human reviews L3 separately.
   ```

3. **`GAPS.md`** — create only if you hit a case the new grammar still can't express. One gap per `## G<letter>` heading, quoting the specific statute text.

### Success gate — you are NOT done until

1. `./.venv-scrape/bin/yuho check --format json library/penal_code/s{N}_<slug>/statute.yh` outputs JSON with `"valid": true` AND `"parse_valid": true` AND `"semantic_valid": true`.
2. Your `statute.yh` uses the new grammar primitives where the statute text demands them (subsections, multi-effective, fine := unlimited, or_both, when-branches).
3. Every canonical illustration appears in the encoding.
4. No fabricated penalty facts (no invented caps, no invented caning, no invented sections).
5. You re-read your `statute.yh` after writing and verified it against the canonical text in `_raw/act.json`. Fidelity > cleverness.

If any of these fail, iterate. Do not submit failing encodings.

### Hard rules

- Only write inside `library/penal_code/s{N}_<slug>/`. No git commands. No changes to grammar, scraper, or other sections.
- Do not use placeholder text.
- Do not invent legal details.
- Do not create extra files not on the deliverables list.

### Report format (end of run, under 20 lines)

```
section: {N}
dir: library/penal_code/s{N}_<slug>/
shape: <offence|punishment|interpretation|scope|defence|other>
primitives_used: <comma list: subsection, multi-effective, fine_unlimited, or_both, when, none>
illustrations_kept: <N of M canonical>
subsections_kept: <N of M canonical>
yuho check: valid=<true|false> parse_valid=<true|false> semantic_valid=<true|false>
gaps: <none | short list>
notes: <one line if anything surprising>
```
