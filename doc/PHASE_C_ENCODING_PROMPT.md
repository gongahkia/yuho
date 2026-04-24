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

### Success gate — depends on your execution access

**If you have shell + filesystem access** (e.g. Claude Code, Codex CLI, Aider):
1. Write the files directly into `library/penal_code/s{N}_<slug>/`.
2. Run `./.venv-scrape/bin/yuho check --format json library/penal_code/s{N}_<slug>/statute.yh`. Iterate on `statute.yh` until the JSON shows `"valid": true` AND `"parse_valid": true` AND `"semantic_valid": true`.
3. You are not done until every mandatory file exists and the check passes.

**If you do NOT have execution access** (e.g. chat session with no tools):
1. Emit every file's full contents as a fenced code block, with the path on the line immediately above the block, exactly like:

       library/penal_code/s{N}_<slug>/statute.yh
       ```yh
       <full file contents>
       ```

       library/penal_code/s{N}_<slug>/metadata.toml
       ```toml
       <full file contents>
       ```

2. Explicitly state in your report: `check not run; human verifies via .venv-scrape/bin/yuho check <path>`.
3. Even without execution, produce encodings you have high confidence will pass — mentally trace the grammar in `src/tree-sitter-yuho/grammar.js`.

**Either mode:** do not submit encodings you know to be failing. Do not weaken the encoding (e.g. delete elements) to paper over a failure — if you cannot satisfy the checker without lying about the statute, that is a gap — document it in `GAPS.md` and apply the minimum surgery needed to get `valid: true`.

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

## Orchestration (for the human dispatching agents)

Dispatcher: `scripts/phase_c_prompt.py` renders this template with section
context pre-filled. Usage and parallel-dispatch best practices live in
`doc/PHASE_C_ORCHESTRATION.md`.

Quick list of unencoded sections:

```bash
.venv-scrape/bin/python scripts/phase_c_prompt.py --list | head
```

Dispatch a single section (copy to clipboard on macOS):

```bash
.venv-scrape/bin/python scripts/phase_c_prompt.py 34 | pbcopy
```
