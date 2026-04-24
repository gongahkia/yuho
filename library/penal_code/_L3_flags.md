# Phase D L3 — flagged sections for human review

_Aggregated from per-section `_L3_FLAG.md` files. Regenerate by re-running `phase_d_l3_review.py`._

## s4A — L3 flag

- failed: 8
- reason: The encoding reduces the operative statutory sentence to disconnected `definitions` and does not preserve the conjunctive/deeming structure or the `Chapter 6 ... or 6B ...` disjunction as `elements` with matching `all_of`/`any_of`.
- suggested fix: Re-encode section 4A like section 4, with an operative `elements` block capturing citizen-or-PR status, outside-Singapore conduct, the Chapter 6 or 6B alternative, and the deeming consequence in Singapore.

## s21 — L3 flag

- failed: 9
- reason: The encoding uses only `effective 1872-01-01` even though the canonical section has later amendment markers, including `[Act 18 of 2023 wef 31/01/2024]`, so the effective-date set is incomplete.
- suggested fix: Add the later amendment effective dates reflected in the canonical markers as `effective` clauses on the section.

## s73 — L3 flag

- failed: 9
- reason: The encoding includes an unsupported `excluded_offence` definition in subsection (4) and an inferred `2020-01-01` effective date that cannot be verified from the canonical `act.json` entry alone.
- suggested fix: Reconcile subsection (4) and the effective dates against the authoritative source text/commencement record, then restamp only if the extra content is proven.

## s74C — L3 flag

- failed: 8
- reason: Subsection (5) says the court must determine the relationship having regard to all the circumstances of the case, including listed factors, but the encoding represents those factors as an `any_of` test.
- suggested fix: Re-encode subsection (5) as a non-exhaustive set of considerations rather than a disjunctive element block.

## s188 — L3 flag

- failed: 7
- reason: The encoded subsection (2) invents the wrong fine ranges by using `$2,500` instead of `$5,000` for individuals and `$20,000` instead of `$10,000` for non-individual cases.
- suggested fix: Replace the subsection (2) penalty amounts so they exactly match the canonical statute before re-running L3 review.

## s193 — L3 flag

- failed: 8
- reason: In the `any other case` branch, the encoding makes `fabricates false evidence` a standalone alternative without the shared `intentionally` requirement that the canonical text applies to both `gives` and `fabricates`.
- suggested fix: Restructure that branch so `intentionally` governs both alternatives, e.g. as a shared condition over `gives` or `fabricates`.

## s304C — L3 flag

- failed: 7
- reason: The canonical text makes the offender liable to fine or to caning without stating any caning quantum, but the encoding adds `caning := 0 .. 24 strokes`.
- suggested fix: Remove the invented caning range and encode only the punishment facts expressly stated in the statute.

## s305 — L3 flag

- failed: 7
- reason: The encoded penalties for subsection (1)(a) and subsection (1)(c) collapse conditional sentencing branches into generic `penalty cumulative` blocks and leave the death/life contingencies only in supplementary text, so the machine-readable penalty structure is not faithful to the statute.
- suggested fix: Re-express subsection (1)(a) and subsection (1)(c) as explicit sibling penalty branches, using conditional `penalty when <ident>` blocks for the fine-if-not-death/life or fine-if-not-life limbs and preserving the life-imprisonment alternatives structurally.

## s375 — L3 flag

- failed: 8
- reason: Subsection (2) uses `penalty or_both` even though the canonical text says imprisonment plus liability to fine or to caning, not “or both”.
- suggested fix: Re-encode subsection (2) as mandatory imprisonment plus an alternative fine-or-caning branch, matching the section 376 pattern.

## s376 — L3 flag

- failed: 7
- reason: The encoding omits structured caning punishment facts that the canonical statute includes, including mandatory caning of at least 12 strokes under subsection (4) and caning as an alternative sanction under subsection (3).
- suggested fix: Encode the subsection (3) and subsection (4) caning consequences explicitly rather than only mentioning them in supplementary text.

