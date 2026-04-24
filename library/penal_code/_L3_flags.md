# Phase D L3 — flagged sections for human review

_Aggregated from per-section `_L3_FLAG.md` files. Regenerate by re-running `phase_d_l3_review.py`._

## s304C — L3 flag

- failed: 9
- reason: The encoding includes a generic `effective 1872-01-01` clause even though canonical section 304C was introduced by amendment `[15/2019]`, so the effective-date metadata is not sane.
- suggested fix: Remove the generic 1872 effective date and retain the amendment-era effective date that corresponds to the section's introduction.

## s376 — L3 flag

- failed: 8
- reason: The encoding does not preserve the statute's disjunctive structure faithfully because subsection (3) is modeled as `penalty or_both` despite the text saying only "fine or to caning", and subsection (4)'s paragraphs (a), (b), and (c) are not expressed as a formal top-level `any_of`.
- suggested fix: Replace subsection (3) with an alternative additional-penalty encoding and model subsection (4) with an explicit disjunctive `any_of` structure following the s375 gold-standard pattern.

## s376H — L3 flag

- failed: 7
- reason: The canonical subsection (2) is conditional, but the encoding preserves only the subsection (2)(b) 2-year/fine/or-both branch and omits the separate subsection (2)(a) punishment branch.
- suggested fix: Encode the missing subsection (2)(a) penalty branch verbatim and preserve the full conditional penalty structure from the canonical entry.

## s377BD — L3 flag

- failed: 6, 8
- reason: The canonical `act.json` entry for section 377BD is truncated at subsection (1)(b), but the Yuho file adds three specific limb-(b) conditions and an `all_of` structure that cannot be verified from the canonical review source.
- suggested fix: Reconcile subsection (1)(b) against an authoritative source or a repaired canonical extract, then re-review the limb structure and connective mapping.

