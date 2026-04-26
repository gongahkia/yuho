# Phase D L3 — flagged sections for human review

_Aggregated from per-section `_L3_FLAG.md` files. Regenerate by re-running `l3_audit.py`._

## s26C — L3 flag

- failed: 8
- reason: Canonical subsection (2) contains two disjunctive limbs, `(2)(a)` and `(2)(b)`, but the encoding stops after the em dash and does not represent either branch.
- suggested fix: Preserve subsection (2)(a) and (2)(b) as explicit alternative branches under subsection (2), with the canonical text verbatim.

## s26D — L3 flag

- failed: 9
- reason: The encoding omits the earlier commencement date for material tagged `[15/2019]` and only records `effective 2020-02-10`, so the effective-date history is incomplete.
- suggested fix: Add the missing amendment commencement date (likely `2019-12-31`) alongside `2020-02-10` after confirming it against the section’s amendment history.

## s29B — L3 flag

- failed: 9
- reason: The encoding uses only `effective 1872-01-01`, but section 29B was introduced later, with external legislative history indicating Act 51 of 2007 commenced on 1 February 2008.
- suggested fix: Add the later commencement date as an `effective` clause after confirming the source amendment metadata for section 29B.

## s38 — L3 flag

- failed: 8
- reason: The operative rule in the canonical text is flattened into two standalone definitions, so the section’s conjunctive "Where ..., they may ..." proposition is not actually encoded as a rule.
- suggested fix: Encode the main clause as a structured rule or elements block that preserves the conditional relationship, while keeping the illustration unchanged.

## s40 — L3 flag

- failed: 6, 9
- reason: Subsection (2) is not faithfully preserved because the encoded statutory text appends the non-canonical amendment marker "[15/2019; 2/2020]", and the section’s effective clauses do not cleanly reflect the `[15/2019; 2/2020]` amendment history.
- suggested fix: Remove amendment markers from the quoted subsection text and encode the amendment chronology only in metadata/effective clauses.

## s53 — L3 flag

- failed: 4
- reason: The canonical explanation ("Explanation. —Caning shall be with a rattan.") is retained only as a bare definition string rather than as an explicit explanation/refinement form.
- suggested fix: Re-encode the explanation as a labelled `/// Explanation` comment or another explicit explanation/refinement construct without changing the statute text.

## s74E — L3 flag

- failed: 6
- reason: Canonical subsection (2) contains operative limbs (a) and (b), but the encoding preserves only the introductory phrase and omits both substantive rules.
- suggested fix: Encode subsection (2)(a) and (2)(b) as structured content under `subsection (2)` so the statutory rule is fully preserved.

## s76 — L3 flag

- failed: 9
- reason: The encoding includes amendment marker `[15/2019]` but only declares `effective 1872-01-01`, so it omits a later effective date required by the checklist.
- suggested fix: Add the correct post-amendment effective date for the `[15/2019]` revision as an `effective` clause in `statute.yh`.

## s78 — L3 flag

- failed: 8
- reason: The encoding treats the “notwithstanding the court may have had no jurisdiction” clause as a required conjunctive circumstance, even though the canonical text makes it a non-limiting proposition.
- suggested fix: Remove that clause from the mandatory `all_of` conditions and preserve it only as a non-required qualification while keeping the good-faith jurisdiction belief as the operative condition.

## s80 — L3 flag

- failed: 6
- reason: Subsection (2) is not faithfully preserved because the encoding drops items (a) and (b) and the sentence requiring the prosecution to prove the fault element.
- suggested fix: Re-encode subsection (2) so both conjunctive limbs and the prosecution-proof requirement are explicitly represented within the subsection block.

## s84 — L3 flag

- failed: 6, 8
- reason: Subsection (2) is reduced to a truncated definition string and omits the canonical (2)(a) and (2)(b) limbs, so the statute's required conjunctive structure is not faithfully encoded.
- suggested fix: Encode subsection (2) as operative structure that captures both (2)(a) and (2)(b) as cumulative conditions instead of leaving only the introductory clause.

## s90 — L3 flag

- failed: 8
- reason: The encoding flattens the section into quoted definition strings and does not represent the operative disjunctive limbs in canonical paragraphs (a)(i), (a)(ii), (b), and (c), so the English connective structure is not faithfully encoded.
- suggested fix: Re-encode section 90 with explicit nested logical branches for paragraph (a) and the alternative limbs in paragraphs (b) and (c) instead of storing them as freeform definitions.

## s94 — L3 flag

- failed: 4
- reason: The two canonical explanations are not preserved as explanations or structured refinements, and the encoding adds a substantive self-placement condition not present in the canonical `text` or `sub_items`.
- suggested fix: Preserve Explanation 1 and Explanation 2 explicitly in explanatory form and remove unsupported substantive conditions unless they appear in the canonical source.

## s96 — L3 flag

- failed: 5
- reason: The encoding fabricates an `exception private_defence` block even though the canonical section is a single operative sentence with no canonical exceptions or sub-items.
- suggested fix: Re-encode section 96 as a direct faithful rule without introducing a non-canonical exception structure.

## s97 — L3 flag

- failed: 9
- reason: The encoding is tagged with amendment marker `[15/2019]` but the statute header only has `effective 1872-01-01`, so the post-2019 amendment date is missing.
- suggested fix: Add the 2019 amendment effective date used for the surrounding private-defence sections instead of leaving section 97 with only the original 1872 date.

