# Phase C — Expressiveness Gaps

Surfaced during bulk encoding of the Singapore Penal Code and during a
deeper L3-style review by Opus 4.7 acting as the reviewer. This file is
the historical discovery log; current status is Phase D complete for the
grammar/resolver items used by the corpus.

## Already identified during encoding

### G1 — element_group rejects preceding doc comments ✅ FIXED

`all_of { ... }` and `any_of { ... }` blocks cannot be preceded by a
`///` doc comment.

**Fix landed:** `element_group` rule now accepts `repeat(doc_comment)`
before the combinator keyword. Verified by smoke test + regression pass
against all 524 encodings.

### G2 — colons break /// doc comments ✅ NOT A GAP

Agent report from wave 1d could not be reproduced on post-fix grammar.
A `:` inside `///` doc-comments parses cleanly. Likely the original
wave-1d errors were misdiagnosed — an unrelated parse failure that
happened to be on a line containing a colon.

**No fix required.** Closing.

### G3 — section_number token only accepts single trailing letter ✅ FIXED

Grammar rule `section_number = \d+[A-Z]?` rejected multi-letter suffixes
like `376AA`, `377BA..377BO`, `377CA`, `377CB`. Affected ~37 real PC
sections.

**Fix landed:** token now matches `\d+[A-Z]*`. All 37 affected
encodings migrated from the `statute <num>.<n>` decimal workaround to
the correct suffix (e.g. `statute 377BO "..."`). The temporary
`/// @section <original>` doc comments have been removed.

## Identified during L3 review

### G4 — no first-class model for illustrations as legal authority ✅ LINTED

In the Penal Code, illustrations are binding statutory content — they
disambiguate mens rea, fix the boundary of an offence, and are cited in
courts. Yuho's `illustration <label> { "…" }` node stores them as free
strings, which led agents to silently drop them when the section was
classified as "interpretation" or when the section had many
illustrations (s464 has 16 illustrations, encoded has 0; s511 has 4,
encoded has 0; s350 has 8, encoded has 1 *fabricated* one).

**Current status:** illustrations are AST children and the fidelity
diagnostic compares encoded illustration counts against the canonical
scrape. The Phase D audit found 98 post-fix illustration-count warnings;
these are lint findings rather than parser gaps.

### G5 — subsections with distinct content have no structural home ✅ FIXED

Sections like s377BO have seven numbered subsections covering separate
legal rules (e.g. extraterritoriality by citizenship vs. by act-location
vs. by victim-location). The grammar had no `subsection N { … }`
construct, so agents flattened all seven rules into one-line definitions.

**Fix landed:** new `subsection_block` rule nests inside `statute_block`
(and inside other subsections — arbitrary depth). Number syntax accepts
`(1)`, `(2A)`, `(a)`, `(iii)`, or bare numerics. New `SubsectionNode` in
the AST carries its own definitions / elements / penalty / illustrations
/ exceptions / nested subsections. Verified on a multi-subsection test
file; all 524 existing encodings remain green.

**Data side:** landed across the corpus where needed. The post-fix
frequency report counts 123 uses of subsection blocks.

### G6 — `effective` date cannot reflect amendment-introduced sections ✅ FIXED

All 524 sections carry `effective 1872-01-01` in their encodings because
that is the act's commencement. But s377BO, s4B, s22A, s26A-H, s74A-E,
etc. were *introduced* by later amendments (commonly [15/2019]). Their
legal effective date is the amendment date, not 1872.

**Current effect:** any Phase 2 work on historical versions will return
wrong results. Temporal queries ("was s377BO in force in 2015?") will
say yes when they should say no.

**Fix landed (grammar side):** `statute_block` now allows multiple
`effective <date>` clauses. Encodings can now write

    statute 377BO "..."
        effective 1872-01-01
        effective 2019-12-31
    { ... }

expressing original-act-commencement + amendment-introduction.

**Data side:** landed across the corpus where needed. The post-fix
frequency report counts 243 multiple-`effective` uses.

### G7 — no decomposition for long interpretation sections with nested terms ✅ SUBSUMED BY G5

Sections like s22 ("Property"), s29 ("Document"), s377C (sexual-offence
definitions) define ~4–12 terms inside one section.

**Resolution:** On closer look, the current grammar's
`definitions { term := "string"; … }` already supports a flat list of
independent term/definition pairs. The earlier "giant string" pattern
wasn't a grammar limitation — agents just chose not to decompose. With
G5 subsections now available, sections that truly need scoped sub-
definitions (e.g. s377C subsection (1) vs (2)) can use
`subsection (1) { definitions { term := "..."; } }`.

No separate grammar work required. Re-encoding agents will be told to
decompose.

### G8 — no explicit model for alternative punishments ✅ FIXED

The Penal Code's standard penalty pattern is "imprisonment up to N
years, or fine, or both," sometimes with caning. Yuho's `penalty { }`
block has separate slots for `imprisonment`, `fine`, `caning`, but no
way to encode whether they are alternative (`or`) or cumulative
(`and`), and no way to encode "fine with no statutory cap".

**Current effect:** (a) agents systematically invent fine caps —
$5,000, $10,000, $20,000, $30,000 — where the statute says only "with
fine" (no cap). Every one of these caps is fabricated. Affected
sections include s153, s166, s269, s325, s420, s501, s504, s505, and
likely most offence sections. (b) Caning is often omitted entirely (s325,
s420, s325). (c) "or both" semantics are lost.

**Fix landed (grammar side):**

1. `fine := unlimited` is now a valid fine-clause form. AST carries
   `fine_unlimited: bool`.