## s376F — L3 flag

- failed: 8
- reason: The encoding introduces a spouse/not-spouse `any_of` branch in subsection (1)(c) that does not appear in the canonical `act.json` text for section 376F.
- suggested fix: Re-encode subsection (1) strictly from the canonical raw text without importing the spouse, inducement, threat, or deception structure from another offence.

## s376G — L3 flag

- failed: 6
- reason: Canonical subsection (5) contains operative limbs (a) and (b) on consent, but the encoding keeps only the opening “To avoid doubt —” and drops both limbs.
- suggested fix: Encode subsection (5)(a) and (5)(b) explicitly within subsection (5) so the full statutory effect is preserved.

## s376H — L3 flag

- failed: 7
- reason: The canonical `act.json` entry only supplies the `(2)(b)` penalty and does not contain any `(2)(a)` punishment text, but the encoding adds a 10-year penetrative-touching penalty branch and a caning-related supplementary note not present in the canonical input.
- suggested fix: Remove the fabricated `(2)(a)` penalty content or regenerate this section from a canonical source that actually includes the missing punishment limb before re-review.

## s377 — L3 flag

- failed: 7
- reason: Subsection (3) states only that the offender is liable to fine or to caning, but the encoding adds `caning := 0 .. 24 strokes`, which fabricates a caning quantum not found in the canonical text.
- suggested fix: Remove the invented numeric caning clause and preserve the caning limb only in explicitly labelled supplementary text or another non-fabricating refinement.

## s377BB — L3 flag

- failed: 6, 7
- reason: Canonical subsections (2) to (5) contain substantive offence text but are empty in `statute.yh`, and subsections (7) and (8) fabricate `caning := 0 .. 24 strokes` even though the statute states only liability to caning with no numeric quantum.
- suggested fix: Populate subsections (2) to (5) from the canonical text and preserve the caning limbs verbatim in supplementary text instead of inventing a stroke range.

## s377BD — L3 flag

- failed: 7
- reason: Subsection (3) states the offender is also liable to fine or to caning, but the encoding only models imprisonment and leaves fine/caning as unstructured supplementary text.
- suggested fix: Encode subsection (3) with an explicit cumulative imprisonment block plus a separate fine/caning liability block, following the pattern used in nearby section 377BB(8).

## s377BG — L3 flag

- failed: 7
- reason: The subsection (2) penalty encoding invents non-statutory `fine_liability` and `caning_liability` conditions even though the statute only provides imprisonment plus discretionary liability to fine or to caning.
- suggested fix: Re-encode subsection (2) without invented `when` conditions, preserving imprisonment plus discretionary fine-or-caning exactly as stated.

## s377D — L3 flag

- failed: 8, 9
- reason: Subsection (3) is not faithfully encoded because the logic adds an extra conjunct and rewrites limb (a) with incorrect statutory references, and the section also claims `effective 1872-01-01` even though s377D was introduced later by Act 15 of 2019.
- suggested fix: Re-encode subsection (3) from the canonical text verbatim and remove the original-Act effective date so only later commencement dates remain.

## s409 — L3 flag

- failed: 6
- reason: Subsection (2) in `statute.yh` adds director/officer definition detail and changes the partnership citation beyond what appears in the canonical `library/penal_code/_raw/act.json` entry, so the subsection is not a faithful encoding of the review source.
- suggested fix: Rewrite subsection (2) to match the canonical `act.json` text exactly and avoid injecting definition detail not present in that source.

## s512 — L3 flag

- failed: 7
- reason: Subsection (1) is encoded as `penalty cumulative` with `fine := unlimited`, which turns the statute's discretionary additional liability to "fine or to caning" into a mandatory fine and does not faithfully preserve the penalty structure.
- suggested fix: Model subsection (1) as imprisonment plus a separate discretionary `fine or caning` penalty construct, without inventing a mandatory unlimited fine.