## s99 — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while Act 15 of 2019 entered into force on 2020-01-01, so the effective-date encoding is not sane.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.

## s105 — L3 flag

- failed: 6, 8
- reason: The encoding drops canonical limbs `(b)(i)`, `(b)(ii)`, and `(2)(a)` to `(2)(f)`, collapsing subsection `(2)` into a definition string and failing to preserve the statute's disjunctive structure.
- suggested fix: Re-encode subsection `(1)(b)` and subsection `(2)` with explicit nested items or `any_of` branches so every canonical limb is represented verbatim.

## s106 — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.

## s108B — L3 flag

- failed: 9
- reason: The encoding uses only `effective 1872-01-01`, but section 108B was introduced by Act 51 of 2007, which commenced on 2008-02-01, so the effective-date encoding is not sane.
- suggested fix: Replace or supplement the generic commencement with an `effective 2008-02-01` clause after confirming the section’s amendment history.

## s113 — L3 flag

- failed: 7
- reason: The canonical text is a liability attribution rule and does not itself prescribe a standalone punishment clause, but the encoding adds a `penalty {}` block.
- suggested fix: Move the "liable for the effect caused" language out of `penalty {}` into a non-penalty liability/refinement construct while preserving the illustration verbatim.

## s115 — L3 flag

- failed: 8
- reason: The statute’s disjunctive penalty phrase "liable to fine or to caning" is not fully captured structurally because the encoding machine-encodes only `fine := unlimited` and leaves caning only in supplementary text.
- suggested fix: Encode the additional liability as a disjunctive penalty structure that preserves both fine and caning as separate machine-readable alternatives.

## s121B — L3 flag

- failed: 9
- reason: The encoded statute uses `effective 2020-01-01` for a section marked `[15/2019]`, and I could not verify that as the correct amendment commencement date for section 121B.
- suggested fix: Verify the actual commencement date for the Act 15 of 2019 amendment affecting section 121B and replace the current `effective` date if needed.

## s124 — L3 flag

- failed: 7, 9
- reason: The encoding does not machine-encode the statute's express life-imprisonment alternative and the later `effective 2019-12-31` date is not reliable enough to certify for a section marked `[15/2019]`.
- suggested fix: Encode life imprisonment as an explicit penalty branch and confirm the correct commencement date for the `[15/2019]` amendment before restamping.

## s130 — L3 flag

- failed: 7
- reason: The penalty encoding omits life imprisonment as an actual encoded penalty branch and makes fine unconditional even though the statute allows fine only if the offender is not sentenced to imprisonment for life.
- suggested fix: Encode the life-imprisonment alternative structurally and make the fine apply only on the non-life-imprisonment branch.

## s130A — L3 flag

- failed: 9
- reason: The encoding uses only `effective 1872-01-01`, but section 130A appears to have been introduced later and external consolidation history shows `[51/2007]`.
- suggested fix: Add an effective date reflecting the amending Act that introduced section 130A, then re-run L3 review.

## s130B — L3 flag

- failed: 9
- reason: Section 130B is a later inserted section number, but the encoding uses only `effective 1872-01-01`, so the effective date is not sane on the present record.
- suggested fix: Verify the insertion commencement date from Singapore Statutes Online legislative history and add that later effective date before stamping.

## s130C — L3 flag

- failed: 9
- reason: The encoding uses only `effective 1872-01-01`, but section 130C is a later inserted provision and therefore needs an amending-act effective date rather than the generic base date alone.
- suggested fix: Add an effective date for the amendment that introduced section 130C, then re-run L3 review.

## s130E — L3 flag

- failed: 7
- reason: The canonical limb `(b)` authorises imprisonment for life or up to 20 years, but the encoding’s operative penalty only models `imprisonment := 0 years .. 20 years` and leaves life imprisonment only in supplementary text.
- suggested fix: Encode the limb `(b)` punishment so the executable penalty model expressly captures the life-imprisonment alternative as well as the term sentence.

## s132 — L3 flag

- failed: 7
- reason: The encoding does not machine-encode the statute's express life-imprisonment alternative, leaving it only in `supplementary` text, so the penalty facts are incomplete.
- suggested fix: Add an explicit life-imprisonment penalty branch or field alongside death and the term-imprisonment branch, while keeping the existing conditional fine logic.

## s137 — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent treats Act 15 of 2019 commencement as `2020-01-01`, so the effective-date encoding is not sane.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.

## s139 — L3 flag

- failed: 8
- reason: The canonical section is a single conditional saving rule, but the encoding reduces it to three definitions and does not preserve the statute's operative logical structure.
- suggested fix: Re-encode the section as an explicit conditional rule that captures the "where ... no person ... shall be subject" logic rather than as standalone definitions.

## s148 — L3 flag

- failed: 3
- reason: The canonical section includes an Illustration heading with a preserved cross-reference note, but the encoding keeps that text only in comments instead of as a separate `illustration` block.
- suggested fix: Replace the comment-only preservation with an explicit `illustration` block containing the canonical text verbatim.

## s154 — L3 flag

- failed: 8
- reason: The encoding collapses the prevention and dispersal/suppression omission limbs into one clause and drops the second canonical "do not", changing the section's conjunctive logic.
- suggested fix: Split the omission requirements so the notice, prevention, and dispersal/suppression failures are each preserved with the same negated conjunctions as the canonical text.

