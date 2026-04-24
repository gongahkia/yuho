# Phase D L3 — flagged sections for human review

## s6
- failed: 8
- reason: The canonical operative sentence is a single conjunctive construction rule, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s6_definitions_this_code_understood_subject/statute.yh:8) decomposes it into five synthetic `definitions` entries, so the English connective structure is not faithfully preserved.
- suggested fix: Re-encode the main rule as one conjunctive construction rule that preserves the canonical sentence, while keeping the two illustrations as separate illustration blocks.

## s6A
- failed: 8
- reason: The canonical text is a single operative rule with embedded `except` and `unless` conditions, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s6A_definitions_apply_this_code_other_written_law/statute.yh:8) splits it into three free-standing `definitions` strings, so the connective logic is not faithfully preserved.
- suggested fix: Re-encode the section as one structured rule that keeps the exclusion for sections 24 and 25 and the express-override condition attached to the main application rule.

## s4A
- failed: 8, 9
- reason: The canonical text is a single operative deeming rule with conjunctive conditions and internal `or` branches, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s4A_offences_against_state_genocide_committed/statute.yh:8) reduces it to free-standing `definitions`, and its `effective 2019-11-01` date is inconsistent with the surrounding `[15/2019]` provisions, including the Chapter `6B` genocide section at [s130D](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s130D_genocide/statute.yh:6) encoded as effective `2020-01-01`.
- suggested fix: Re-encode the section as operative `elements` preserving the sentence logic and verify the correct commencement date for section `4A` before restamping.

## s21
- failed: 9
- reason: The canonical record includes later amendment markers `[Act 18 of 2023 wef 31/01/2024]`, `[Act 25 of 2021 wef 01/04/2022]`, `[Act 33 of 2021 wef 14/01/2022]`, and `[19/2016; 15/2019]`, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s21_public_servant/statute.yh:8) encodes only `effective 1872-01-01`.
- suggested fix: Add the relevant amendment commencement date clauses to the section’s `effective` metadata instead of relying solely on the original 1872 commencement date.

## s24
- failed: 8
- reason: The canonical section defines dishonesty through two operative limbs joined by `or`, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s24_dishonestly/statute.yh:8) rewrites the opening sentence and stores paragraphs `(a)` and `(b)` as loose `definitions` strings rather than an explicit disjunctive structure.
- suggested fix: Re-encode section 24 so the two statutory limbs are preserved verbatim as sibling `any_of` branches or an equivalent structured disjunction.
