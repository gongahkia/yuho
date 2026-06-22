# Phase D — Flag Fix Prompt

Copy the block below, replace `{N}` with the PC section number, and
dispatch to Codex gpt-5.4 high. Agent reads the section's existing
`_L3_FLAG.md`, the canonical text, and the current encoding, then makes
the **minimum edit** needed to address the flag. If the edit passes
`yuho check`, the `_L3_FLAG.md` is deleted to signal success.

---

## PROMPT

You are fixing a flagged Singapore Penal Code 1871 encoding. **Section `{N}`.**

The flag lives at `library/penal_code/s{N}_<slug>/_L3_FLAG.md`. Read it
first. It tells you exactly which L3 checklist item(s) failed and what
fix the reviewer suggested.

### Inputs

1. **The flag file** — `library/penal_code/s{N}_<slug>/_L3_FLAG.md`. Treat the "suggested fix" line as authoritative. If the suggested fix is unclear or underspecified, fall back to the "reason" line.
2. **Canonical text** — the `library/penal_code/_raw/act.json` entry whose `number == "{N}"`. This is the ground truth. Every edit must be backed by this text.
3. **Current encoding** — `library/penal_code/s{N}_<slug>/statute.yh`.
4. **Grammar** — `src/tree-sitter-yuho/grammar.js` for primitive syntax. Noteworthy: multi-`effective` clauses, `subsection (N) { … }`, `penalty or_both / cumulative / alternative`, `penalty when <ident>`, `fine := unlimited`, `exception { priority N defeats name }`.
5. **Reference good encodings** — `s415_cheating/`, `s300_murder/`, `s378_theft/` are gold patterns.

### What to do

1. Make the **minimum edit** to `statute.yh` that addresses the flag. Do NOT re-encode the whole section. Do NOT touch other files in the directory.
2. Strictly respect the canonical text. If the flag says "remove invented value X", delete X. If the flag says "add missing content Y", add Y with text verbatim from the canonical `act.json`. Do not paraphrase.
3. No fabrication rules: if the statute says "with fine" without a number → `fine := unlimited`; if the statute says "liable to caning" without a stroke count → **`caning := unspecified` (G14 keyword — prefer this to supplementary-text fallback)**; missing limbs must be quoted verbatim from `_raw/act.json`.
4. Some flags use the "three-way any combination of punishments" pattern (G12 in `doc/PHASE_C_GAPS.md`). Current workaround: two sibling penalty blocks — `penalty cumulative { imprisonment := …; supplementary := "imprisonment imposed"; }` + `penalty or_both { fine := unlimited; caning := unspecified; supplementary := "fine or caning or both, per canonical text"; }`. **Never** write `caning := 0 .. 0 strokes` or any invented numeric range — that is fabrication.
5. Run `./.venv-scrape/bin/yuho check --format json library/penal_code/s{N}_<slug>/statute.yh`. It must emit `valid: true`, `parse_valid: true`, `semantic_valid: true`. If it fails, iterate up to 3 times. If still failing, leave the file in the best state you can and proceed to step 7 as a "partial".
6. If the edit is successful AND `yuho check` passes, **delete the `_L3_FLAG.md` file** in this section's directory. This signals the next L3 review pass that the flag has been addressed.
7. Report what you did (see format below).

### Hard rules

- Only write inside `library/penal_code/s{N}_<slug>/`.
- Do NOT edit other sections. Do NOT touch grammar, scraper, `_raw/act.json`, `_coverage/`, or the shared `_L3_flags.md`.
- Do NOT invent statutory content. Every added clause must be sourced from `_raw/act.json`.
- Do NOT mass-rewrite when the flag asks for a small edit.
- Do NOT run git commands.

### Report format (final message, under 12 lines)

```
section: {N}
flag_item: <checklist number(s) from _L3_FLAG.md>
edit: <one-sentence description of what you changed>
yuho_check: valid=<true|false> parse_valid=<true|false> semantic_valid=<true|false>
flag_deleted: <true|false>
notes: <one line if anything surprising>
```