2. `penalty` now accepts an optional combinator keyword:
   `penalty cumulative { ... }` (all clauses required together — default),
   `penalty alternative { ... }` (exactly one applies),
   `penalty or_both { ... }` (any one, or any combination — the dominant
   PC idiom). AST carries `combinator: Optional[str]`.

Wire-up verified: grammar parses, AST builder reads the fields,
`yuho check` / ast / semantic all pass.

**Data side:** landed across the corpus where needed. The post-fix
frequency report counts 249 `fine := unlimited` uses and 190
`penalty or_both` uses.

### G9 — no support for conditional / branch-dependent penalties ✅ FIXED

s153 has "if rioting committed, 3yr; if not, 1yr." s304A has "(a) rash
act → 5yr; (b) negligent act → 2yr." These are distinct penalty branches
keyed on facts.

**Fix landed:** `penalty_block` now accepts an optional `when <ident>`
clause. Sections with branched punishment can write sibling penalty
blocks:

    penalty when rash_act     { imprisonment := 0 days .. 5 years; fine := unlimited; }
    penalty when negligent_act { imprisonment := 0 days .. 2 years; fine := unlimited; }

`PenaltyNode` now carries `condition: Optional[str]`. `StatuteNode`
keeps the first penalty as the backwards-compatible `penalty` field and
collects sibling blocks in `additional_penalties`.

**Data side:** landed across the corpus where needed. The post-fix
frequency report counts 49 conditional penalty branches.

### G10 — no cross-section reference primitive ✅ NOT A GAP (GRAMMAR SIDE)

Agents invented `referencing penal_code/s441_criminal_trespass` as a
pseudo-syntax (s325, s420, s442).

**Resolution:** this is a real AST node. `referencing_statement` has
existed in the grammar since v5. The grammar also has `subsumes <num>`
and `amends <num>` clauses on `statute_block`. Agents used the existing
grammar correctly.

**Resolver side:** landed. `yuho refs` builds the cross-section
reference graph, and the evaluator/Z3 layers understand `is_infringed`
/ `apply_scope` guards.

### G12 — mixed cumulative + alternative penalty clauses ✅ FIXED

Surfaced during the Phase D priority-batch re-encoding of s420: "imprisonment
for a term which may extend to 10 years, and shall also be liable to fine or
to caning or to both." This is cumulative imprisonment AND alternative
(fine | caning | both). Neither `penalty cumulative { ... }` nor `penalty
or_both { ... }` alone expresses it — the imprisonment is always imposed,
the fine/caning is a separate choice.

**Fix landed:** nested penalty combinators are accepted, e.g.:

    penalty cumulative {
      imprisonment := 0 years .. 10 years;
      or_both {
        fine := unlimited;
        caning := 0 .. 24 strokes;
      }
    }

`PenaltyNode.nested` carries the nested sub-combinator. The post-fix
frequency report counts 11 nested penalty uses.

### G11 — `any_of` vs `all_of` misclassification risk ✅ LINTED

s505 has three alternative mens-rea arms: intent to cause mutiny OR
intent to cause public fear OR intent to incite class hatred. The
encoding wraps all three in an `all_of { mens_rea … mens_rea … mens_rea … }`
block, which is legally wrong — the statute requires any one of them.

**Current status:** this is a fidelity diagnostic, not a grammar fix.
The checker compares raw connective cues against encoded element-group
shape. The Phase D audit found 208 post-fix G11 warnings and treats the
heuristic as low precision.

### G14 — caning liability without stroke count ✅ FIXED

Surfaced from the Phase D L3 re-review. Several sections (s21, s73,
s304C, s376, s376H, s377, s377BB, s377BD, s377BG) say *"liable to
fine or to caning"* with no stroke-count range. Current grammar:
`caning := <int> strokes` or `caning := <int> .. <int> strokes`.
Nothing expresses "caning liability without a statutory numeric cap."

Fix-agents correctly refuse to invent a range and instead write the
caning clause into `supplementary := "…"` strings, which the L3
reviewer then flags as "not structured penalty facts." Genuine
expressiveness gap, not a fabrication or encoding bug.

**Fix landed:**

    caning := unspecified            // or: caning := liable
    caning := 12 .. unspecified      // minimum stated, no cap

`"unspecified"` is a valid `caning_clause` value alongside
`integer_literal` and `integer_literal .. integer_literal`. AST fields
`caning_min` / `caning_max` remain `Optional[int]`, with
`caning_unspecified: bool` parallel to `fine_unlimited`. The post-fix
frequency report counts 31 uses.

## Fabrication findings (not grammar gaps, but require fixing)

These surfaced during the L3 review and go beyond what Phase D grammar
fixes can address. They need targeted re-encoding.

- **s350 Criminal Force**: encoded with `penalty { fine := $0 .. $1,000 }`
  and an invented illustration. The section has **no penalty at all** —
  it's a pure definition; punishment is in s352. The illustration
  "The conduct of A matches the statutory criteria defined under
  section 350" is agent boilerplate, not statutory text.
- **s269 Negligent act**: fine cap `$5,000` fabricated (statute says
  "with fine" — unlimited).
- **s166, s501, s504, s505**: fine clauses in the statute are missing
  from encoded `penalty { }`.
- **s325**: caning clause missing (statute says "liable to fine or to
  caning"); fine cap `$30,000` fabricated.
- **s420**: imprisonment floor `1 year` fabricated (statute says only
  "may extend to 10 years", no minimum). Caning missing.
- **s304A**: encoded with single 5-year imprisonment range, losing the
  2-year branch for negligent acts.

See `doc/PHASE_C_REVIEW.md` for additional section-level findings as
they are collected.
