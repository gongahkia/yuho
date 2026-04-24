# Phase C — Expressiveness Gaps

Surfaced during bulk encoding of the Singapore Penal Code and during a
deeper L3-style review by Opus 4.7 acting as the reviewer. Each gap is a
concrete input to Phase D (AST/grammar refactor).

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

### G4 — no first-class model for illustrations as legal authority

In the Penal Code, illustrations are binding statutory content — they
disambiguate mens rea, fix the boundary of an offence, and are cited in
courts. Yuho's `illustration <label> { "…" }` node stores them as free
strings, which led agents to silently drop them when the section was
classified as "interpretation" or when the section had many
illustrations (s464 has 16 illustrations, encoded has 0; s511 has 4,
encoded has 0; s350 has 8, encoded has 1 *fabricated* one).

**Current effect:** ~200+ illustrations across the corpus are missing
from encodings.

**Fix direction:** treat illustrations as first-class AST children with
structured content (facts pattern + legal-conclusion fields), and have
`yuho check` require their presence when the raw corpus has them. This
makes silent illustration-drop detectable.

### G5 — subsections with distinct content have no structural home

Sections like s377BO have seven numbered subsections covering separate
legal rules (e.g. extraterritoriality by citizenship vs. by act-location
vs. by victim-location). The grammar has no `subsection N { … }`
construct, so agents flattened all seven rules into one-line definitions.

**Current effect:** multi-subsection sections systematically lose
structure. Examples: s377BO, s377BN, s377CB, s511, s21, s22, s33, s40,
s464.

**Fix direction:** add `subsection <N> { … }` nesting inside `statute`
blocks. Subsections should be able to contain their own definitions,
elements, penalty, and illustrations independently.

### G6 — `effective` date cannot reflect amendment-introduced sections ✅ PARTIALLY FIXED

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

**Still pending (data side):** re-encoding the ~50+ amendment-introduced
sections to actually include the correct second `effective` clause.
This is part of the re-encoding wave, not the grammar fix.

### G7 — no decomposition for long interpretation sections with nested terms

Sections like s22 ("Property"), s29 ("Document"), s377C (sexual-offence
definitions) define ~4–12 terms inside one section, often with nested
lists, recursive sub-definitions, and cross-references. The grammar's
`definitions { term := "string" }` only supports flat key/string pairs.

**Current effect:** agents either (a) dump the entire section as one
giant string bound to a single term (s21, s22, s29, s33, s40 —
technically faithful but useless), or (b) pick ~3 of the defined terms
and invent paraphrased summaries for them (s377C — lost ~8 definitions).

**Fix direction:** allow `definitions { term := <structured> }` where
structured can be a string, a nested definitions block, a list of
alternatives, or a reference. Optionally add a separate
`interpretation_block` node for interpretation sections with different
semantics (Penal Code has ~40 pure-interpretation sections).

### G8 — no explicit model for alternative punishments ✅ PARTIALLY FIXED

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

**Still pending (data side):** re-encoding the ~150+ offence sections
that currently have fabricated fine caps and cumulative-defaulted
penalty blocks. These need to use `fine := unlimited` and
`penalty or_both { ... }` where appropriate.

### G9 — no support for conditional / branch-dependent penalties

s153 has "if rioting committed, 3yr; if not, 1yr." s304A has "(a) rash
act → 5yr; (b) negligent act → 2yr." These are distinct penalty
branches keyed on facts. Yuho's `penalty { }` collapses them to a
single range.

**Current effect:** conditional penalties are silently truncated to
the most-severe branch. Querying Yuho for max sentence returns the wrong
answer on any branch-conditional section.

**Fix direction:** add `penalty { case <condition> := <penalty-block> }`
branching, or similar.

### G10 — no cross-section reference primitive

Agents invented `referencing penal_code/s441_criminal_trespass` as a
pseudo-syntax (s325, s420, s442). It passes `yuho check` because the
checker is lenient, but it's not a real AST node — no semantic binding,
no validation that the referenced section exists, no way to traverse.

**Current effect:** cross-section references exist in text but are not
machine-navigable. Phase 2 features that depend on the reference graph
(e.g. "show me all sections that extend s415 cheating") cannot be built.

**Fix direction:** add a `references <section-number>` clause at
statute top level, semantically resolved to the referenced section's
AST. Optionally add `uses_definition_from <section>` for explicit
dependency.

### G11 — `any_of` vs `all_of` misclassification risk

s505 has three alternative mens-rea arms: intent to cause mutiny OR
intent to cause public fear OR intent to incite class hatred. The
encoding wraps all three in an `all_of { mens_rea … mens_rea … mens_rea … }`
block, which is legally wrong — the statute requires any one of them.

**Current effect:** ~unknown scale, but spot-check found at least one
(s505). The checker has no way to validate that the encoding's boolean
logic matches the statute's English "or" / "and" / "or both".

**Fix direction:** this is not a grammar fix, it's a checking-
infrastructure fix. Add a validation pass that cross-references the
raw statute text's logical connectives against the element-group
structure. Hard in general but feasible with an LLM judge or pattern
matching on "or" / "and" in the raw text near element markers.

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