## s155 — L3 flag

- failed: 8
- reason: The encoding decouples who had reason to believe from who failed to use lawful means, which broadens the statutory logic in a way the English text does not clearly permit.
- suggested fix: Model the person and the agent-or-manager as correlated alternative branches so each branch carries both the foresight and failure-to-act condition together.

## s157 — L3 flag

- failed: 9
- reason: The encoded statute uses `effective 2019-12-31` for a provision marked `[15/2019]`, and I could not certify that as the correct commencement date for the section.
- suggested fix: Confirm the actual commencement date for the section 157 amendment under Act 15 of 2019 and replace the unsupported effective date before restamping.

## s158 — L3 flag

- failed: 7
- reason: The `base_offence` condition is broad enough that an armed offender also satisfies it, so the encoding can trigger both the 2-year and 5-year penalty branches even though section 158 states alternative punishments for separate limbs.
- suggested fix: Make the penalty triggers mutually exclusive by separating the ordinary limb from the armed limb at the element or condition level.

## s166 — L3 flag

- failed: 9
- reason: The section is tagged `[Act 25 of 2021 wef 01/04/2022]` but the statute header encodes only `effective 1872-01-01`, so the later operative date is missing.
- suggested fix: Add `effective 2022-04-01` to the statute header while preserving the original `effective 1872-01-01`.

## s172 — L3 flag

- failed: 7, 8
- reason: The encoding makes every case depend on `ordinary_process` or `court_process`, so absconding to avoid arrest on a warrant is not faithfully preserved as a standalone route to the base penalty.
- suggested fix: Model warrant-avoidance separately from summons/notice/order service, and apply the enhanced branch only where the summons, notice or order is for court attendance or production.

## s175 — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.

## s179 — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses only `effective 1872-01-01`, so the effective-date encoding is not sane.
- suggested fix: Add the verified commencement date for the `[15/2019]` amendment as an additional `effective` clause before restamping.

## s183 — L3 flag

- failed: 9
- reason: The encoded section is tagged with amendment `[15/2019]` but lists only `effective 1872-01-01`, so it omits a later amendment effective date required by the checklist.
- suggested fix: Add the applicable later effective date for the 2019 amendment to the statute header, consistent with the canonical amendment history and nearby amended sections.

## s185 — L3 flag

- failed: 8
- reason: The encoding factors the offence into `purchase_or_bid` plus an alternative mens rea block, which incorrectly makes a purchase without intent to perform punishable even though the canonical second limb applies only to a bid.
- suggested fix: Restructure the elements as two disjunctive branches: `(purchase or bid) + knowledge of legal incapacity`, and `bid + no intention to perform`.

## s186 — L3 flag

- failed: 9
- reason: The encoding uses `effective 2019-12-31` for the `[15/2019]` amendment, but repo-local precedent for comparable Penal Code sections points to `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Confirm the actual commencement date for the Act 15 of 2019 amendment to section 186 and update the `effective` clause accordingly before restamping.

## s190 — L3 flag

- failed: 8
- reason: The `elements` split changes the statutory meaning by encoding the application as being for protection against injury to the public servant, instead of an application made to a legally empowered public servant for protection against injury.
- suggested fix: Re-encode the application/public-servant relationship so the offence matches the canonical sentence structure without changing who the protection is sought from.

## s194 — L3 flag

- failed: 7
- reason: The penalty encoding does not faithfully capture the statute because imprisonment for life is only mentioned in supplementary text and the aggravated death-eligible branch is encoded broadly enough to cover fabrication as well as giving false evidence.
- suggested fix: Model the base punishment as life imprisonment or up to 20 years with fine only on the non-life branch, and scope the aggravated branch to the person who gives such false evidence.

## s204 — L3 flag

- failed: 8
- reason: The encoding rewrites the canonical sentence into `all_of` plus two `any_of` groups in a way that appears to make the prevention intent mandatory and treat lawful summons as a sibling alternative circumstance, which is not clearly faithful to the statute's original connective structure.
- suggested fix: Re-encode the operative clause more literally, preserving the placement of the final `or after he has been lawfully summoned or required...` limb before seeking L3 stamp.

## s204B — L3 flag

- failed: 9
- reason: The encoding uses only `effective 1872-01-01` for a lettered section `204B`, so the effective-date sanity check cannot be certified without confirming the later insertion date from source history.
- suggested fix: Confirm the actual commencement date for section 204B from SSO or legislative history and add it as an `effective` clause if the section was introduced later.

## s207 — L3 flag

- failed: 8
- reason: The encoding places `deceptive_practice` inside the same `all_of` bundle as `no_right_or_rightful_claim`, but the statute reads as a disjunctive branch where that knowledge qualifier attaches to accepting/receiving/claiming property, not necessarily to practising deception.
- suggested fix: Restructure the elements so the act branches track the statute’s syntax, with the knowledge qualifier scoped only to the acceptance/receipt/claim branch and the common seizure-prevention intent applied to both branches.

## s211 — L3 flag

- failed: 7, 8
- reason: The encoding makes the serious-charge qualifier a required `elements` branch and fabricates a mutually exclusive `ordinary_false_charge` condition, instead of modeling the statute's base offence with an aggravated penalty condition.
- suggested fix: Keep the offence elements to the canonical charging conduct and knowledge/intent only, then express the 2-year base penalty and the 7-year serious-charge branch as faithful sibling penalty conditions.

## s217 — L3 flag

- failed: 8
- reason: The `.yh` uses an `all_of` structure in the person-saving limb that turns “save any person from legal punishment, or subject him to a lesser punishment” into a required sibling element instead of preserving the statute’s disjunctive object of the intent/knowledge clause.
- suggested fix: Re-encode the person-facing limb so the “save from legal punishment” and “subject to a lesser punishment” alternatives remain within the same disjunctive intent/knowledge branch.

## s222 — L3 flag

- failed: 7
- reason: The first penalty branch does not faithfully capture the statute because imprisonment for life is only preserved in supplementary text rather than in the operative penalty encoding.
- suggested fix: Re-encode limb (a) so the life-imprisonment alternative is represented explicitly rather than only described in supplementary prose.

## s259 — L3 flag

- failed: 7, 8
- reason: The canonical penalty is cumulative ("shall be punished with imprisonment ... and shall also be liable to fine"), but the encoding uses `penalty or_both`, which incorrectly makes imprisonment optional.
- suggested fix: Replace the `penalty or_both` structure with a cumulative/default penalty form that preserves mandatory imprisonment plus liability to an unlimited fine.

## s267B — L3 flag

- failed: 9
- reason: The encoding uses only `effective 1872-01-01`, but section 267B is an inserted later section and I could not verify a sane later commencement date from the local sources.
- suggested fix: Confirm the actual insertion commencement date from Singapore Statutes Online legislative history and add it as an `effective` clause before restamping.

## s287 — L3 flag

- failed: 7
- reason: The encoding drops the four conditional punishment limbs in canonical subsection (3) and incorrectly states that the raw text stops at the dash.
- suggested fix: Encode subsection (3)(a) to (d) as conditional penalty branches with the correct imprisonment and fine consequences, including the $5,000 fine cap only for subsection (1)(a) or (b).

## s292A — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent treats Act 15 of 2019 commencement as `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Verify the commencement date for section 292A under Act 15 of 2019 and replace the later `effective` clause with the confirmed date before restamping.

