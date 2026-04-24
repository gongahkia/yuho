# Phase D L3 — flagged sections for human review

## s376H
- failed: 7, 8
- reason: `statute.yh` does not preserve the subsection 376H(2)(a) caning limb in the encoded penalty and reduces the English “or any combination of such punishments” to `or_both`, so the penalty logic is not faithful to the current statute.
- suggested fix: Keep the caning limb inside `statute.yh` itself as verbatim supplementary text for subsection (2)(a) and avoid using `or_both` as a stand-in for a three-punishment “any combination” clause.

## s177
- failed: 7
- reason: The canonical `act.json` entry for section `177` stops subsection `(2)` at “the person who is guilty of an offence under that subsection shall —”, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s177_furnishing_false_information/statute.yh:39) supplies subsection `(2)` imprisonment and fine branches that are not present in that designated source of record.
- suggested fix: Reconcile subsection `(2)` against a fuller canonical source or scraper fix before restamping, and remove the unverified subsection `(2)` penalty facts unless they are supported by the canonical record.

## s376ED
- failed: 7, 8
- reason: The canonical `act.json` entry for section `376ED` truncates subsection `(1)(c)` and stops subsections `(2)` and `(3)` at their opening clauses, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s376ED_sexual_activity_image_presence_minor_below/statute.yh:9) supplies detailed conjunctive limbs for subsection `(1)(c)`, a full subsection `(2)` offence, and age-tiered subsection `(3)` penalty branches that cannot be verified from that designated source of record.
- suggested fix: Repair the raw `376ED` extraction so the full subsection `(1)(c)`, `(2)`, and `(3)` text is present in `act.json`, then re-encode only the connective logic and penalty facts supported by that canonical source before restamping.

## s377BD
- failed: 7
- reason: [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s377BD_possession_gaining_access_voyeuristic/statute.yh:37) encodes subsection `(3)` only as imprisonment plus supplementary text, but the statute expressly adds further liability to fine or to caning, so the aggravated penalty is not fully preserved.
- suggested fix: Encode subsection `(3)` with explicit fine/caning liability branches, and then recheck subsection `(4)` once the raw `act.json` extraction is completed beyond its current opening words.

## s174
- failed: 7
- reason: The canonical `act.json` entry for section `174` stops subsection `(2)` at “any person who is guilty of an offence under subsection (1) shall —”, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s174_failure_attend_obedience_order_public_servant/statute.yh:35) supplies subsection `(2)` imprisonment and fine branches that are not present in that designated source of record.
- suggested fix: Reconcile subsection `(2)` against a fuller canonical source or scraper fix before restamping, and remove the unverified subsection `(2)` penalty facts unless they are supported by the canonical record.

## s267C
- failed: 8
- reason: The canonical `act.json` entry for section `267C` truncates subsection `(2)` at “This section also applies where a person —”, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s267C_uttering_words_making_document_etc/statute.yh:25) supplies a full subsection `(2)` offence structure with `all_of`/`any_of` branches that cannot be verified from that designated source of record.
- suggested fix: Repair the raw `267C` extraction so subsection `(2)` is complete in `act.json`, then re-audit the encoded subsection `(2)` elements and connective logic against that canonical text before stamping.

## s188
- failed: 7, 9
- reason: [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s188_disobedience_order_duly_promulgated_public/statute.yh:45) encodes the subsection `(2)` individual fine as `$2,500` and the other-case fine as `$20,000`, but the statute provides `$5,000` and `$10,000`, and its `[15/2019]` amendment took effect on `2020-01-01`, not `2019-12-31`.
- suggested fix: Correct the subsection `(2)` penalty caps to match section 188 and replace the amendment effective date with `2020-01-01` before restamping.

## s193
- failed: 4
- reason: [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s193_punishment_false_evidence/statute.yh:6) preserves the three canonical explanations only as `definitions`, not as explanation-labelled comments or structured refinements, so the explanatory material is not faithfully encoded in the required form.
- suggested fix: Re-encode Explanations 1 to 3 as explicit explanation-labelled comments or structured refinements while preserving their current verbatim text.

## s376G
- failed: 5
- reason: [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s376G_incest/statute.yh:50) encodes subsection `(6)` only as a `definitions` entry even though the canonical text states that certain victims of section `376AA` are "not guilty of an offence under this section", so the exclusion is not preserved as an exception-style carve-out or explicitly labelled refinement.
- suggested fix: Re-encode subsection `(6)` as an exception or other explicitly labelled exclusion, while retaining the existing subsection numbering and the subsection `(5)` “To avoid doubt —” lead-in from the canonical text.

## s187
- failed: 7
- reason: The canonical `act.json` entry for section `187` stops subsection `(2)` at “the person who is guilty of an offence under that subsection shall —”, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s187_omission_assist_public_servant_when_bound/statute.yh:37) supplies subsection `(2)` punishment branches that are not present in that designated source of record.
- suggested fix: Reconcile subsection `(2)` against a fuller canonical source or scraper fix before restamping, and remove the unverified subsection `(2)` penalty facts unless they are supported by the canonical record.

## s377BB
- failed: 7, 8
- reason: [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s377BB_voyeurism/statute.yh:40) reduces subsection `(7)`’s “or with any combination of such punishments” to `or_both`, and [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s377BB_voyeurism/statute.yh:43) and [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s377BB_voyeurism/statute.yh:56) invent a `0 .. 24 strokes` caning cap that the canonical text does not state.
- suggested fix: Preserve the subsection `(7)` penalty combination only through faithful supplementary text or a structure that can represent any combination of imprisonment, fine, and caning, and remove the unstated caning stroke counts from subsections `(7)` and `(8)`.

## s377BG
- failed: 6
- reason: The canonical `act.json` entry for section `377BG` ends subsection `(3)` at “For the purposes of subsection (1) —” with no `sub_items`, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s377BG_using_involving_child_production_child_abuse/statute.yh:42) supplies three subsection `(3)` definition clauses that cannot be verified from that designated source of record.
- suggested fix: Repair the raw `377BG` extraction so subsection `(3)` is complete in `act.json`, then re-audit or trim the subsection `(3)` definitions to only what the canonical source supports before restamping.

## s173
- failed: 7
- reason: The canonical `act.json` entry for section `173` stops subsection `(2)` at “any person who is guilty of an offence under subsection (1) shall —”, but [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s173_preventing_service_summons_etc_preventing/statute.yh:35) supplies subsection `(2)` punishment branches that are not present in that designated source of record.
- suggested fix: Reconcile subsection `(2)` against a fuller canonical source or scraper fix before restamping, and remove the unverified subsection `(2)` penalty facts unless they are supported by the canonical record.

## s377
- failed: 7
- reason: [statute.yh](/Users/gongahkia/Desktop/coding/projects/yuho/library/penal_code/s377_sexual_penetration_etc_corpse/statute.yh:39) encodes subsection `(3)` with `caning := 0 .. 24 strokes`, but the canonical section 377 text only says the offender is liable to fine or to caning and does not specify any stroke range.
- suggested fix: Remove the numeric caning range and preserve the caning limb only in the penalty structure or supplementary text unless a canonical source expressly states the stroke count.
