# Phase D — L3 Auto-Review Prompt

Copy the block below, replace `{N}` with a PC section number, and
dispatch to a reasoning-capable agent (Codex `gpt-5.4` at `high`, or
Claude Opus). Agent reviews the encoded `.yh` against the canonical
SSO text, decides STAMP or FLAG, and writes its decision + reasoning
back into `metadata.toml`.

---

## PROMPT

You are acting as the L3 reviewer for **Singapore Penal Code 1871
section `{N}`**. Your job is to decide whether the encoded Yuho file
faithfully represents the canonical statute.

You are not rewriting. You are only auditing + stamping.

### Inputs

1. **Canonical text** — `library/penal_code/_raw/act.json`. Find the entry whose `number == "{N}"`. Read every field: `text`, every `sub_items[]` entry (illustrations, explanations, exceptions, headings), every `amendments[]` entry.
2. **Encoded** — the `statute.yh` in the section's `s{N}_<slug>/` dir.
3. **Metadata** — the same dir's `metadata.toml`.
4. **Reference good encodings** — `s415_cheating/`, `s300_murder/`, `s378_theft/`, `s302_punishment_for_murder/`. These are the gold standard for what a faithful encoding looks like.

### Checklist — run through every item

For each, decide PASS / FAIL and note the reason.

1. **Section number matches.** `statute {N} "..."` in the `.yh` file uses the correct section number. (Watch for leftover `377.N` decimal workarounds — those should all have been migrated.)
2. **Marginal note matches.** The statute title in the `.yh` is the verbatim marginal note from `_raw/act.json`, including trailing "etc." and quote marks.
3. **Illustrations complete.** Every canonical illustration in `_raw/act.json` (`kind == "illustration"` or alphabetic sub-items `(a), (b), ...` under an "Illustrations" heading) is present in the `.yh` as a separate `illustration <label> { "..." }` block. Text is verbatim, not paraphrased. Count must match.
4. **Explanations preserved.** Canonical explanations (`kind == "explanation"`) appear either as `/// Explanation N` doc comments or as structured refinements. They must not be silently dropped.
5. **Exceptions preserved.** Canonical exceptions (`kind == "exception"`) appear as `exception <label> { ... }` blocks or as explicitly labelled refinements.
6. **Subsections preserved.** If the canonical text has numbered subsections (1)(2)(3), the encoding uses `subsection (N) { ... }` blocks. No flattening into freeform strings.
7. **No fabricated penalty facts.**
    - If the statute says only "with fine" with no dollar amount → encoding must use `fine := unlimited`, not an invented cap.
    - If the statute says nothing about caning → encoding has no `caning :=` clause.
    - If the statute is a pure definition (no punishment clause at all) → encoding has no `penalty { }` block.
    - If the statute has conditional penalties ("if rash, 5yr; if negligent, 2yr") → encoding uses `penalty when <ident>` sibling blocks, all branches captured.
8. **`all_of` vs `any_of` matches English.** Read the statute's English connectives. Conjunctive lists (", and", "must all") → `all_of`. Disjunctive lists (", or", "any one of") → `any_of`. "or both" → `penalty or_both`. s505-style mis-classification is a FAIL.
9. **Effective date sane.** Sections introduced by later amendments must have the amendment date as one of the `effective` clauses. Generic `effective 1872-01-01` alone on a section tagged [15/2019] or similar is a FAIL.
10. **No placeholder text.** Grep for "TODO", "lorem", "scaffolded", "placeholder", "XXX". Any hit is a FAIL.
11. **`yuho check` still passes.** Run `./.venv-scrape/bin/yuho check --format json library/penal_code/s{N}_<slug>/statute.yh` and confirm `valid: true`, `parse_valid: true`, `semantic_valid: true`.

### Decision

- **STAMP** — every checklist item passes. Write the `[verification]` block in the section's `metadata.toml`:
    ```toml
    [verification]
    last_verified = "2026-04-24"  # use today's date
    verified_by = "gpt-5.4 high (automated L3 reviewer)"
    sso_url = "https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr{N}-#pr{N}-"
    ```
  Preserve any other `[verification]` fields that were already present (sso_url, disclaimer, etc.). Only set `last_verified` and `verified_by`.

- **FLAG** — one or more checklist items fails, OR the decision requires human judgment you are not comfortable making. Do NOT write to `metadata.toml`. Instead, write a per-section flag file at `library/penal_code/s{N}_<slug>/_L3_FLAG.md` with exactly this content:
    ```markdown
    # s{N} — L3 flag

    - failed: <checklist item number(s)>
    - reason: <one-sentence explanation>
    - suggested fix: <one sentence, optional>
    ```
  **Do not** touch `library/penal_code/_L3_flags.md` or any other shared file — the dispatcher aggregates the per-section `_L3_FLAG.md` files at the end of the run so parallel agents never collide.

### Hard rules

- Do NOT edit the `statute.yh` file. Review only.
- Do NOT rewrite canonical text.
- Do NOT stamp sections that fail any checklist item.
- Do NOT create any files other than this section's `_L3_FLAG.md`.
- If `metadata.toml` doesn't exist, create a minimal one with `[statute]` + `[verification]` fields (use the statute number, jurisdiction = "Singapore").
- No git commands.

### Report format (end of run, under 10 lines)

```
section: {N}
decision: STAMP | FLAG
checklist_passed: <count> / 11
failed_items: <comma-separated checklist numbers, or empty>
yuho_check: valid=<true|false>
notes: <one line>
```