## s294 — L3 flag

- failed: 9
- reason: The statute is tagged with amendment marker `[15/2019]` but the encoding uses only `effective 1872-01-01`, which fails the amended-section effective-date requirement.
- suggested fix: Add the amendment commencement date as an `effective` clause alongside any historical baseline date if the section remained in force through amendment.

## s301 — L3 flag

- failed: 9
- reason: The section is marked `[15/2019]` but the encoding uses `effective 2019-12-31`, while the Criminal Law Reform Act 2019 (Act 15 of 2019) entered into force on 2020-01-01, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later `effective` clause with the verified commencement date `2020-01-01`, then rerun L3 review.

## s304B — L3 flag

- failed: 6, 7
- reason: The encoding leaves subsection (2) empty even though the canonical statute contains definitional content there, and its penalty encodes fine but omits the statute's separate caning liability.
- suggested fix: Populate subsection (2) with the canonical definitions and add the missing caning branch to the cumulative penalty structure without changing the source text.

## s308 — L3 flag

- failed: 7
- reason: The `hurt_caused` penalty branch omits a structured caning punishment even though the canonical text expressly provides imprisonment, fine, caning, or any combination of those punishments.
- suggested fix: Add the missing `caning :=` punishment to the aggravated `when hurt_caused` penalty branch so every canonical punishment option is encoded.

## s308A — L3 flag

- failed: 8
- reason: Subsection (1)(b) is not faithfully encoded because the canonical disjunction between items (b)(i) and (b)(ii) is replaced by the truncated placeholder `paragraph_b_truncated := "Knowing that —"` and the two alternatives are omitted.
- suggested fix: Encode subsection (1) so paragraph (b) contains an explicit `any_of` that preserves both canonical alternatives in items (b)(i) and (b)(ii).

## s311 — L3 flag

- failed: 9
- reason: The section carries amendment markers `[15/2019]` and `[Act 23 of 2021 wef 01/03/2022]` but the encoding uses only `effective 1872-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Add later `effective` clauses for the post-1872 amendments, including `2022-03-01` and the verified commencement date for Act 15 of 2019, then rerun L3 review.

## s312 — L3 flag

- failed: 7, 8
- reason: The encoding invents a `pregnancy_not_more_than_16_weeks` condition and makes pregnancy duration an element-level `any_of`, but the statute states a base offence with a higher penalty only if the pregnancy exceeds 16 weeks.
- suggested fix: Keep the miscarriage elements unconditional and model the `more than 16 weeks` language only as an aggravated penalty branch, with the base penalty as the default.

## s314 — L3 flag

- failed: 7
- reason: The encoding does not faithfully capture the no-consent penalty alternative because it omits an explicit life-imprisonment branch and invents a separate `woman_without_consent_non_life_sentence` condition.
- suggested fix: Encode the no-consent punishment as explicit alternatives of imprisonment for life or the above-mentioned imprisonment-plus-fine punishment using the canonical condition only.

## s323A — L3 flag

- failed: 9
- reason: The section is marked `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later `effective` clause with the verified commencement date `2020-01-01`, then rerun L3 review.

## s324 — L3 flag

