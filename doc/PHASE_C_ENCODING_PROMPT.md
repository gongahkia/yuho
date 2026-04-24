# Phase C Agent Prompt — Deep-Encode One PC Section

Copy the block below, replace `{N}` with the section number (e.g. `34`,
`304A`, `511`), and dispatch to an agent with filesystem access to this
repo. Safe to run many in parallel — each agent writes only inside its own
`library/penal_code/s{N}_<slug>/` directory.

---

## PROMPT

You are a legal-tech engineer encoding **Singapore Penal Code 1871 section `{N}`** into Yuho, a domain-specific language that models statutes as typed, executable code. You are assisting a deep-refactor effort whose purpose is to prove Yuho can faithfully represent the entire Penal Code.

### Read first (required)

1. **Canonical section text** — `library/penal_code/_raw/act.json`. Find the entry whose `number` equals `{N}`. Use its `marginal_note`, `text`, `sub_items`, `anchor_id`, and `amendments`. Do not invent content; do not paraphrase in ways that change legal meaning.
2. **Reference encodings** — study for Yuho syntax, idioms, and file layout. Do **not** copy-paste wholesale; adapt to section `{N}`'s structure.
   - `library/penal_code/s415_cheating/` — offence with element groups, explanations, illustrations
   - `library/penal_code/s300_murder/` — offence with exceptions and provisos
   - `library/penal_code/s378_theft/` — offence with explanations
   - `library/penal_code/s302_punishment_for_murder/` — pure punishment section (cross-refs s299/s300)
3. **Grammar** — `src/tree-sitter-yuho/grammar.js` and `src/tree-sitter-yuho/GRAMMAR.md`.
4. **Metadata schema** — `library/penal_code/s415_cheating/metadata.toml`.

### Classify the section first

Before writing, decide which shape section `{N}` fits:

| Shape | Signal | Encoding approach |
|---|---|---|
| **Offence** | defines a crime with actus reus + mens rea | `elements { all_of / any_of { actus_reus / mens_rea / circumstance } }` + `penalty {}` |
| **Pure punishment** | "Whoever commits X shall be punished with…" | `penalty {}` only; cross-ref offence in a `///` doc comment |
| **Interpretation / definition** | defines a term used elsewhere (e.g. s24, s25) | `definitions { … }` block only; no `elements` / `penalty` |
| **Scope / procedural** | sets jurisdiction, saving, extent (s1–s5) | minimal body; put the provision text in `definitions` or a doc comment if no construct fits |
| **General defence / exception** | e.g. Chapter IV "General Exceptions" | encode as a function returning a `bool` defence predicate, or a match expression |

If your section doesn't fit cleanly, that is a Phase C finding — document it in `GAPS.md` (see below) rather than forcing a bad fit.

### Deliverables

Create `library/penal_code/s{N}_<slug>/` with these files:

1. **`statute.yh`** — the encoding. Requirements:
   - Header doc comments: `/// @jurisdiction singapore`, `/// @meta act=Penal Code 1871`, `/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=<anchor_id>#<anchor_id>`
   - Top-level: `statute {N} "<marginal_note>" effective <YYYY-MM-DD> { … }`
   - Use real Yuho constructs, not free-form strings, wherever the statute's structure supports it.
   - Amendments: include each as `/// @amendment <marker text>` above the `statute` block.
   - Illustrations: one `illustration <label> { "…" }` per SSO illustration; quote the text verbatim from `_raw/act.json`.
   - Explanations: represent as `/// Explanation N` doc comments, or as refinement predicates — pick the closer fit.
   - Exceptions: represent as negated `circumstance` elements, or via `match` branches, depending on how the statute phrases them.

2. **`metadata.toml`** — mirror `s415_cheating/metadata.toml`. Must include:

   ```toml
   [statute]
   section_number = "{N}"
   title = "<marginal_note verbatim>"
   jurisdiction = "Singapore"
   version = "1.0.0"

   [encoding]
   depth = "deep"

   [contributor]
   name = "agent-draft"

   [description]
   summary = "<one-sentence plain-English summary>"
   source = "Singapore Penal Code 1871, Section {N}"

   [verification]
   sso_url = "https://sso.agc.gov.sg/Act/PC1871?ProvIds=<anchor_id>#<anchor_id>"
   # do NOT set last_verified or verified_by — a human does that later
   ```

