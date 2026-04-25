# L3 flags — failed check -123 sections in this group.---### s40 — “Offence”

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: Subsection (2) is not faithfully preserved because the encoded statutory text appends the non-canonical amendment marker "[15/2019; 2/2020]", and the section’s effective clauses do not cleanly reflect the `[15/2019; 2/2020]` amendment history.
- suggested fix: Remove amendment markers from the quoted subsection text and encode the amendment chronology only in metadata/effective clauses.

**Canonical text (first 500 chars):**

> —(1) Except in the Chapters and sections mentioned in subsections (2) and (3), “offence” denotes a thing made punishable by this Code. (2) In Chapters 4, 4A, 5 and 5A, and in sections 4, 187, 194, 195, 203, 204B, 211, 213, 214, 221, 222, 223, 224, 225, 327, 328, 329, 330, 331, 347, 348, 388 and 389, “offence” denotes a thing punishable under this Code or under any other written law for the time being in force. (3) In sections 141, 176, 177, 201, 202, 212, 216 and 441, “offence” has the same mean…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr40-#pr40-
/// @amendment [15/2019; 2/2020]

statute 40 "“Offence”" effective 1872-01-01 effective 2020-02-10 {
    subsection (1) {
        definitions {
            offence_default := "Except in the Chapters and sections mentioned in subsections (2) and (3), “offence” denotes a thing made punishable by this Code.";
        }
    }

    subsection (2) {
        definitions {
            offence_chapters_4_4A_5_5A_and_listed_sections := "In Chapters 4, 4A, 5 and 5A, and in sections 4, 187, 194, 195, 203, 204B, 211, 213, 214, 221, 222, 223, 224, 225, 327, 328, 329, 330, 331, 347, 348, 388 and 389, “offence” denotes a thing punishable under this Code or under any other written law for the time being in force. [15/2019; 2/2020]";
        }
    }

    subsection (3) {
        definitions {
            offence_sections_141_176_177_201_202_212_216_441 := "In sections 141, 176, 177, 201, 202, 212, 216 and 441, “offence” has the same meaning when the thing punishable under any other law for the time being in force is punishable under such law with imprisonment for a term of
```

---

### s84 — Act of person of unsound mind

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: Subsection (2) is reduced to a truncated definition string and omits the canonical (2)(a) and (2)(b) limbs, so the statute's required conjunctive structure is not faithfully encoded.
- suggested fix: Encode subsection (2) as operative structure that captures both (2)(a) and (2)(b) as cumulative conditions instead of leaving only the introductory clause.

**Canonical text (first 500 chars):**

> —(1) Nothing is an offence which is done by a person who, at the time of doing it, by reason of unsoundness of mind, is — ( a ) incapable of knowing the nature of the act; ( b ) incapable of knowing that what he is doing is wrong; or ( c ) completely deprived of any power to control his actions. (2) Subsection (1)( b ) applies only if the person is incapable of knowing that his act —

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr84-#pr84-
/// @amendment [Act 23 of 2021 wef 01/03/2022]
/// @amendment [15/2019]

statute 84 "Act of person of unsound mind" effective 1872-01-01 effective 2019-12-31 effective 2022-03-01 {
    subsection (1) {
        definitions {
            no_offence_rule := "Nothing is an offence which is done by a person who, at the time of doing it, by reason of unsoundness of mind, is incapable of knowing the nature of the act, incapable of knowing that what he is doing is wrong, or completely deprived of any power to control his actions.";
        }

        elements {
            all_of {
                actus_reus act_done := "An act is done by a person";
                circumstance unsoundness := "At the time of doing the act, the person acts by reason of unsoundness of mind";
                /// subsection (1) uses disjunctive limbs (a), (b), and (c), with limb (c) added by Act 23 of 2021.
                any_of {
                    circumstance incapable_nature := "The person is incapable of knowing the nature of the act";
                    circumstance incapabl
```

---

### s105 — When right of private defence of property extends to causing death

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding drops canonical limbs `(b)(i)`, `(b)(ii)`, and `(2)(a)` to `(2)(f)`, collapsing subsection `(2)` into a definition string and failing to preserve the statute's disjunctive structure.
- suggested fix: Re-encode subsection `(1)(b)` and subsection `(2)` with explicit nested items or `any_of` branches so every canonical limb is represented verbatim.

**Canonical text (first 500 chars):**

> —(1) The right of private defence of property extends, under the restrictions mentioned in sections 98 and 106A, to the voluntary causing of death to the wrongdoer when the defender reasonably believes that there was a danger to property (either his own or that of any other person) arising from any of the following descriptions: ( a ) robbery; ( b ) house-breaking committed after 7 p.m. and before 7 a.m. and if the wrongdoer — ( c ) mischief by fire committed on any building, tent, container or …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr105-#pr105-
/// @amendment [15/2019]

statute 105 "When right of private defence of property extends to causing death" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// subsection (1) extends the right only where the baseline right, restrictions, belief, and one listed danger-description all coexist.
            all_of {
                permission right_extends := "The right of private defence of property extends, under the restrictions mentioned in sections 98 and 106A, to the voluntary causing of death to the wrongdoer";
                circumstance reasonable_belief_of_danger := "The defender reasonably believes that there was a danger to property (either his own or that of any other person)";
                circumstance listed_description := "The danger to property arose from any of the following descriptions";
                any_of {
                    circumstance robbery := "robbery";
                    circumstance house_breaking_night := "house-breaking committed after 7 p.m. and before 7 a.m. and if th
```

---

### s124 — Assaulting President, etc., with intent to compel or restrain the exercise of any lawful power

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding does not machine-encode the statute's express life-imprisonment alternative and the later `effective 2019-12-31` date is not reliable enough to certify for a section marked `[15/2019]`.
- suggested fix: Encode life imprisonment as an explicit penalty branch and confirm the correct commencement date for the `[15/2019]` amendment before restamping.

**Canonical text (first 500 chars):**

> Whoever, with the intention of inducing or compelling the President or a Member of Parliament or the Cabinet, to exercise or refrain from exercising in any manner any of the lawful powers of the President, or such Member, assaults or wrongfully restrains, or attempts wrongfully to restrain, or overawes by means of criminal force, or the show of criminal force, or attempts so to overawe, the President or such Member, shall be punished with imprisonment for life or for a term which may extend to 2…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr124-#pr124-
/// @amendment [15/2019]

statute 124 "Assaulting President, etc., with intent to compel or restrain the exercise of any lawful power" effective 1872-01-01 effective 2019-12-31 {
    elements {
        all_of {
            mens_rea intention_to_induce_or_compel := "With the intention of inducing or compelling the President or a Member of Parliament or the Cabinet, to exercise or refrain from exercising in any manner any of the lawful powers of the President, or such Member";
            circumstance protected_person := "The President or such Member is the person against whom the conduct is directed";
            any_of {
                actus_reus assaults := "Assaults the President or such Member";
                actus_reus wrongfully_restrains := "Wrongfully restrains the President or such Member";
                actus_reus attempts_wrongfully_to_restrain := "Attempts wrongfully to restrain the President or such Member";
                actus_reus overawes_by_criminal_force := "Overawes the President or such Member by means of criminal force, or the
```

---

### s172 — Absconding to avoid arrest on warrant or service of summons, etc., proceeding from a public servant

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding makes every case depend on `ordinary_process` or `court_process`, so absconding to avoid arrest on a warrant is not faithfully preserved as a standalone route to the base penalty.
- suggested fix: Model warrant-avoidance separately from summons/notice/order service, and apply the enhanced branch only where the summons, notice or order is for court attendance or production.

**Canonical text (first 500 chars):**

> Whoever absconds in order to avoid being arrested on a warrant, or to avoid being served with a summons, a notice, or an order proceeding from any public servant, legally competent, as such public servant, to issue such warrant, summons, notice or order, shall be punished with imprisonment for a term which may extend to one month, or with fine which may extend to $1,500, or with both; or, if the summons, notice or order is to attend in person or by agent, or to produce a document or an electroni…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr172-#pr172-
/// @amendment [15/2019]
statute 172 "Absconding to avoid arrest on warrant or service of summons, etc., proceeding from a public servant" effective 1872-01-01 effective 2020-01-01 {
    elements {
        /// Section 172 requires absconding to avoid arrest on a warrant or service of process issued by a legally competent public servant.
        all_of {
            actus_reus absconding := "Absconds";
            mens_rea avoidance_purpose := "In order to avoid being arrested on a warrant, or to avoid being served with a summons, a notice, or an order";
            circumstance competent_public_servant := "The warrant, summons, notice or order proceeds from a public servant, legally competent, as such public servant, to issue such warrant, summons, notice or order";
            /// The enhanced branch applies only if the summons, notice or order is court process requiring attendance or production.
            any_of {
                circumstance ordinary_process := "The summons, notice or order is not to attend in person or by agent, or to produce a do
```

---

### s211 — False charge of offence made with intent to injure

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding makes the serious-charge qualifier a required `elements` branch and fabricates a mutually exclusive `ordinary_false_charge` condition, instead of modeling the statute's base offence with an aggravated penalty condition.
- suggested fix: Keep the offence elements to the canonical charging conduct and knowledge/intent only, then express the 2-year base penalty and the 7-year serious-charge branch as faithful sibling penalty conditions.

**Canonical text (first 500 chars):**

> Whoever, with intent to cause injury to any person, institutes or causes to be instituted any criminal proceeding against that person, or falsely charges any person with having committed an offence, knowing that there is no just or lawful ground for such proceeding or charge against that person, shall be punished with imprisonment for a term which may extend to 2 years, or with fine, or with both; and if such criminal proceeding be instituted on a false charge of an offence punishable with death…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr211-#pr211-

statute 211 "False charge of offence made with intent to injure" effective 1872-01-01 {
    elements {
        /// Section 211 requires the injury intent, one of the two charging acts, knowledge that no just or lawful ground exists, and one of the two mutually exclusive punishment-triggering charge categories.
        all_of {
            mens_rea intent_to_cause_injury := "With intent to cause injury to any person";
            any_of {
                actus_reus institutes_criminal_proceeding := "Institutes or causes to be instituted any criminal proceeding against that person";
                actus_reus falsely_charges_offence := "Falsely charges any person with having committed an offence";
            }
            mens_rea knowledge_no_just_or_lawful_ground := "Knowing that there is no just or lawful ground for such proceeding or charge against that person";
            any_of {
                circumstance ordinary_false_charge := "Such criminal proceeding is not instituted on a false charge of an offence punishable with death, or imprisonment 
```

---

### s259 — Having possession of a counterfeit Government stamp

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The canonical penalty is cumulative ("shall be punished with imprisonment ... and shall also be liable to fine"), but the encoding uses `penalty or_both`, which incorrectly makes imprisonment optional.
- suggested fix: Replace the `penalty or_both` structure with a cumulative/default penalty form that preserves mandatory imprisonment plus liability to an unlimited fine.

**Canonical text (first 500 chars):**

> Whoever has in his possession any stamp which he knows to be a counterfeit of any stamp issued by the Government for the purpose of revenue, intending to use or dispose of the same as a genuine stamp, or in order that it may be used as a genuine stamp, shall be punished with imprisonment for a term which may extend to 7 years, and shall also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr259-#pr259-

statute 259 "Having possession of a counterfeit Government stamp" effective 1872-01-01 {
    elements {
        all_of {
            actus_reus possession := "Has in his possession any stamp.";
            mens_rea knowledge := "Knows the stamp to be a counterfeit of a stamp issued by the Government for the purpose of revenue.";
            any_of {
                mens_rea intent_to_use_as_genuine := "Intending to use the stamp as a genuine stamp.";
                mens_rea intent_to_dispose_as_genuine := "Intending to dispose of the stamp as a genuine stamp.";
                mens_rea intent_that_it_may_be_used_as_genuine := "Intending that the stamp may be used as a genuine stamp.";
            }
        }
    }

    penalty or_both {
        imprisonment := 0 days .. 7 years;
        fine := unlimited;
    }
}

```

---

### s304B — Causing death of child below 14 years of age, domestic worker or vulnerable person by sustained abuse

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding leaves subsection (2) empty even though the canonical statute contains definitional content there, and its penalty encodes fine but omits the statute's separate caning liability.
- suggested fix: Populate subsection (2) with the canonical definitions and add the missing caning branch to the cumulative penalty structure without changing the source text.

**Canonical text (first 500 chars):**

> —(1) A relevant person who causes the death of any child, domestic worker or vulnerable person by sustained abuse shall be punished with imprisonment for a term which may extend to 20 years, and shall also be liable to fine or to caning. (2) In this section —

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr304B-#pr304B-
/// @amendment [15/2019]
statute 304B "Causing death of child below 14 years of age, domestic worker or vulnerable person by sustained abuse" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// Subsection (1) requires the offender to be a relevant person, the deceased to fall within the protected classes, and the death to be caused by sustained abuse.
            all_of {
                circumstance relevant_person := "The offender is a relevant person";
                actus_reus causes_death := "Causes the death";
                circumstance protected_person := "The person whose death is caused is a child, domestic worker or vulnerable person" caused_by causes_death;
                circumstance sustained_abuse := "The death is caused by sustained abuse" caused_by causes_death;
            }
        }

        penalty cumulative {

            imprisonment := 0 years .. 20 years;
            supplementary := "A relevant person who causes the death of any child, domestic worker or vulnerable person by
```

---

### s312 — Causing miscarriage

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding invents a `pregnancy_not_more_than_16_weeks` condition and makes pregnancy duration an element-level `any_of`, but the statute states a base offence with a higher penalty only if the pregnancy exceeds 16 weeks.
- suggested fix: Keep the miscarriage elements unconditional and model the `more than 16 weeks` language only as an aggravated penalty branch, with the base penalty as the default.

**Canonical text (first 500 chars):**

> Subject to the provisions of the Termination of Pregnancy Act 1974, whoever voluntarily causes a woman with child to miscarry, shall be punished with imprisonment for a term which may extend to 3 years, or with fine, or with both; and if the woman’s pregnancy is of more than 16 weeks’ duration as calculated in accordance with section 4 of that Act, shall be punished with imprisonment for a term which may extend to 7 years, and shall also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr312-#pr312-
/// @amendment [15/2019]

statute 312 "Causing miscarriage" effective 1872-01-01 effective 2019-12-31 {
    definitions {
        explanation_self_caused_miscarriage := "A woman who causes herself to miscarry is within the meaning of this section.";
    }

    elements {
        /// Section 312 criminalises voluntarily causing miscarriage, subject to the Termination of Pregnancy Act 1974, with punishment split by pregnancy duration.
        all_of {
            circumstance subject_to_termination_of_pregnancy_act := "Subject to the provisions of the Termination of Pregnancy Act 1974";
            actus_reus causing_miscarriage := "Causing a woman with child to miscarry";
            mens_rea voluntary_causation := "Voluntarily";
            any_of {
                circumstance pregnancy_not_more_than_16_weeks := "The woman’s pregnancy is not of more than 16 weeks’ duration as calculated in accordance with section 4 of the Termination of Pregnancy Act 1974";
                circumstance pregnancy_more_than_16_weeks := "The woman’s pregnancy is of more t
```

---

### s363A — Punishment for abduction

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding omits a structured caning punishment even though the canonical text expressly includes caning, and `penalty or_both` does not faithfully capture a three-way “fine, or caning, or any combination” punishment clause.
- suggested fix: Add an explicit caning limb without inventing a stroke count and re-express the penalty logic so all three punishment options and their combinations are structurally captured.

**Canonical text (first 500 chars):**

> Whoever abducts any person shall be punished with imprisonment for a term which may extend to 7 years, or with fine, or with caning, or with any combination of such punishments.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr363A-#pr363A-

referencing penal_code/s362_abduction

statute 363A "Punishment for abduction" effective 1872-01-01 {
    /// Punishment for the offence of abduction under section 362.
    penalty or_both {
        imprisonment := 0 years .. 7 years;
        fine := unlimited;
        supplementary := "Whoever abducts any person shall be punished with imprisonment for a term which may extend to 7 years, or with fine, or with caning, or with any combination of such punishments.";
    }
}

```

---

### s376EA — Exploitative sexual grooming of minor of or above 16 but below 18 years of age

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding truncates subsection (1) after paragraph (b)'s opening words and collapses subsection (2) without preserving the operative paragraph structure and English conjunctions in the canonical text.
- suggested fix: Restore subsection (1)(b)(i)-(iv) and subsection (2)(a)-(c) as structured Yuho elements with the correct conjunctive/disjunctive logic.

**Canonical text (first 500 chars):**

> —(1) Any person of or above 18 years of age ( A ) shall be guilty of an offence if having met or communicated with another person ( B ) on at least one previous occasion — ( a ) A intentionally meets B or travels with the intention of meeting B or B travels to attend a meeting with A which A has either initiated or agreed to whether expressly or by implication; and ( b ) at the time of the acts mentioned in paragraph ( a ) — (2) In subsection (1), “relevant offence” means an offence under — (3) …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr376EA-#pr376EA-
/// @amendment [15/2019]
/// @amendment [Act 23 of 2021 wef 01/03/2022]
/// @amendment [Act 39 of 2022 wef 03/01/2023]

statute 376EA "Exploitative sexual grooming of minor of or above 16 but below 18 years of age" effective 1872-01-01 effective 2019-12-31 effective 2022-03-01 effective 2023-01-03 {
    subsection (1) {
        elements {
            /// The canonical source preserves subsection (1) as an offence with conjunctive limbs, but truncates paragraph (b) after its opening words.
            all_of {
                circumstance accused_age := "Any person of or above 18 years of age ( A )";
                actus_reus prior_contact := "Having met or communicated with another person ( B ) on at least one previous occasion";
                actus_reus meeting_or_travel := "A intentionally meets B or travels with the intention of meeting B or B travels to attend a meeting with A which A has either initiated or agreed to whether expressly or by implication";
                circumstance paragraph_b_opening := "At the time of the acts mentioned i
```

---

### s376EB — Sexual communication with minor below 16 years of age

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: Subsections (2) and (3) are not faithfully preserved because the encoded file keeps only opening text and omits subsection (2)(a)-(b) plus both conditional penalty limbs in subsection (3)(a)-(b).
- suggested fix: Encode subsection (2)(a)-(b) explicitly and represent subsection (3) with both conditional penalty branches, preserving the original conditions and "or with both" structure.

**Canonical text (first 500 chars):**

> —(1) Any person of or above 18 years of age ( A ) shall be guilty of an offence if — ( a ) for the purpose of obtaining sexual gratification or of causing another person ( B ) humiliation, alarm or distress, A intentionally communicated with B ; ( b ) the communication is sexual; ( c ) at the time of the communication, B is below 16 years of age; and ( d ) A does not reasonably believe that B is of or above 16 years of age. (2) For the purposes of this section, it is immaterial — (3) A person wh…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr376EB-#pr376EB-
/// @amendment [15/2019]

statute 376EB "Sexual communication with minor below 16 years of age" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            all_of {
                circumstance accused_age := "Any person of or above 18 years of age ( A )";
                actus_reus communication := "For the purpose of obtaining sexual gratification or of causing another person ( B ) humiliation, alarm or distress, A intentionally communicated with B";
                circumstance sexual_communication := "The communication is sexual";
                circumstance victim_below_16 := "At the time of the communication, B is below 16 years of age";
                circumstance no_reasonable_belief_b_at_or_above_16 := "A does not reasonably believe that B is of or above 16 years of age. [15/2019]";
            }
        }
    }

    subsection (2) {
        definitions {
            immaterial_opening := "For the purposes of this section, it is immaterial —";
        }
    }

    subsection (3) {
        definitions {

```

---

### s376EE — Exploitative sexual activity or image in presence of minor of or above 16 but below 18 years of age

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: Subsection (2) is left empty and subsection (1) omits canonical sub-paragraphs (c)(i) to (c)(iii), and the section uses `effective 2019-12-31` for `[15/2019]` where repo-local L3 precedent treats the Act 15 of 2019 commencement as `2020-01-01`.
- suggested fix: Encode all canonical subsection content, including subsection (2) and paragraph (c)(i)-(iii), and verify the Act 15 of 2019 commencement date before rerunning L3 review.

**Canonical text (first 500 chars):**

> —(1) Any person of or above 18 years of age ( A ) shall be guilty of an offence if — ( a ) for the purpose of obtaining sexual gratification or of causing another person ( B ) humiliation, alarm or distress, A intentionally engages in an activity; ( b ) the activity is sexual; ( c ) A engages in the activity — ( d ) B is of or above 16 but below 18 years of age; ( e ) A does not reasonably believe that B is of or above 18 years of age; and ( f ) A is in a relationship with B that is exploitative…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr376EE-#pr376EE-
/// @amendment [15/2019]
/// @amendment [Act 23 of 2021 wef 01/03/2022]

statute 376EE "Exploitative sexual activity or image in presence of minor of or above 16 but below 18 years of age" effective 1872-01-01 effective 2019-12-31 effective 2022-03-01 {
    subsection (1) {
        elements {
            /// The canonical source preserves subsection (1) as a conjunctive offence, but paragraph (c) is truncated after its opening words.
            all_of {
                circumstance accused_age := "Any person of or above 18 years of age ( A )";
                actus_reus purpose_activity := "For the purpose of obtaining sexual gratification or of causing another person ( B ) humiliation, alarm or distress, A intentionally engages in an activity";
                circumstance sexual_activity := "The activity is sexual";
                actus_reus paragraph_c_opening := "A engages in the activity —";
                circumstance b_age_range := "B is of or above 16 but below 18 years of age";
                circumstance no_reasonable_belief_b_is_18 :=
```

---

### s376E — Sexual grooming of minor below 16 years of age

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding omits subsection (1)(b)(i)-(iii), subsection (2)(a)-(c), and the subsection (4) conditional punishment branches, so the statute's operative conjunctive conditions and `or with both` penalty structure are not faithfully represented.
- suggested fix: Encode the missing sub-items explicitly and represent subsection (4) with both age-based penalty branches, including imprisonment, fine, and `or_both`.

**Canonical text (first 500 chars):**

> —(1) Any person of or above 18 years of age ( A ) shall be guilty of an offence if having met or communicated with another person ( B ) on at least one previous occasion — ( a ) A intentionally meets B or travels with the intention of meeting B or B travels to attend a meeting with A which A has either initiated or agreed to whether expressly or by implication; and ( b ) at the time of the acts referred to in paragraph ( a ) — (2) In subsection (1), “relevant offence” means an offence under — (3…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr376E-#pr376E-
/// @amendment [15/2019]
/// @amendment [Act 23 of 2021 wef 01/03/2022]
/// @amendment [Act 39 of 2022 wef 03/01/2023]

statute 376E "Sexual grooming of minor below 16 years of age" effective 1872-01-01 effective 2019-12-31 effective 2022-03-01 effective 2023-01-03 {
    subsection (1) {
        elements {
            /// The canonical source preserves subsection (1) as an offence with conjunctive limbs, but truncates paragraph (b) after its opening words.
            all_of {
                circumstance accused_age := "Any person of or above 18 years of age ( A )";
                actus_reus prior_contact := "Having met or communicated with another person ( B ) on at least one previous occasion";
                actus_reus meeting_or_travel := "A intentionally meets B or travels with the intention of meeting B or B travels to attend a meeting with A which A has either initiated or agreed to whether expressly or by implication";
                circumstance paragraph_b_opening := "At the time of the acts referred to in paragraph ( a ) —";
           
```

---

### s377BC — Distribution of voyeuristic image or recording

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: Canonical subsection (2) is missing from the encoding, and subsections (3) and (4) omit or mis-encode the caning and alternative/cumulative penalty structure stated in the statute.
- suggested fix: Encode subsection (2) verbatim from `sub_items`, add the missing caning liability, and model subsection (4) as imprisonment plus alternative fine-or-caning rather than a single imprisonment-plus-fine block.

**Canonical text (first 500 chars):**

> —(1) Any person ( A ) shall be guilty of an offence who — ( a ) intentionally or knowingly distributes an image or recording of another person ( B ) without B ’s consent to the distribution; ( b ) knowing or having reason to believe that the image or recording was obtained through the commission of an offence under section 377BB; and ( c ) knows or has reason to believe that B does not consent to the distribution. (2) Any person ( A ) shall be guilty of an offence who — (3) Subject to subsection…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr377BC-#pr377BC-
/// @amendment [15/2019]

statute 377BC "Distribution of voyeuristic image or recording" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// subsection (1) requires distribution plus all three knowledge/consent conditions
            all_of {
                actus_reus distribution := "A intentionally or knowingly distributes an image or recording of another person ( B ) without B ’s consent to the distribution. [15/2019]";
                circumstance obtained_through_377BB := "A knows or has reason to believe that the image or recording was obtained through the commission of an offence under section 377BB. [15/2019]";
                mens_rea knows_no_consent := "A knows or has reason to believe that B does not consent to the distribution. [15/2019]";
            }
        }
    }

    subsection (2) {
        /// Canonical source text in library/penal_code/_raw/act.json is truncated at:
        /// "Any person ( A ) shall be guilty of an offence who —"
    }

    subsection (3) {
        penalty or_
```

---

### s377BH — Producing child abuse material

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: Subsection (3)'s canonical itemised production methods in (a)-(c) are omitted, and subsection (2)'s penalty omits the statute's express caning alternative.
- suggested fix: Encode subsection (3)(a)-(c) explicitly and represent subsection (2) as mandatory imprisonment plus the disjunctive fine-or-caning liability without inventing any further caning details.

**Canonical text (first 500 chars):**

> —(1) Any person who intentionally produces child abuse material knowing or having reason to believe that the material is child abuse material shall be guilty of an offence. (2) A person who is guilty of an offence under subsection (1) shall on conviction be punished with imprisonment for a term which may extend to 10 years, and shall also be liable to fine or to caning. (3) For the purposes of subsection (1), the ways in which material is produced may include —

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr377BH-#pr377BH-
/// @amendment [15/2019]

statute 377BH "Producing child abuse material" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// Subsection (1) requires intentional production plus knowledge or reason to believe that the material is child abuse material.
            all_of {
                actus_reus production := "Any person produces child abuse material";
                mens_rea intention := "Intentionally";
                mens_rea knowledge_or_reason_to_believe := "Knowing or having reason to believe that the material is child abuse material. [15/2019]";
            }
        }
    }

    subsection (2) {
        penalty cumulative {

            imprisonment := 0 years .. 10 years;
            supplementary := "A person who is guilty of an offence under subsection (1) shall on conviction be punished with imprisonment for a term which may extend to 10 years, and shall also be liable to fine or to caning. [15/2019]";

            alternative {
                fine := unlimited;
                supplem
```

---

### s377B — Sexual penetration with living animal

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding leaves canonical subsection (3) empty, fabricates a `0 .. 24 strokes` caning cap for subsection (4) where the statute states only that the offender is liable to caning, and uses only `effective 1872-01-01` even though section 377B was introduced by Act 51 of 2007 with commencement on 1 February 2008.
- suggested fix: Populate subsection (3) verbatim from the canonical text, change subsection (4) caning to an unspecified liability form, and add the 2008 commencement date to the section’s effective clauses.

**Canonical text (first 500 chars):**

> —(1) Any person ( A ) who — ( a ) penetrates, with A ’s penis, the vagina, anus or any orifice of an animal; or ( b ) causes or permits A ’s vagina, anus or mouth, as the case may be, to be penetrated by the penis of an animal, shall be guilty of an offence. (2) A person who is guilty of an offence under subsection (1) shall be punished with imprisonment for a term which may extend to 2 years, or with fine, or with both. (3) Any person ( A ) who — (4) A person who is guilty of an offence under s…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr377B-#pr377B-

statute 377B "Sexual penetration with living animal" effective 1872-01-01 {
    subsection (1) {
        elements {
            /// Subsection (1) is conjunctive overall: the actor must be a person A and must commit one of the two penetration alternatives.
            all_of {
                circumstance person_a := "Any person ( A )";
                any_of {
                    actus_reus penile_penetration_of_animal := "Penetrates, with A ’s penis, the vagina, anus or any orifice of an animal";
                    actus_reus causes_or_permits_penetration_by_animal := "Causes or permits A ’s vagina, anus or mouth, as the case may be, to be penetrated by the penis of an animal";
                }
            }
        }
    }

    subsection (2) {
        penalty or_both {
            imprisonment := 0 days .. 2 years;
            fine := unlimited;
        }
    }

    subsection (3) {
    }

    subsection (4) {
        penalty cumulative {
            imprisonment := 0 days .. 20 years;
            supplementary := "A person who is guilty of an 
```

---

### s377CA — Meaning of exploitative relationship

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: Subsection (2) omits the canonical paragraph list in `(2)(a)` to `(2)(g)`, and the operative list logic in subsections `(1)` and `(2)` is flattened into `definitions` instead of being encoded as structured conjunctive/disjunctive content.
- suggested fix: Preserve subsection `(1)`'s required factors and subsection `(2)`'s seven presumed relationships as structured content, using list logic that matches the statute’s English.

**Canonical text (first 500 chars):**

> —(1) For the purposes of sections 375, 376, 376A, 376AA, 376EA, 376EC, 376EE, 377BL and 377D, whether an accused person’s relationship with a person below 18 years of age (called in this section a minor) is exploitative of the minor is to be determined by the court in the circumstances of each case and the court must have regard to the following in making such determination: ( a ) the age of the minor; ( b ) the difference between the age of the accused person and the minor; ( c ) the nature of …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr377CA-#pr377CA-
/// @amendment [15/2019]

statute 377CA "Meaning of exploitative relationship" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        definitions {
            minor := "A person below 18 years of age.";
            exploitative_relationship_determination := "For the purposes of sections 375, 376, 376A, 376AA, 376EA, 376EC, 376EE, 377BL and 377D, whether an accused person’s relationship with a person below 18 years of age (called in this section a minor) is exploitative of the minor is to be determined by the court in the circumstances of each case.";
            determination_factor_age_of_minor := "The age of the minor.";
            determination_factor_age_difference := "The difference between the age of the accused person and the minor.";
            determination_factor_nature_of_relationship := "The nature of the relationship.";
            determination_factor_degree_of_control_or_influence := "The degree of control or influence exercised by the accused person over the minor. [15/2019]";
        }
    }

    subsection (2) 
```

---

### s379A — Punishment for theft of a motor vehicle

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: Subsection (3) is reduced to a comment instead of preserving the canonical definitions of “component part” and “motor vehicle”, and the encoding uses only `effective 1872-01-01` even though this section has later amendment provenance.
- suggested fix: Encode subsection (3) with the two statutory definitions and add the later effective date(s) for section 379A before re-running L3 review.

**Canonical text (first 500 chars):**

> —(1) Whoever commits theft of a motor vehicle or any component part of a motor vehicle shall be punished with imprisonment for a term which may extend to 7 years, and shall also be liable to fine. (2) A person convicted of an offence under this section shall, unless the court for special reasons thinks fit to order otherwise, be disqualified for such period as the court may order from the date of his release from imprisonment from holding or obtaining a driving licence under the Road Traffic Act…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr379A-#pr379A-

statute 379A "Punishment for theft of a motor vehicle" effective 1872-01-01 {
    subsection (1) {
        /// This subsection punishes theft under section 378 where the property is a motor vehicle or a component part of a motor vehicle.
        penalty cumulative {
            imprisonment := 0 years .. 7 years;
            fine := unlimited;
            supplementary := "Whoever commits theft of a motor vehicle or any component part of a motor vehicle shall be punished with imprisonment for a term which may extend to 7 years, and shall also be liable to fine.";
        }
    }

    subsection (2) {
        /// This subsection imposes a post-release driving-licence disqualification on conviction unless the court orders otherwise for special reasons.
        penalty cumulative {
            supplementary := "A person convicted of an offence under this section shall, unless the court for special reasons thinks fit to order otherwise, be disqualified for such period as the court may order from the date of his release from imprisonment from holding or o
```

---

### s414 — Assisting in concealment or disposal of stolen property

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding uses an unsound `[15/2019]` effective date (`2019-12-31` instead of repo-local `2020-01-01`) and alters subsection (2)(b) by substituting `Road Traffic Act (Cap. 276)` for the canonical `Road Traffic Act 1961`.
- suggested fix: Update the amendment effective date to the verified commencement date and restore subsection (2)(b) to the canonical Road Traffic Act wording before rerunning L3 review.

**Canonical text (first 500 chars):**

> —(1) Whoever voluntarily assists in concealing or disposing of or making away with property which he knows or has reason to believe to be stolen property or property obtained in whole or in part through any criminal offence involving fraud or dishonesty, shall be punished with imprisonment for a term which may extend to 5 years, or with fine, or with both. (2) If the property mentioned in subsection (1) is a motor vehicle or any component part of a motor vehicle as defined in section 379A(3), a …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr414-#pr414-
/// @amendment [15/2019]

referencing penal_code/s379A_punishment_theft_motor_vehicle
referencing penal_code/s410_stolen_property

statute 414 "Assisting in concealment or disposal of stolen property" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// The offence requires voluntary assistance, tainted property, and knowledge or reason to believe of that taint.
            all_of {
                actus_reus assists_concealment_or_disposal := "Voluntarily assists in concealing or disposing of or making away with property";
                circumstance tainted_property := "The property is stolen property or property obtained in whole or in part through any criminal offence involving fraud or dishonesty";
                mens_rea knows_or_has_reason_to_believe := "Knows or has reason to believe that the property is stolen property or property obtained in whole or in part through any criminal offence involving fraud or dishonesty";
            }
        }

        penalty or_both {
            imprisonment :=
```

---

### s416A — Illegally obtained personal information

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: Subsections (2), (3), and (7) drop the canonical paragraph content and subsection (3)'s conjunctive structure, and the section uses `effective 2019-12-31` for `[15/2019]` despite repo-local L3 precedent treating Act 15 of 2019 commencement as `2020-01-01`.
- suggested fix: Restore the missing `(2)(a)` to `(2)(b)`, `(3)(a)` to `(3)(b)`, and `(7)(a)` to `(7)(b)` content with the correct logical structure, then correct the amendment effective date.

**Canonical text (first 500 chars):**

> —(1) A person ( A ) shall be guilty of an offence who, knowing or having reason to believe that any personal information about another person ( B ) (being an individual) was obtained without B ’s consent — ( a ) obtains or retains the personal information; or ( b ) supplies, offers to supply, transmits or makes available, by any means, the personal information. (2) It is not an offence under subsection (1)( a ) if the person obtained or retained the personal information for a purpose other than …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr416A-#pr416A-
/// @amendment [15/2019]

statute 416A "Illegally obtained personal information" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            all_of {
                mens_rea knowledge_or_reason_to_believe := "Knowing or having reason to believe that any personal information about another person ( B ) (being an individual) was obtained without B ’s consent";
                any_of {
                    actus_reus paragraph_a := "Obtains or retains the personal information";
                    actus_reus paragraph_b := "Supplies, offers to supply, transmits or makes available, by any means, the personal information. [15/2019]";
                }
            }
        }
    }

    subsection (2) {
        definitions {
            carve_out_for_subsection_1a_lead_in := "It is not an offence under subsection (1)( a ) if the person obtained or retained the personal information for a purpose other than —";
        }
    }

    subsection (3) {
        definitions {
            carve_out_for_subsection_1b_lead_in := "It 
```

---

### s449 — House-breaking in order to commit an offence punishable with death

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The encoding does not preserve the imprisonment-for-life alternative as a structured penalty branch, and it uses `effective 2019-12-31` for a section tagged `[15/2019]`, which is not a reliable commencement date for that amendment.
- suggested fix: Encode imprisonment for life as an explicit alternative penalty branch and replace the amendment effective date with the correct commencement date for Act 15 of 2019 before resubmitting for L3 review.

**Canonical text (first 500 chars):**

> Whoever commits house-breaking in order to commit any offence punishable with death, shall be punished with imprisonment for life, or with imprisonment for a term not exceeding 15 years, and shall, if he is not sentenced to imprisonment for life, also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr449-#pr449-
/// @amendment [15/2019]

referencing penal_code/s442_house_breaking

statute 449 "House-breaking in order to commit an offence punishable with death" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// Section 449 is conjunctive: the accused must commit house-breaking and do so in order to commit a death-punishable offence.
        all_of {
            actus_reus house_breaking := "Commits house-breaking";
            mens_rea purpose_of_committing_capital_offence := "In order to commit any offence punishable with death";
        }
    }

    penalty alternative {
        imprisonment := 0 days .. 15 years;
        supplementary := "Whoever commits house-breaking in order to commit any offence punishable with death, shall be punished with imprisonment for life, or with imprisonment for a term not exceeding 15 years. [15/2019]";
    }

    penalty when non_life_sentence {
        fine := unlimited;
        supplementary := "If the offender is not sentenced to imprisonment for life, the offender is also liable to fine. [15/2019]";
    
```

---

### s476 — Counterfeiting a device or mark used for authenticating documents or electronic records other than those described in section 467, or possessing counterfeit marked material

**Verdict:** `INVESTIGATE` — no machine-readable check code; needs human read

**Flag** (check -1):
- reason: The canonical penalty is imprisonment up to 10 years and liability to fine, but the encoding uses `penalty or_both`, which introduces an alternative fine-only branch not stated in the statute.
- suggested fix: Replace the penalty form with a cumulative or otherwise explicitly mandatory imprisonment-plus-fine encoding that matches the canonical text.

**Canonical text (first 500 chars):**

> Whoever counterfeits upon or in the substance of any material any device or mark used for the purpose of authenticating any document or electronic record other than the documents described in section 467, intending that such device or mark shall be used for the purpose of giving the appearance of authenticity to any document or electronic record then forged or thereafter to be forged on such material, or who with such intent has in his possession any material upon or in the substance of which an…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr476-#pr476-

statute 476 "Counterfeiting a device or mark used for authenticating documents or electronic records other than those described in section 467, or possessing counterfeit marked material" effective 1872-01-01 {
    elements {
        /// The section criminalises either counterfeiting the authenticating device or possessing material bearing the counterfeit, provided the same intent is present.
        all_of {
            any_of {
                actus_reus counterfeits_device_or_mark := "Counterfeits upon or in the substance of any material any device or mark used for the purpose of authenticating any document or electronic record other than the documents described in section 467";
                actus_reus possesses_counterfeit_marked_material := "Has in his possession any material upon or in the substance of which any such device or mark has been counterfeited";
            }
            mens_rea intent_to_give_appearance_of_authenticity := "Intending that such device or mark shall be used for the purpose of giving the appearance of authenticity to a
```

---