- failed: 7
- reason: The encoding fabricates a caning range of `0 .. 24 strokes` even though the canonical text states only liability to caning without any numeric stroke count.
- suggested fix: Preserve the caning limb without inventing a stroke count, such as by moving the verbatim caning language into a supplementary penalty field.

## s326 — L3 flag

- failed: 7
- reason: The encoding does not faithfully capture the punishment because it omits an explicit life-imprisonment branch and invents a separate `non_life_sentence` condition for fine liability.
- suggested fix: Encode the penalty as the canonical alternatives and conditional fine consequence without introducing a non-canonical condition.

## s327 — L3 flag

- failed: 7
- reason: The encoding fabricates a caning range of `0 .. 24 strokes` even though the canonical text only says the offender is liable "to caning" without specifying any stroke count.
- suggested fix: Remove the invented numeric caning clause and preserve the caning limb only in an explicitly labelled textual refinement or supplementary punishment text that does not add a number.

## s328 — L3 flag

- failed: 7
- reason: The encoding hard-codes `caning := 0 .. 24 strokes` even though the canonical text only says the offender is liable to caning without specifying any stroke count.
- suggested fix: Preserve the caning limb without inventing a numeric range, consistent with the repo's handling of uncapped caning provisions.

## s329 — L3 flag

- failed: 7
- reason: The encoding hard-codes `caning := 0 .. 24 strokes` even though the canonical text only says the offender is liable to caning without specifying any stroke count.
- suggested fix: Preserve the caning limb without inventing a numeric range, consistent with the repo's handling of uncapped caning provisions.

## s330 — L3 flag

- failed: 7
- reason: The penalty encoding is not faithful because it makes `fine` part of a cumulative penalty and omits a structured `caning` branch, even though the canonical text says the offender is liable to fine or to caning.
- suggested fix: Model the punishment like the comparable hurt/grievous-hurt extortion sections, with imprisonment plus an alternative branch for `fine` or `caning`.

## s331 — L3 flag

- failed: 7
- reason: The encoding omits a structured caning punishment even though the canonical text expressly makes the offender liable to caning in addition to imprisonment and fine.
- suggested fix: Add an explicit caning limb, using `caning := unspecified;` if needed, so every canonical punishment option is encoded without inventing a stroke count.

## s332 — L3 flag

- failed: 7
- reason: The encoding omits a structured caning punishment even though the canonical text expressly makes the offender liable to fine or to caning, and the grammar now supports `caning := unspecified` for that case.
- suggested fix: Replace the prose-only preservation of the caning limb with an explicit structured caning branch so every canonical punishment option is encoded without inventing a stroke count.

## s333 — L3 flag

- failed: 7
- reason: The canonical punishment includes liability to fine or to caning, but the encoding only models `fine := unlimited` and omits any `caning :=` clause.
- suggested fix: Add an explicit caning branch to the penalty block so the encoded punishment captures both alternatives stated in the statute.

## s334 — L3 flag

- failed: 9
- reason: The section carries amendment marker `[15/2019]` but the encoding uses `effective 2019-12-31`, while the Criminal Law Reform Act 2019 commenced on `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later effective date with `2020-01-01` and re-run L3 review.

## s334A — L3 flag

- failed: 9
- reason: The section is marked `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent treats Act 15 of 2019 commencement as `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later `effective` clause with `2020-01-01`, then rerun L3 review.

## s342 — L3 flag

- failed: 9
- reason: The encoding is tagged with amendment marker `[15/2019]` but uses `effective 2019-12-31`, while Act 15 of 2019 commenced on 2020-01-01.
- suggested fix: Replace the later effective date with `2020-01-01` and keep the original `1872-01-01` commencement clause.

## s363A — L3 flag

- failed: 7, 8
- reason: The encoding omits a structured caning punishment even though the canonical text expressly includes caning, and `penalty or_both` does not faithfully capture a three-way “fine, or caning, or any combination” punishment clause.
- suggested fix: Add an explicit caning limb without inventing a stroke count and re-express the penalty logic so all three punishment options and their combinations are structurally captured.

## s365 — L3 flag

- failed: 7
- reason: The encoding fabricates `caning := 0 .. 24 strokes` even though the canonical text states only that the offender is liable "to caning" without any numeric stroke count.
- suggested fix: Remove the invented stroke range and preserve the caning limb without adding a number of strokes.

## s366 — L3 flag

- failed: 7
- reason: The encoding fabricates `caning := 0 .. 24 strokes` even though the canonical text only makes the offender liable to caning without specifying any numeric stroke count.
- suggested fix: Preserve the caning limb without inventing a number of strokes, and keep the imprisonment-plus-fine-or-caning structure faithful to the statute.

## s367 — L3 flag

- failed: 9
- reason: The section is marked `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the amendment effective date with the correct commencement date for Act 15 of 2019, then re-run L3 review.

## s368 — L3 flag

- failed: 8
- reason: The encoding uses top-level `all_of` with freeform strings for "kidnapped or abducted" and "conceals or keeps such person in confinement" instead of preserving those disjunctive alternatives as structured `any_of` branches.
- suggested fix: Split the knowledge and actus reus limbs into explicit `any_of` alternatives while keeping the overall offence conjunctive.

## s376AA — L3 flag

- failed: 6
- reason: Canonical subsection (2) contains operative consent-related text, but the encoded `subsection (2)` block is empty and therefore does not faithfully preserve the statute.
- suggested fix: Encode subsection (2)(a) and (2)(b) explicitly within `subsection (2)` using the same structured preservation standard as the neighboring Penal Code sections.