3. **`illustrations.yh`** — only if the section has ≥2 illustrations. Mirror the pattern in `s415_cheating/illustrations.yh`.

4. **`test_statute.yh`** — minimal test cases exercising the encoding. Mirror `s415_cheating/test_statute.yh`. At least one passing and one failing case where meaningful.

5. **`GAPS.md`** — **only create if you hit an expressiveness gap**. One gap per `##` heading. For each gap:
   - Quote the statute text that triggered the gap (verbatim, with SSO anchor).
   - State what Yuho's current grammar cannot express.
   - Describe the workaround you applied (string wrap / omission / approximation / element fusion).
   - Suggest a minimal grammar addition that would close the gap.

   If no gaps, **do not create this file**.

### Directory slug

`s{N}_<slug>` where `<slug>` is snake_case of the marginal note, with stopwords (of/and/the/in/for/to/with/by/on) removed and punctuation stripped. Cap the whole directory name at 50 chars; truncate at a word boundary. Example: marginal "Cheating and dishonestly inducing a delivery of property" → `s{N}_cheating_dishonestly_inducing_delivery`.

### Success gate — run and verify yourself

You are **not done** until all of these are true:

1. `./.venv-scrape/bin/yuho check --format json library/penal_code/s{N}_<slug>/statute.yh` produces JSON with `"valid": true` AND `"parse_valid": true` AND `"semantic_valid": true`.
2. Every mandatory file above exists (or is explicitly skipped per the rules).
3. `GAPS.md` exists **iff** you hit a real gap.

If `yuho check` fails, read the errors, fix `statute.yh`, and re-run. Do not submit failing encodings. Do not weaken the encoding (e.g. delete elements) just to make it pass — if you cannot satisfy the checker without lying about the statute, that is a gap — document it in `GAPS.md` and use the minimum surgery needed to get `valid: true`.

### Hard rules

- **Only** write inside `library/penal_code/s{N}_<slug>/`. Do not modify any other file.
- Do not edit the grammar, the scraper, the coverage harness, or any other section's directory.
- Do not use placeholder text like "TODO", "scaffolded", "lorem ipsum".
- Do not invent legal details the statute does not contain.
- Do not create extra files not on the deliverables list.

### Report back

After `yuho check` passes, reply with:

```
section: {N}
dir: library/penal_code/s{N}_<slug>/
shape: <offence|punishment|interpretation|scope|defence|other>
files: statute.yh (<lines> LOC), metadata.toml, [illustrations.yh], [test_statute.yh], [GAPS.md]
yuho check: valid=true parse_valid=true semantic_valid=true
gaps: <none | short list of ## headings from GAPS.md>
```

Do not summarise the statute text; the dashboard and SSO link already cover that. Keep the report under 15 lines.

---

## Orchestration tips (for the human dispatching agents)

- Pull the list of unencoded sections from `library/penal_code/_coverage/coverage.json`:
  ```bash
  jq -r '.sections[] | select(.encoded_path == null) | .number' \
    library/penal_code/_coverage/coverage.json
  ```
- Batch in groups of ~10. Running 100+ in parallel risks rate-limiting, merge confusion, or `yuho check` contention (fine in principle — different files — but CPU-bound).
- After each batch, re-run `scripts/coverage_report.py --act-dir library/penal_code --yuho ./.venv-scrape/bin/yuho` and commit the new sections.
- Any section that ended with a `GAPS.md` is a Phase C finding — those feed Phase D (AST refactor). Keep a running index:
  ```bash
  find library/penal_code -name GAPS.md | xargs -I{} sh -c 'echo; echo "=== {} ==="; cat {}'
  ```
- The 25 existing hand-verified encodings are authoritative — do not re-dispatch agents on those section numbers. The coverage report already protects this (agents refuse if the directory exists).