## s376C — L3 flag

- failed: 9
- reason: The encoded statute uses `effective 2020-01-01` even though comparable Penal Code sections introduced by the same `[15/2019]` amendment in this codebase use `2019-12-31`, so the amendment effective date is not sane enough to stamp.
- suggested fix: Verify the commencement date for Act 15 of 2019 for section 376C and update the `effective` clause to the correct date before rerunning L3 review.

## s376E — L3 flag

- failed: 7, 8
- reason: The encoding omits subsection (1)(b)(i)-(iii), subsection (2)(a)-(c), and the subsection (4) conditional punishment branches, so the statute's operative conjunctive conditions and `or with both` penalty structure are not faithfully represented.
- suggested fix: Encode the missing sub-items explicitly and represent subsection (4) with both age-based penalty branches, including imprisonment, fine, and `or_both`.

## s376EA — L3 flag

- failed: 6, 8
- reason: The encoding truncates subsection (1) after paragraph (b)'s opening words and collapses subsection (2) without preserving the operative paragraph structure and English conjunctions in the canonical text.
- suggested fix: Restore subsection (1)(b)(i)-(iv) and subsection (2)(a)-(c) as structured Yuho elements with the correct conjunctive/disjunctive logic.

## s376EB — L3 flag

- failed: 6, 7
- reason: Subsections (2) and (3) are not faithfully preserved because the encoded file keeps only opening text and omits subsection (2)(a)-(b) plus both conditional penalty limbs in subsection (3)(a)-(b).
- suggested fix: Encode subsection (2)(a)-(b) explicitly and represent subsection (3) with both conditional penalty branches, preserving the original conditions and "or with both" structure.

## s376EE — L3 flag

- failed: 6, 9
- reason: Subsection (2) is left empty and subsection (1) omits canonical sub-paragraphs (c)(i) to (c)(iii), and the section uses `effective 2019-12-31` for `[15/2019]` where repo-local L3 precedent treats the Act 15 of 2019 commencement as `2020-01-01`.
- suggested fix: Encode all canonical subsection content, including subsection (2) and paragraph (c)(i)-(iii), and verify the Act 15 of 2019 commencement date before rerunning L3 review.

## s377B — L3 flag

- failed: 6, 7, 9
- reason: The encoding leaves canonical subsection (3) empty, fabricates a `0 .. 24 strokes` caning cap for subsection (4) where the statute states only that the offender is liable to caning, and uses only `effective 1872-01-01` even though section 377B was introduced by Act 51 of 2007 with commencement on 1 February 2008.
- suggested fix: Populate subsection (3) verbatim from the canonical text, change subsection (4) caning to an unspecified liability form, and add the 2008 commencement date to the section’s effective clauses.

## s377BC — L3 flag

- failed: 6, 7, 8
- reason: Canonical subsection (2) is missing from the encoding, and subsections (3) and (4) omit or mis-encode the caning and alternative/cumulative penalty structure stated in the statute.
- suggested fix: Encode subsection (2) verbatim from `sub_items`, add the missing caning liability, and model subsection (4) as imprisonment plus alternative fine-or-caning rather than a single imprisonment-plus-fine block.

## s377BF — L3 flag

- failed: 7
- reason: Subsection (4) says the offender "shall also be liable to fine or to caning", but the encoding only models fine structurally and leaves caning as supplementary prose.
- suggested fix: Replace the freeform supplementary sentence in subsection (4) with a structured penalty branch that explicitly encodes caning as an alternative to fine.

## s377BH — L3 flag

- failed: 6, 7
- reason: Subsection (3)'s canonical itemised production methods in (a)-(c) are omitted, and subsection (2)'s penalty omits the statute's express caning alternative.
- suggested fix: Encode subsection (3)(a)-(c) explicitly and represent subsection (2) as mandatory imprisonment plus the disjunctive fine-or-caning liability without inventing any further caning details.

## s377BI — L3 flag

- failed: 7
- reason: Subsection (2) says imprisonment plus liability to fine or to caning, but the encoding models only the fine branch structurally and leaves the caning branch in supplementary text.
- suggested fix: Add a separate caning-liability penalty branch, as used in nearby section encodings, without inventing any stroke count.

## s377BJ — L3 flag

- failed: 7
- reason: The canonical punishment makes the offender liable to fine or to caning, but the encoding only structures the fine limb and leaves caning in prose instead of an explicit punishment clause.
- suggested fix: Add an explicit caning branch, using `caning := unspecified` if needed, so every canonical punishment option is encoded without inventing a stroke count.

## s377BK — L3 flag

- failed: 6
- reason: The encoding includes subsection (3) as a shell with only an illustration, but the canonical source also contains substantive paragraph (3)(a) and (3)(b) text that is omitted.
- suggested fix: Add the omitted subsection (3)(a) and (3)(b) definitions as structured content under subsection (3) while preserving the existing illustration verbatim.

## s377C — L3 flag

- failed: 6
- reason: The encoding does not preserve the canonical subsection content because subsection (3) omits items (a) to (f)(iii) and subsection (1) leaves several definitions as incomplete stubs rather than carrying the full statutory text.
- suggested fix: Re-encode subsection (1) and subsection (3) so every canonical definition limb and paragraph in `act.json` is represented explicitly in `statute.yh`.

## s377CA — L3 flag

- failed: 6, 8
- reason: Subsection (2) omits the canonical paragraph list in `(2)(a)` to `(2)(g)`, and the operative list logic in subsections `(1)` and `(2)` is flattened into `definitions` instead of being encoded as structured conjunctive/disjunctive content.
- suggested fix: Preserve subsection `(1)`'s required factors and subsection `(2)`'s seven presumed relationships as structured content, using list logic that matches the statute’s English.

## s379A — L3 flag

- failed: 6, 9
- reason: Subsection (3) is reduced to a comment instead of preserving the canonical definitions of “component part” and “motor vehicle”, and the encoding uses only `effective 1872-01-01` even though this section has later amendment provenance.
- suggested fix: Encode subsection (3) with the two statutory definitions and add the later effective date(s) for section 379A before re-running L3 review.

## s385 — L3 flag

- failed: 7
- reason: The canonical text expressly requires caning, but the encoding preserves that punishment only in `supplementary` prose instead of as a structured `caning` penalty fact.
- suggested fix: Replace the prose-only caning sentence with an explicit caning punishment entry, using an unspecified form if the statute gives no stroke count.

## s387 — L3 flag

- failed: 7
- reason: The encoding omits a structured caning punishment even though the canonical text expressly requires punishment "with caning", and the repo now supports `caning := unspecified` for non-numeric caning terms.
- suggested fix: Add an explicit `caning := unspecified` punishment entry so the mandatory caning limb is preserved structurally instead of only in supplementary prose.

## s393 — L3 flag

- failed: 7
- reason: The encoding preserves the mandatory caning limb only in `supplementary` prose even though the canonical text expressly requires punishment with caning of not less than 6 strokes.
- suggested fix: Add an explicit caning punishment entry and keep the statutory minimum-strokes language in supplementary text so the caning limb is preserved structurally without inventing a ceiling.

## s400 — L3 flag

- failed: 7
- reason: The encoded penalty omits the canonical life-imprisonment branch and adds a structured caning maximum of 24 strokes even though the statute only states not less than 6 strokes.
- suggested fix: Re-encode the punishment so the life-imprisonment alternative is explicit and the caning clause preserves only the statutory minimum unless another canonical source supplies a maximum.

## s404 — L3 flag

- failed: 8
- reason: The encoding introduces an `any_of` split between an invented `ordinary_case` and `clerk_or_servant_case`, but the canonical text states one offence with a higher imprisonment ceiling if the offender was the deceased's clerk or servant.
- suggested fix: Remove the fabricated offence-level disjunction and model the clerk-or-servant status only as the predicate for the enhanced penalty branch.

## s407 — L3 flag

- failed: 7
- reason: The penalty block makes the fine optional by nesting it under `alternative {}` even though the canonical text requires imprisonment and fine cumulatively ("and shall also be liable to fine").
- suggested fix: Encode the fine as a direct cumulative penalty alongside the imprisonment term, without an `alternative {}` wrapper.

## s410 — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.

## s414 — L3 flag

- failed: 7, 9
- reason: The encoding uses an unsound `[15/2019]` effective date (`2019-12-31` instead of repo-local `2020-01-01`) and alters subsection (2)(b) by substituting `Road Traffic Act (Cap. 276)` for the canonical `Road Traffic Act 1961`.
- suggested fix: Update the amendment effective date to the verified commencement date and restore subsection (2)(b) to the canonical Road Traffic Act wording before rerunning L3 review.

## s416A — L3 flag

- failed: 6, 8, 9
- reason: Subsections (2), (3), and (7) drop the canonical paragraph content and subsection (3)'s conjunctive structure, and the section uses `effective 2019-12-31` for `[15/2019]` despite repo-local L3 precedent treating Act 15 of 2019 commencement as `2020-01-01`.
- suggested fix: Restore the missing `(2)(a)` to `(2)(b)`, `(3)(a)` to `(3)(b)`, and `(7)(a)` to `(7)(b)` content with the correct logical structure, then correct the amendment effective date.

## s416B — L3 flag

- failed: 6
- reason: The encoding does not faithfully preserve subsection (2), omitting paragraphs (a) to (d) and the exclusion clause after "means communication through —".
- suggested fix: Re-encode subsection (2) with all paragraph items and the full exclusion text from the canonical statute.

## s420A — L3 flag

- failed: 6
- reason: The canonical entry includes subsection (1)(c) plus sub-items (c)(i) and (c)(ii), but the encoding omits them and therefore does not fully preserve subsection structure/content.
- suggested fix: Re-encode paragraph (c) and its two sub-items as part of subsection (1) without changing the canonical wording.

## s424A — L3 flag

- failed: 6
- reason: Subsection (5) is not fully preserved because the encoding omits the chapeau that its definitions apply "for the purposes of this section and section 424B", which drops a substantive cross-section scope statement.
- suggested fix: Preserve subsection (5)'s introductory scope text explicitly in the encoding so the definitions are not represented as applying only within section 424A.

## s426 — L3 flag

- failed: 9
- reason: The section is marked `[15/2019]` but the encoding uses only `effective 1872-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Add the verified post-2019 commencement date for the Act 15 of 2019 amendment as an additional `effective` clause, then rerun L3 review.

## s438 — L3 flag

- failed: 7
- reason: The encoding leaves the statute’s imprisonment-for-life alternative only in supplementary prose instead of preserving it as a structured penalty branch, so the punishment is not faithfully captured.
- suggested fix: Encode imprisonment for life as an explicit structured alternative alongside the up-to-10-years branch, while retaining the conditional unlimited fine for non-life sentences.

## s442 — L3 flag

- failed: 9
- reason: The section is marked `[15/2019]` but the encoding only has `effective 1872-01-01`, so the later amendment effective date is missing and the effective-date encoding is not sane enough to stamp.
- suggested fix: Add the applicable later effective date for the 2019 amendment to the statute header, consistent with the canonical amendment history and nearby amended sections.

## s447 — L3 flag

- failed: 7
- reason: The canonical text makes the fine discretionary up to $1,500, but the encoding fixes it at exactly `$1,500.00`, which fabricates the penalty ceiling into a mandatory amount.
- suggested fix: Change the fine encoding to a capped range that preserves "may extend to $1,500" rather than a fixed sum.

## s448 — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, which repo-local L3 precedent already treats as an unsound commencement date for Act 15 of 2019.
- suggested fix: Replace the amendment effective date with the correct Act 15 of 2019 commencement date before resubmitting for L3 review.

## s449 — L3 flag

- failed: 7, 9
- reason: The encoding does not preserve the imprisonment-for-life alternative as a structured penalty branch, and it uses `effective 2019-12-31` for a section tagged `[15/2019]`, which is not a reliable commencement date for that amendment.
- suggested fix: Encode imprisonment for life as an explicit alternative penalty branch and replace the amendment effective date with the correct commencement date for Act 15 of 2019 before resubmitting for L3 review.

## s450 — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent treats Act 15 of 2019 commencement as `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the unsound 2019 amendment effective date with the correct commencement date used consistently for Act 15 of 2019 in this repo, then re-run L3 review.

## s453 — L3 flag

- failed: 6
- reason: Subsection (3) in the canonical text includes operative paragraphs (a) to (d), but the encoding preserves only the lead-in presumption sentence and drops all four categories.
- suggested fix: Encode subsection (3)(a) to (d) explicitly instead of reducing subsection (3) to a single definition line.

## s460 — L3 flag

- failed: 8
- reason: The encoding flattens the statute's disjunctive aggravated-act phrase ("causes or attempts to cause death or grievous hurt") into a single element instead of modeling the alternatives with `any_of`.
- suggested fix: Refine the aggravated-act limb into explicit disjunctive branches so the connective structure matches the English text.

## s468 — L3 flag

- failed: 8
- reason: The encoding uses `penalty or_both`, but the canonical text makes imprisonment and liability to fine conjunctive, not disjunctive.
- suggested fix: Replace the disjunctive penalty form with the standard conjunctive penalty encoding used for sections that say the offender "shall also be liable to fine".

## s473A — L3 flag

- failed: 9
- reason: The encoding uses only `effective 1872-01-01`, but section 473A is a later inserted provision and should include its later commencement date instead of only the original 1872 date.
- suggested fix: Confirm the insertion commencement from the Penal Code legislative history and add that date as an `effective` clause for section 473A.

## s473B — L3 flag

- failed: 8
- reason: The English in paragraph (b) requires conjunctive intent content in both `(b)(i)` and `(b)(ii)`, but the encoding stops at `mens_rea intent_clause := "Intends that —";` and omits those operative limbs entirely.
- suggested fix: Encode paragraph `(b)` so the intent element explicitly captures both `(b)(i)` and `(b)(ii)` as conjunctive requirements instead of a placeholder clause.

## s473C — L3 flag

- failed: 8
- reason: Subsection (1) encodes the `(a)` to `(f)` alternatives as opaque definition strings instead of preserving their disjunctive structure, so the English "or" logic is not represented faithfully.
- suggested fix: Refine subsection `(1)` into structured alternatives that preserve the `(a)` to `(f)` list and its disjunctive connective.

## s476 — L3 flag

- failed: 7, 8
- reason: The canonical penalty is imprisonment up to 10 years and liability to fine, but the encoding uses `penalty or_both`, which introduces an alternative fine-only branch not stated in the statute.
- suggested fix: Replace the penalty form with a cumulative or otherwise explicitly mandatory imprisonment-plus-fine encoding that matches the canonical text.

## s477A — L3 flag

- failed: 9
- reason: The encoding omits the amendment commencement date `2022-03-01` from `[Act 23 of 2021 wef 01/03/2022]`, so the effective clauses are incomplete.
- suggested fix: Add `effective 2022-03-01` to the statute header, preserving any already-valid commencement dates.

## s489A — L3 flag

- failed: 6
- reason: Subsection (2) is not faithfully preserved because the encoding drops the statutory definitions of "bank note", "coin", and "currency" and keeps only the lead-in.
- suggested fix: Encode subsection (2) with all three canonical definitions from `_raw/act.json` instead of the placeholder lead-in-only definition.

## s489B — L3 flag

- failed: 9
- reason: The section is tagged `[15/2019]`, but the encoding uses `effective 2019-12-31` and the repo contains conflicting guidance on whether Act 15 of 2019 commenced on `2019-12-31` or `2020-01-01`, so the effective-date encoding is not safe to stamp.
- suggested fix: Confirm the commencement date for Act 15 of 2019 from an authoritative source, then update the second `effective` clause and re-run L3 review.

