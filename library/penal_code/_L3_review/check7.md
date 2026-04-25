# L3 flags — failed check 731 sections in this group.---### s113 — Liability of abettor for an offence caused by the act abetted different from that intended by the abettor

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The canonical text is a liability attribution rule and does not itself prescribe a standalone punishment clause, but the encoding adds a `penalty {}` block.
- suggested fix: Move the "liable for the effect caused" language out of `penalty {}` into a non-penalty liability/refinement construct while preserving the illustration verbatim.

**Canonical text (first 500 chars):**

> When an act is abetted with the intention on the part of the abettor of causing a particular effect, and an act for which the abettor is liable in consequence of the abetment causes a different effect from that intended by the abettor, the abettor is liable for the effect caused, in the same manner, and to the same extent, as if he had abetted the act with the intention of causing that effect, provided he knew that the act abetted was likely to cause that effect.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr113-#pr113-

statute 113 "Liability of abettor for an offence caused by the act abetted different from that intended by the abettor" effective 1872-01-01 {
    elements {
        /// Section 113 applies only where the abetment carried an intended effect, the liable act caused a different effect, and the abettor knew that different effect was likely.
        all_of {
            actus_reus act_abetted := "An act is abetted";
            mens_rea intention_to_cause_particular_effect := "The abetment is with the intention on the part of the abettor of causing a particular effect";
            circumstance liable_act_causes_different_effect := "An act for which the abettor is liable in consequence of the abetment causes a different effect from that intended by the abettor";
            mens_rea knowledge_of_likely_effect := "The abettor knew that the act abetted was likely to cause that effect";
        }
    }

    penalty {
        supplementary := "The abettor is liable for the effect caused, in the same manner, and to the same extent, as if he had abetted the act w
```

---

### s130E — Punishment for genocide

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The canonical limb `(b)` authorises imprisonment for life or up to 20 years, but the encoding’s operative penalty only models `imprisonment := 0 years .. 20 years` and leaves life imprisonment only in supplementary text.
- suggested fix: Encode the limb `(b)` punishment so the executable penalty model expressly captures the life-imprisonment alternative as well as the term sentence.

**Canonical text (first 500 chars):**

> Whoever commits genocide shall — ( a ) if the offence consists of the killing of any person, be punished with death; or ( b ) in any other case, be punished with imprisonment for life or with imprisonment for a term which may extend to 20 years.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr130E-#pr130E-
/// @amendment [15/2019]

referencing penal_code/s130D_genocide

statute 130E "Punishment for genocide" effective 1872-01-01 effective 2020-01-01 {
    /// Punishment for the offence of genocide under section 130D.
    penalty alternative when offence_consists_of_killing_any_person {
        death := TRUE;
        supplementary := "If the offence consists of the killing of any person, the offender shall be punished with death. [15/2019]";
    }

    penalty alternative when any_other_case {
        imprisonment := 0 years .. 20 years;
        supplementary := "In any other case, the offender shall be punished with imprisonment for life or with imprisonment for a term which may extend to 20 years. [15/2019]";
    }
}

```

---

### s130 — Aiding escape of, rescuing, or harbouring such prisoner

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The penalty encoding omits life imprisonment as an actual encoded penalty branch and makes fine unconditional even though the statute allows fine only if the offender is not sentenced to imprisonment for life.
- suggested fix: Encode the life-imprisonment alternative structurally and make the fine apply only on the non-life-imprisonment branch.

**Canonical text (first 500 chars):**

> Whoever knowingly aids or assists any prisoner of State or prisoner of war in escaping from lawful custody or rescues or attempts to rescue any such prisoner, or harbours or conceals any such prisoner who has escaped from lawful custody, or offers or attempts to offer any resistance to the recapture of such prisoner, shall be punished with imprisonment for life, or with imprisonment for a term which may extend to 15 years, and shall, if he is not sentenced to imprisonment for life, also be liabl…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr130-#pr130-
/// @amendment [15/2019]

statute 130 "Aiding escape of, rescuing, or harbouring such prisoner" effective 1872-01-01 effective 2020-01-01 {
    definitions {
        explanation_escape_from_lawful_custody := "Explanation .—A prisoner of State or prisoner of war who is permitted to be at large on his parole within certain limits in Singapore, is said to escape from lawful custody if he goes beyond the limits within which he is allowed to be at large.";
    }

    elements {
        /// Section 130 is conjunctive overall, with four disjunctive actus reus limbs tied to a knowing mental element.
        all_of {
            mens_rea knowledge := "Whoever knowingly";
            any_of {
                actus_reus aiding_or_assisting_escape := "Aids or assists any prisoner of State or prisoner of war in escaping from lawful custody" caused_by knowledge;
                actus_reus rescuing_or_attempting_rescue := "Rescues or attempts to rescue any such prisoner" caused_by knowledge;
                actus_reus harbouring_or_concealing_escapee := "Harbours or c
```

---

### s132 — Abetment of mutiny, if mutiny is committed in consequence thereof

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding does not machine-encode the statute's express life-imprisonment alternative, leaving it only in `supplementary` text, so the penalty facts are incomplete.
- suggested fix: Add an explicit life-imprisonment penalty branch or field alongside death and the term-imprisonment branch, while keeping the existing conditional fine logic.

**Canonical text (first 500 chars):**

> Whoever abets the committing of mutiny by an officer or any serviceman in the Singapore Armed Forces or any visiting forces lawfully present in Singapore shall, if mutiny be committed in consequence of that abetment, be punished with death or with imprisonment for life, or with imprisonment for a term which may extend to 10 years, and shall, if he is not sentenced to death or imprisonment for life, also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr132-#pr132-
/// @amendment [15/2019]
statute 132 "Abetment of mutiny, if mutiny is committed in consequence thereof" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// The offence requires abetment of mutiny and the consequential commission of mutiny.
        all_of {
            actus_reus abetment := "Whoever abets the committing of mutiny by an officer or any serviceman in the Singapore Armed Forces or any visiting forces lawfully present in Singapore";
            circumstance mutiny_committed := "Mutiny be committed in consequence of that abetment";
        }
    }

    penalty alternative {
        imprisonment := 0 years .. 10 years;
        death := TRUE;
        supplementary := "Whoever abets the committing of mutiny by an officer or any serviceman in the Singapore Armed Forces or any visiting forces lawfully present in Singapore shall, if mutiny be committed in consequence of that abetment, be punished with death or with imprisonment for life, or with imprisonment for a term which may extend to 10 years. [15/2019]";
    }

    penalty
```

---

### s158 — Being hired to take part in an unlawful assembly or riot

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The `base_offence` condition is broad enough that an armed offender also satisfies it, so the encoding can trigger both the 2-year and 5-year penalty branches even though section 158 states alternative punishments for separate limbs.
- suggested fix: Make the penalty triggers mutually exclusive by separating the ordinary limb from the armed limb at the element or condition level.

**Canonical text (first 500 chars):**

> Whoever is engaged or hired, or offers or attempts to be hired or engaged, to do or assist in doing any of the acts specified in section 141, shall be punished with imprisonment for a term which may extend to 2 years, or with fine, or with both; and whoever, being so engaged or hired as aforesaid, goes armed, or engages or offers to go armed, with any deadly weapon, or with anything which used as a weapon of offence is likely to cause death, shall be punished with imprisonment for a term which m…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr158-#pr158-

statute 158 "Being hired to take part in an unlawful assembly or riot" effective 1872-01-01 {
    elements {
        /// Section 158 criminalises being hired or offering to be hired to do or assist in doing acts specified in section 141, with a higher punishment where the person goes armed.
        all_of {
            actus_reus hired_or_engaged := "Is engaged or hired, or offers or attempts to be hired or engaged";
            actus_reus unlawful_assembly_acts := "To do or assist in doing any of the acts specified in section 141";
            any_of {
                circumstance base_offence := "The person is engaged or hired, or offers or attempts to be hired or engaged to do or assist in doing any of the acts specified in section 141";
                /// The aggravated limb applies where the person, being so engaged or hired as aforesaid, goes armed or engages or offers to go armed.
                all_of {
                    circumstance engaged_or_hired_as_aforesaid := "Being so engaged or hired as aforesaid";
                    actus_reus go
```

---

### s194 — Giving or fabricating false evidence with intent to procure conviction of a capital offence

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The penalty encoding does not faithfully capture the statute because imprisonment for life is only mentioned in supplementary text and the aggravated death-eligible branch is encoded broadly enough to cover fabrication as well as giving false evidence.
- suggested fix: Model the base punishment as life imprisonment or up to 20 years with fine only on the non-life branch, and scope the aggravated branch to the person who gives such false evidence.

**Canonical text (first 500 chars):**

> Whoever gives or fabricates false evidence, intending thereby to cause, or knowing it to be likely that he will thereby cause, any person to be convicted of an offence which is capital by this Code, or under any other law for the time being in force, shall be punished with imprisonment for life, or with imprisonment for a term which may extend to 20 years, and shall, if he is not sentenced to imprisonment for life, also be liable to fine; and if an innocent person is convicted and executed in co…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr194-#pr194-
/// @amendment [15/2019]

statute 194 "Giving or fabricating false evidence with intent to procure conviction of a capital offence" effective 1872-01-01 effective 2019-12-31 {
    definitions {
        capital_offence := "An offence which is capital by this Code, or under any other law for the time being in force";
        aggravated_consequence := "An innocent person is convicted and executed in consequence of such false evidence";
    }

    elements {
        /// Section 194 requires false evidence plus the fault element directed at procuring conviction of a capital offence.
        all_of {
            any_of {
                actus_reus gives_false_evidence := "Gives false evidence";
                actus_reus fabricates_false_evidence := "Fabricates false evidence";
            }
            any_of {
                mens_rea intent_to_cause_conviction := "Intending thereby to cause any person to be convicted of a capital offence";
                mens_rea knowledge_likely_to_cause_conviction := "Knowing it to be likely that he will thereby cause a
```

---

### s222 — Intentional omission to apprehend on the part of a public servant bound by law to apprehend person under sentence of a court of justice

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The first penalty branch does not faithfully capture the statute because imprisonment for life is only preserved in supplementary text rather than in the operative penalty encoding.
- suggested fix: Re-encode limb (a) so the life-imprisonment alternative is represented explicitly rather than only described in supplementary prose.

**Canonical text (first 500 chars):**

> Whoever, being a public servant, legally bound as such public servant to apprehend or to keep in confinement any person under sentence of a court of justice for any offence, or lawfully committed to custody, intentionally omits to apprehend such person, or intentionally suffers such person to escape, or intentionally aids such person in escaping or attempting to escape from such confinement, shall be punished — ( a ) with imprisonment for life or with imprisonment for a term which may extend to …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr222-#pr222-

statute 222 "Intentional omission to apprehend on the part of a public servant bound by law to apprehend person under sentence of a court of justice" effective 1872-01-01 {
    elements {
        /// Section 222 requires public-servant status, legal duty, intentional omission/escape conduct, and one sentence-status branch.
        all_of {
            circumstance public_servant_status := "Whoever, being a public servant";
            circumstance legal_duty := "Legally bound as such public servant to apprehend or to keep in confinement any person under sentence of a court of justice for any offence, or lawfully committed to custody";
            mens_rea intention := "Intentionally";
            any_of {
                actus_reus omission_to_apprehend := "Omits to apprehend such person" caused_by intention;
                actus_reus suffers_escape := "Suffers such person to escape" caused_by intention;
                actus_reus aids_escape := "Aids such person in escaping or attempting to escape from such confinement" caused_by intention;
         
```

---

### s287 — Rash or negligent conduct with respect to any machinery in possession or under charge of offender

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding drops the four conditional punishment limbs in canonical subsection (3) and incorrectly states that the raw text stops at the dash.
- suggested fix: Encode subsection (3)(a) to (d) as conditional penalty branches with the correct imprisonment and fine consequences, including the $5,000 fine cap only for subsection (1)(a) or (b).

**Canonical text (first 500 chars):**

> —(1) A person shall be guilty of an offence who does, with any machinery in the person’s possession or under the person’s care, any act so rashly or negligently as — ( a ) to be likely to cause hurt or injury to any other person; ( b ) to endanger human life; ( c ) to cause hurt or injury to any other person; ( d ) to cause grievous hurt to any other person; or ( e ) to cause the death of any other person. (2) In subsection (1), an act includes an omission to take such measure with any machinery…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr287-#pr287-
/// @amendment [15/2019]

statute 287 "Rash or negligent conduct with respect to any machinery in possession or under charge of offender" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// Subsection (1) requires conduct with machinery in the person's possession or care, rashness or negligence, and one of the listed harmful outcomes.
            all_of {
                actus_reus machinery_act := "A person does, with any machinery in the person’s possession or under the person’s care, any act";
                any_of {
                    mens_rea rashly := "The act is done so rashly";
                    mens_rea negligently := "The act is done so negligently";
                }
                any_of {
                    circumstance likely_hurt_or_injury := "The act is likely to cause hurt or injury to any other person";
                    circumstance endangers_human_life := "The act endangers human life";
                    circumstance causes_hurt_or_injury := "The act causes hurt or injury to a
```

---

### s308 — Attempt to commit culpable homicide

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The `hurt_caused` penalty branch omits a structured caning punishment even though the canonical text expressly provides imprisonment, fine, caning, or any combination of those punishments.
- suggested fix: Add the missing `caning :=` punishment to the aggravated `when hurt_caused` penalty branch so every canonical punishment option is encoded.

**Canonical text (first 500 chars):**

> Whoever does any act with the intention to cause death and under such circumstances that if he by that act caused death he would be guilty of culpable homicide not amounting to murder, shall be punished with imprisonment for a term which may extend to 7 years, or with fine, or with both; and if hurt is caused to any person by such act, the offender shall be punished with imprisonment for a term which may extend to 15 years, or with fine, or with caning, or with any combination of such punishment…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr308-#pr308-
/// @amendment [15/2019]

statute 308 "Attempt to commit culpable homicide" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// Section 308 requires the doing of an act, the intention to cause death, and circumstances making the completed killing culpable homicide not amounting to murder.
        all_of {
            actus_reus doing_act := "Whoever does any act";
            mens_rea intention_to_cause_death := "The act is done with the intention to cause death";
            circumstance culpable_homicide_not_murder_if_death_caused := "Under such circumstances that if he by that act caused death he would be guilty of culpable homicide not amounting to murder";
        }
    }

    penalty or_both {
        imprisonment := 0 years .. 7 years;
        fine := unlimited;
        supplementary := "Whoever does any act with the intention to cause death and under such circumstances that if he by that act caused death he would be guilty of culpable homicide not amounting to murder, shall be punished with imprisonment for a term which may ex
```

---

### s314 — Death caused by act done with intent to cause miscarriage

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding does not faithfully capture the no-consent penalty alternative because it omits an explicit life-imprisonment branch and invents a separate `woman_without_consent_non_life_sentence` condition.
- suggested fix: Encode the no-consent punishment as explicit alternatives of imprisonment for life or the above-mentioned imprisonment-plus-fine punishment using the canonical condition only.

**Canonical text (first 500 chars):**

> Subject to the provisions of the Termination of Pregnancy Act 1974, whoever with intent to cause the miscarriage of a woman with child does any act which causes the death of such woman, shall be punished with imprisonment for a term which may extend to 10 years, and shall also be liable to fine; and if the act is done without the consent of the woman, shall be punished either with imprisonment for life, or with the punishment above‑mentioned.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr314-#pr314-

statute 314 "Death caused by act done with intent to cause miscarriage" effective 1872-01-01 {
    definitions {
        explanation_likelihood_of_death := "Explanation. — It is not essential to this offence that the offender should know that the act is likely to cause death.";
    }

    elements {
        /// Section 314 requires an act done with intent to cause miscarriage, causing the death of the woman, subject to the Termination of Pregnancy Act 1974.
        all_of {
            circumstance subject_to_termination_of_pregnancy_act := "Subject to the provisions of the Termination of Pregnancy Act 1974";
            actus_reus doing_act := "Doing any act";
            mens_rea intent_to_cause_miscarriage := "With intent to cause the miscarriage of a woman with child";
            circumstance woman_with_child := "The woman is a woman with child";
            actus_reus causes_death := "Causing the death of such woman" caused_by doing_act;
            any_of {
                circumstance woman_consented := "The act is done with the consent of the 
```

---

### s324 — Voluntarily causing hurt by dangerous weapons or means

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding fabricates a caning range of `0 .. 24 strokes` even though the canonical text states only liability to caning without any numeric stroke count.
- suggested fix: Preserve the caning limb without inventing a stroke count, such as by moving the verbatim caning language into a supplementary penalty field.

**Canonical text (first 500 chars):**

> Whoever, except in the case provided for by section 334, voluntarily causes hurt by means of any instrument for shooting, stabbing or cutting, or any instrument which, used as a weapon of offence, is likely to cause death, or by means of fire or any heated substance, or by means of any poison or any corrosive substance, or by means of any explosive substance, or by means of any substance which it is harmful to the human body to inhale, to swallow, or to receive into the blood, or by means of any…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr324-#pr324-
/// @amendment [15/2019]

statute 324 "Voluntarily causing hurt by dangerous weapons or means" effective 1872-01-01 effective 2019-12-31 {
    elements {
        all_of {
            circumstance not_section_334_case := "Except in the case provided for by section 334";
            mens_rea voluntary := "Voluntarily";
            actus_reus causes_hurt := "Causes hurt";
            /// The dangerous means alternatives are disjunctive; any one satisfies this limb.
            any_of {
                circumstance instrument_for_shooting_stabbing_or_cutting := "By means of any instrument for shooting, stabbing or cutting";
                circumstance weapon_likely_to_cause_death := "By means of any instrument which, used as a weapon of offence, is likely to cause death";
                circumstance fire_or_heated_substance := "By means of fire or any heated substance";
                circumstance poison_or_corrosive_substance := "By means of any poison or any corrosive substance";
                circumstance explosive_substance := "By means of any expl
```

---

### s326 — Voluntarily causing grievous hurt by dangerous weapons or means

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding does not faithfully capture the punishment because it omits an explicit life-imprisonment branch and invents a separate `non_life_sentence` condition for fine liability.
- suggested fix: Encode the penalty as the canonical alternatives and conditional fine consequence without introducing a non-canonical condition.

**Canonical text (first 500 chars):**

> Whoever, except in the case provided for by section 335, voluntarily causes grievous hurt by means of any instrument for shooting, stabbing or cutting, or any instrument which, used as a weapon of offence, is likely to cause death, or by means of fire or any heated substance, or by means of any poison or any corrosive substance, or by means of any explosive substance, or by means of any substance which it is harmful to the human body to inhale, to swallow, or to receive into the blood, or by mea…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr326-#pr326-
/// @amendment [15/2019]

statute 326 "Voluntarily causing grievous hurt by dangerous weapons or means" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// Section 326 is conjunctive overall: the section 335 exclusion, voluntary causing of grievous hurt, and one dangerous weapon or means must all be present.
        all_of {
            circumstance not_section_335_case := "Except in the case provided for by section 335";
            mens_rea voluntary := "Voluntarily";
            actus_reus causes_grievous_hurt := "Causes grievous hurt";
            /// The dangerous weapon or means limb is disjunctive; any one statutory means suffices.
            any_of {
                circumstance instrument_for_shooting_stabbing_or_cutting := "By means of any instrument for shooting, stabbing or cutting";
                circumstance weapon_likely_to_cause_death := "By means of any instrument which, used as a weapon of offence, is likely to cause death";
                circumstance fire_or_heated_substance := "By means of fire or any heated s
```

---

### s327 — Voluntarily causing hurt to extort property or to constrain to an illegal act

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding fabricates a caning range of `0 .. 24 strokes` even though the canonical text only says the offender is liable "to caning" without specifying any stroke count.
- suggested fix: Remove the invented numeric caning clause and preserve the caning limb only in an explicitly labelled textual refinement or supplementary punishment text that does not add a number.

**Canonical text (first 500 chars):**

> Whoever voluntarily causes hurt for the purpose of extorting from the sufferer, or from any person interested in the sufferer, any property or valuable security, or of constraining the sufferer, or any person interested in such sufferer, to do anything which is illegal or which may facilitate the commission of an offence, shall be punished with imprisonment for a term which may extend to 10 years, and shall also be liable to fine or to caning.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr327-#pr327-
statute 327 "Voluntarily causing hurt to extort property or to constrain to an illegal act" effective 1872-01-01 {
    elements {
        /// The section is conjunctive: voluntary causation of hurt plus one of the two coercive purposes.
        all_of {
            mens_rea voluntary := "Voluntarily";
            actus_reus causes_hurt := "Causes hurt";
            /// The coercive purpose is disjunctive: extortion of property or valuable security, or constraint to an illegal act or one facilitating an offence.
            any_of {
                mens_rea purpose_of_extorting_property := "For the purpose of extorting from the sufferer, or from any person interested in the sufferer, any property or valuable security";
                mens_rea purpose_of_constraining_illegal_act := "Of constraining the sufferer, or any person interested in such sufferer, to do anything which is illegal or which may facilitate the commission of an offence";
            }
        }
    }

    penalty cumulative {

        imprisonment := 0 years .. 10 years;
        supple
```

---

### s328 — Causing hurt by means of poison, etc., with intent to commit an offence

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding hard-codes `caning := 0 .. 24 strokes` even though the canonical text only says the offender is liable to caning without specifying any stroke count.
- suggested fix: Preserve the caning limb without inventing a numeric range, consistent with the repo's handling of uncapped caning provisions.

**Canonical text (first 500 chars):**

> Whoever administers to, or causes to be taken by, any person any poison or any stupefying or intoxicating substance, or any substance which is harmful to the human body to inhale, swallow or receive into the blood, with intent to cause hurt to such person, or with intent to commit or to facilitate the commission of an offence, or knowing it to be likely that he will thereby cause hurt, shall be punished with imprisonment for a term which may extend to 10 years, and shall also be liable to fine o…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr328-#pr328-
/// @amendment [15/2019]

statute 328 "Causing hurt by means of poison, etc., with intent to commit an offence" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// Section 328 requires the prohibited administration or caused ingestion, one listed harmful substance category, and one listed fault element.
        all_of {
            actus_reus administers_or_causes_taken := "Administers to, or causes to be taken by, any person a substance";

            /// The prohibited means are disjunctive; any one listed substance category is sufficient.
            any_of {
                circumstance poison := "The substance is any poison";
                circumstance stupefying_or_intoxicating_substance := "The substance is any stupefying or intoxicating substance";
                circumstance harmful_substance_to_inhale_swallow_or_receive_into_blood := "The substance is any substance which is harmful to the human body to inhale, swallow or receive into the blood";
            }

            /// The fault element is disjunctive; intent to ca
```

---

### s329 — Voluntarily causing grievous hurt to extort property, or to constrain to an illegal act

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding hard-codes `caning := 0 .. 24 strokes` even though the canonical text only says the offender is liable to caning without specifying any stroke count.
- suggested fix: Preserve the caning limb without inventing a numeric range, consistent with the repo's handling of uncapped caning provisions.

**Canonical text (first 500 chars):**

> Whoever voluntarily causes grievous hurt for the purpose of extorting from the sufferer, or from any person interested in the sufferer, any property or valuable security, or of constraining the sufferer, or any person interested in such sufferer, to do anything which is illegal or which may facilitate the commission of an offence, shall be punished with imprisonment for life, or imprisonment for a term which may extend to 10 years, and shall also be liable to fine or to caning.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr329-#pr329-
statute 329 "Voluntarily causing grievous hurt to extort property, or to constrain to an illegal act" effective 1872-01-01 {
    elements {
        /// The offence requires both voluntary causation of grievous hurt and one of the two prohibited purposes.
        all_of {
            actus_reus grievous_hurt := "Voluntarily causes grievous hurt";
            any_of {
                all_of {
                    mens_rea extortion_purpose := "For the purpose of extorting from the sufferer, or from any person interested in the sufferer";
                    any_of {
                        actus_reus property := "Any property" caused_by extortion_purpose;
                        actus_reus valuable_security := "Any valuable security" caused_by extortion_purpose;
                    }
                }
                all_of {
                    mens_rea constraint_purpose := "For the purpose of constraining the sufferer, or any person interested in such sufferer";
                    any_of {
                        actus_reus illegal_act := "To do anythi
```

---

### s330 — Voluntarily causing hurt to extort confession or to compel restoration of property

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The penalty encoding is not faithful because it makes `fine` part of a cumulative penalty and omits a structured `caning` branch, even though the canonical text says the offender is liable to fine or to caning.
- suggested fix: Model the punishment like the comparable hurt/grievous-hurt extortion sections, with imprisonment plus an alternative branch for `fine` or `caning`.

**Canonical text (first 500 chars):**

> Whoever voluntarily causes hurt for the purpose of extorting from the sufferer, or from any person interested in the sufferer, any confession or any information which may lead to the detection of an offence or misconduct, or for the purpose of constraining the sufferer, or any person interested in the sufferer, to restore or to cause the restoration of any property or valuable security, or to satisfy any claim or demand, or to give information which may lead to the restoration of any property or…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr330-#pr330-

statute 330 "Voluntarily causing hurt to extort confession or to compel restoration of property" effective 1872-01-01 {
    elements {
        /// The offence requires the causing of hurt and one of the two prohibited purposes.
        all_of {
            actus_reus voluntarily_causes_hurt := "Whoever voluntarily causes hurt";
            any_of {
                mens_rea purpose_of_extorting_confession_or_detection_information := "For the purpose of extorting from the sufferer, or from any person interested in the sufferer, any confession or any information which may lead to the detection of an offence or misconduct";
                mens_rea purpose_of_constraining_restoration_or_satisfaction := "For the purpose of constraining the sufferer, or any person interested in the sufferer, to restore or to cause the restoration of any property or valuable security, or to satisfy any claim or demand, or to give information which may lead to the restoration of any property or valuable security";
            }
        }
    }

    penalty cumulative {
       
```

---

### s331 — Voluntarily causing grievous hurt to extort confession or to compel restoration of property

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding omits a structured caning punishment even though the canonical text expressly makes the offender liable to caning in addition to imprisonment and fine.
- suggested fix: Add an explicit caning limb, using `caning := unspecified;` if needed, so every canonical punishment option is encoded without inventing a stroke count.

**Canonical text (first 500 chars):**

> Whoever voluntarily causes grievous hurt for the purpose of extorting from the sufferer, or from any person interested in the sufferer, any confession or any information which may lead to the detection of an offence or misconduct, or for the purpose of constraining the sufferer, or any person interested in the sufferer, to restore or to cause the restoration of any property or valuable security, or to satisfy any claim or demand, or to give information which may lead to the restoration of any pr…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr331-#pr331-
statute 331 "Voluntarily causing grievous hurt to extort confession or to compel restoration of property" effective 1872-01-01 {
    elements {
        /// Section 331 requires the grievous hurt plus one of the listed extortion-or-restoration purposes.
        all_of {
            actus_reus voluntarily_causes_grievous_hurt := "Whoever voluntarily causes grievous hurt";
            any_of {
                mens_rea extorting_confession_or_information := "For the purpose of extorting from the sufferer, or from any person interested in the sufferer, any confession or any information which may lead to the detection of an offence or misconduct";
                mens_rea constraining_restoration_or_satisfaction := "For the purpose of constraining the sufferer, or any person interested in the sufferer, to restore or to cause the restoration of any property or valuable security, or to satisfy any claim or demand, or to give information which may lead to the restoration of any property or valuable security";
            }
        }
    }

    penalty cumulative
```

---

### s332 — Voluntarily causing hurt to deter public servant from his duty

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding omits a structured caning punishment even though the canonical text expressly makes the offender liable to fine or to caning, and the grammar now supports `caning := unspecified` for that case.
- suggested fix: Replace the prose-only preservation of the caning limb with an explicit structured caning branch so every canonical punishment option is encoded without inventing a stroke count.

**Canonical text (first 500 chars):**

> Whoever voluntarily causes hurt to any person being a public servant in the discharge of his duty as such public servant, or with intent to prevent or deter that person or any other public servant from discharging his duty as such public servant, or in consequence of anything done or attempted to be done by that person in the lawful discharge of his duty as such public servant, shall be punished with imprisonment for a term which may extend to 7 years, and shall also be liable to fine or to cani…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr332-#pr332-
/// @amendment [15/2019]
statute 332 "Voluntarily causing hurt to deter public servant from his duty" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// Section 332 requires the voluntary causing of hurt to a public servant, plus one of the three statutory duty-related nexuses.
        all_of {
            actus_reus voluntarily_causes_hurt := "Voluntarily causes hurt";
            circumstance person_is_public_servant := "The person to whom hurt is caused is a public servant";

            /// The statute is disjunctive across the three duty-related limbs separated by "or".
            any_of {
                circumstance hurt_caused_in_discharge_of_duty := "The hurt is caused to that person in the discharge of his duty as such public servant";

                all_of {
                    mens_rea intent_to_prevent_or_deter_public_servant := "With intent to prevent or deter that person or any other public servant from discharging his duty as such public servant";
                }

                circumstance hurt_caused_in_conse
```

---

### s333 — Voluntarily causing grievous hurt to deter public servant from his duty

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The canonical punishment includes liability to fine or to caning, but the encoding only models `fine := unlimited` and omits any `caning :=` clause.
- suggested fix: Add an explicit caning branch to the penalty block so the encoded punishment captures both alternatives stated in the statute.

**Canonical text (first 500 chars):**

> Whoever voluntarily causes grievous hurt to any person being a public servant in the discharge of his duty as such public servant, or with intent to prevent or deter that person or any other public servant from discharging his duty as such public servant, or in consequence of anything done or attempted to be done by that person in the lawful discharge of his duty as such public servant, shall be punished with imprisonment for a term which may extend to 15 years, and shall also be liable to fine …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr333-#pr333-

statute 333 "Voluntarily causing grievous hurt to deter public servant from his duty" effective 1872-01-01 {
    elements {
        /// Section 333 requires voluntary causation of grievous hurt to a person who is a public servant, plus one of the three statutory public-duty contexts.
        all_of {
            actus_reus causes_grievous_hurt := "Voluntarily causes grievous hurt";
            circumstance victim_is_public_servant := "To any person being a public servant";

            /// The public-duty nexus is disjunctive because the statute uses repeated "or".
            any_of {
                circumstance discharge_of_duty := "That person is in the discharge of his duty as such public servant";
                mens_rea intent_to_prevent_or_deter := "With intent to prevent or deter that person or any other public servant from discharging his duty as such public servant";
                circumstance consequence_of_lawful_discharge := "In consequence of anything done or attempted to be done by that person in the lawful discharge of his duty as s
```

---

### s365 — Kidnapping or abducting with intent secretly and wrongfully to confine a person

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding fabricates `caning := 0 .. 24 strokes` even though the canonical text states only that the offender is liable "to caning" without any numeric stroke count.
- suggested fix: Remove the invented stroke range and preserve the caning limb without adding a number of strokes.

**Canonical text (first 500 chars):**

> Whoever kidnaps or abducts any person with intent to cause that person to be secretly and wrongfully confined, shall be punished with imprisonment for a term which may extend to 10 years, and shall also be liable to fine or to caning.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr365-#pr365-

statute 365 "Kidnapping or abducting with intent secretly and wrongfully to confine a person" effective 1872-01-01 {
    elements {
        /// Section 365 is conjunctive: the kidnapping or abduction and the stated intent must both be proved.
        all_of {
            actus_reus kidnaps_or_abducts := "Whoever kidnaps or abducts any person";
            mens_rea intent_secret_wrongful_confinement := "With intent to cause that person to be secretly and wrongfully confined";
        }
    }

    penalty cumulative {

        imprisonment := 0 years .. 10 years;
        supplementary := "Whoever kidnaps or abducts any person with intent to cause that person to be secretly and wrongfully confined, shall be punished with imprisonment for a term which may extend to 10 years.";

        alternative {
            fine := unlimited;
            caning := 0 .. 24 strokes;
            supplementary := "The offender shall also be liable to fine or to caning.";
    
        }
    }
}

```

---

### s366 — Kidnapping or abducting a woman to compel her marriage, etc.

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding fabricates `caning := 0 .. 24 strokes` even though the canonical text only makes the offender liable to caning without specifying any numeric stroke count.
- suggested fix: Preserve the caning limb without inventing a number of strokes, and keep the imprisonment-plus-fine-or-caning structure faithful to the statute.

**Canonical text (first 500 chars):**

> Whoever kidnaps or abducts any woman with intent that she may be compelled, or knowing it to be likely that she will be compelled to marry any person against her will, or in order that she may be forced or seduced to illicit intercourse, or to a life of prostitution, or knowing it to be likely that she will be forced or seduced to illicit intercourse, or to a life of prostitution, shall be punished with imprisonment for a term which may extend to 10 years, and shall also be liable to fine or to …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr366-#pr366-

statute 366 "Kidnapping or abducting a woman to compel her marriage, etc." effective 1872-01-01 {
    elements {
        /// Section 366 requires the kidnapping or abduction of a woman plus one of the listed marriage, intercourse, or prostitution purposes or likelihood states.
        all_of {
            actus_reus kidnaps_or_abducts_woman := "Whoever kidnaps or abducts any woman";
            any_of {
                mens_rea intent_compelled_to_marry := "With intent that she may be compelled to marry any person against her will";
                mens_rea knowledge_likely_compelled_to_marry := "Knowing it to be likely that she will be compelled to marry any person against her will";
                mens_rea purpose_forced_or_seduced_to_illicit_intercourse := "In order that she may be forced or seduced to illicit intercourse";
                mens_rea purpose_forced_or_seduced_to_life_of_prostitution := "In order that she may be forced or seduced to a life of prostitution";
                mens_rea knowledge_likely_forced_or_seduced_to_illicit_interco
```

---

### s377BF — Sexual exposure

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: Subsection (4) says the offender "shall also be liable to fine or to caning", but the encoding only models fine structurally and leaves caning as supplementary prose.
- suggested fix: Replace the freeform supplementary sentence in subsection (4) with a structured penalty branch that explicitly encodes caning as an alternative to fine.

**Canonical text (first 500 chars):**

> —(1) Any person ( A ) shall be guilty of an offence who — ( a ) for the purpose of obtaining sexual gratification or of causing another person ( B ) humiliation, alarm or distress, intentionally exposes A ’s genitals; ( b ) intends that B will see A ’s genitals; and ( c ) does so without B ’s consent. (2) Any person ( A ) shall be guilty of an offence who — (3) Subject to subsection (4), a person who is guilty of an offence under subsection (1) or (2) shall on conviction be punished with impriso…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr377BF-#pr377BF-
/// @amendment [15/2019]

statute 377BF "Sexual exposure" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// Subsection (1) is conjunctive: purpose, exposure, intended viewing, and lack of consent must all be proved.
            all_of {
                actus_reus exposure := "For the purpose of obtaining sexual gratification or of causing another person ( B ) humiliation, alarm or distress, A intentionally exposes A’s genitals.";
                mens_rea intended_viewing := "A intends that B will see A’s genitals.";
                circumstance absence_of_consent := "A does so without B’s consent. [15/2019]";
            }
        }
    }

    subsection (2) {
        elements {
            /// Subsection (2) is conjunctive: purpose, intentional distribution of the genital image, intended viewing, and lack of consent must all be proved.
            all_of {
                actus_reus distribution := "For the purpose of obtaining sexual gratification or of causing another person ( B ) humiliation, ala
```

---

### s377BI — Distributing or selling child abuse material

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: Subsection (2) says imprisonment plus liability to fine or to caning, but the encoding models only the fine branch structurally and leaves the caning branch in supplementary text.
- suggested fix: Add a separate caning-liability penalty branch, as used in nearby section encodings, without inventing any stroke count.

**Canonical text (first 500 chars):**

> —(1) Any person shall be guilty of an offence who — ( a ) distributes or sells or offers for sale child abuse material or has in the person’s possession child abuse material for the purpose of such distribution, sale or offer for sale; and ( b ) knows or has reason to believe that the material is child abuse material. (2) A person who is guilty of an offence under subsection (1) shall on conviction be punished with imprisonment for a term which may extend to 7 years, and shall also be liable to …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr377BI-#pr377BI-
/// @amendment [15/2019]
statute 377BI "Distributing or selling child abuse material" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// Subsection (1) is conjunctive overall: one prohibited distribution/sale-possession limb plus knowledge or reason to believe the material is child abuse material.
            all_of {
                any_of {
                    actus_reus distributes_child_abuse_material := "Distributes child abuse material";
                    actus_reus sells_child_abuse_material := "Sells child abuse material";
                    actus_reus offers_child_abuse_material_for_sale := "Offers for sale child abuse material";
                    actus_reus possesses_for_distribution_sale_or_offer := "Has in the person’s possession child abuse material for the purpose of such distribution, sale or offer for sale";
                }
                mens_rea knowledge_or_reason_to_believe := "Knows or has reason to believe that the material is child abuse material. [15/2019]";
           
```

---

### s377BJ — Advertising or seeking child abuse material

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The canonical punishment makes the offender liable to fine or to caning, but the encoding only structures the fine limb and leaves caning in prose instead of an explicit punishment clause.
- suggested fix: Add an explicit caning branch, using `caning := unspecified` if needed, so every canonical punishment option is encoded without inventing a stroke count.

**Canonical text (first 500 chars):**

> —(1) Any person shall be guilty of an offence who — ( a ) for the purposes of distributing or selling or offering for sale any child abuse material advertises the material; and ( b ) knows or has reason to believe that the material is child abuse material. (2) Any person shall be guilty of an offence who — (3) A person who is guilty of an offence under subsection (1) or (2) shall on conviction be punished with imprisonment for a term which may extend to 5 years, and shall also be liable to fine …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr377BJ-#pr377BJ-
/// @amendment [15/2019]

statute 377BJ "Advertising or seeking child abuse material" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// Subsection (1) is conjunctive: the advertising limb and the knowledge limb must both be proved.
            all_of {
                actus_reus advertising_child_abuse_material := "For the purposes of distributing or selling or offering for sale any child abuse material advertises the material";
                mens_rea knowledge_of_child_abuse_material := "Knows or has reason to believe that the material is child abuse material";
            }
        }
    }

    subsection (2) {
        elements {
            /// Subsection (2) is conjunctive: the announced offer limb and the knowledge limb must both be proved.
            all_of {
                actus_reus announcing_offer_to_acquire_buy_or_gain_access := "Announces or otherwise makes known by any means any offer or purported offer to acquire, buy or gain access to any child abuse material";
                mens
```

---

### s385 — Putting person in fear of harm in order to commit extortion

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The canonical text expressly requires caning, but the encoding preserves that punishment only in `supplementary` prose instead of as a structured `caning` penalty fact.
- suggested fix: Replace the prose-only caning sentence with an explicit caning punishment entry, using an unspecified form if the statute gives no stroke count.

**Canonical text (first 500 chars):**

> Whoever, in order to commit extortion, puts or attempts to put any person in fear of any harm to that person or to any other person, in body, mind, reputation or property, whether such harm is to be caused legally or illegally, shall be punished with imprisonment for a term of not less than 2 years and not more than 5 years and with caning.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr385-#pr385-

statute 385 "Putting person in fear of harm in order to commit extortion" effective 1872-01-01 {
    elements {
        /// The offence is conjunctive: extortion purpose plus the fear-inducing conduct plus the statutory harm scope.
        all_of {
            mens_rea extortion_purpose := "In order to commit extortion";
            actus_reus putting_or_attempting_to_put_in_fear := "Puts or attempts to put any person in fear";
            circumstance harm_scope := "Fear of any harm to that person or to any other person, in body, mind, reputation or property, whether such harm is to be caused legally or illegally";
        }
    }

    penalty cumulative {
        imprisonment := 2 years .. 5 years;
        supplementary := "The offender shall be punished with caning.";
    }
}

```

---

### s387 — Putting person in fear of death or of grievous hurt in order to commit extortion

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding omits a structured caning punishment even though the canonical text expressly requires punishment "with caning", and the repo now supports `caning := unspecified` for non-numeric caning terms.
- suggested fix: Add an explicit `caning := unspecified` punishment entry so the mandatory caning limb is preserved structurally instead of only in supplementary prose.

**Canonical text (first 500 chars):**

> Whoever, in order to commit extortion, puts or attempts to put any person in fear of death or of grievous hurt to that person or to any other, shall be punished with imprisonment for a term of not less than 2 years and not more than 7 years and with caning.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr387-#pr387-

statute 387 "Putting person in fear of death or of grievous hurt in order to commit extortion" effective 1872-01-01 {
    elements {
        all_of {
            mens_rea extortion_purpose := "In order to commit extortion";
            actus_reus threat_conduct := "Puts or attempts to put any person in fear";
            circumstance aggravated_fear := "Fear of death or of grievous hurt to that person or to any other";
        }
    }

    penalty cumulative {
        imprisonment := 2 years .. 7 years;
        supplementary := "Whoever, in order to commit extortion, puts or attempts to put any person in fear of death or of grievous hurt to that person or to any other, shall be punished with imprisonment for a term of not less than 2 years and not more than 7 years and with caning.";
    }
}

```

---

### s393 — Attempt to commit robbery

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding preserves the mandatory caning limb only in `supplementary` prose even though the canonical text expressly requires punishment with caning of not less than 6 strokes.
- suggested fix: Add an explicit caning punishment entry and keep the statutory minimum-strokes language in supplementary text so the caning limb is preserved structurally without inventing a ceiling.

**Canonical text (first 500 chars):**

> Whoever attempts to commit robbery shall be punished with imprisonment for a term of not less than 2 years and not more than 7 years and shall also be punished with caning with not less than 6 strokes.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr393-#pr393-

referencing penal_code/s390_robbery

statute 393 "Attempt to commit robbery" effective 1872-01-01 {
    definitions {
        robbery := "Robbery as defined in section 390.";
        attempt_to_commit_robbery := "Attempting to commit robbery.";
    }

    elements {
        all_of {
            /// the prohibited conduct is an attempt to commit the cross-referenced robbery offence
            actus_reus attempt := "Attempts to commit robbery" burden prosecution beyond_reasonable_doubt;
            circumstance target_offence := "The offence attempted is robbery under section 390";
        }
    }

    penalty cumulative {
        imprisonment := 2 years .. 7 years;
        supplementary := "The offender shall also be punished with caning with not less than 6 strokes.";
    }
}

```

---

### s400 — Punishment for belonging to gang-robbers

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoded penalty omits the canonical life-imprisonment branch and adds a structured caning maximum of 24 strokes even though the statute only states not less than 6 strokes.
- suggested fix: Re-encode the punishment so the life-imprisonment alternative is explicit and the caning clause preserves only the statutory minimum unless another canonical source supplies a maximum.

**Canonical text (first 500 chars):**

> Whoever shall belong to a gang of persons associated for the purpose of habitually committing gang‑robbery, shall be punished with imprisonment for life, or with imprisonment for a term which may extend to 10 years, and shall also be punished with caning with not less than 6 strokes.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr400-#pr400-

referencing penal_code/s391_gang_robbery

statute 400 "Punishment for belonging to gang-robbers" effective 1872-01-01 {
    definitions {
        gang_robbery := "Gang-robbery as defined in section 391.";
    }

    elements {
        /// The section is conjunctive: belonging to the gang and the gang's habitual gang-robbery purpose must both be proved.
        all_of {
            actus_reus belongs_to_gang := "Belongs to a gang of persons";
            circumstance gang_purpose := "The gang is associated for the purpose of habitually committing gang-robbery";
        }
    }

    penalty alternative {
        imprisonment := 0 days .. 10 years;
        supplementary := "Whoever shall belong to a gang of persons associated for the purpose of habitually committing gang‑robbery, shall be punished with imprisonment for life, or with imprisonment for a term which may extend to 10 years.";
    }

    penalty cumulative {
        caning := 6 .. 24 strokes;
        supplementary := "The offender shall also be punished with caning with not less than 6 strokes.
```

---

### s407 — Criminal breach of trust of property entrusted for purposes of transportation or storage

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The penalty block makes the fine optional by nesting it under `alternative {}` even though the canonical text requires imprisonment and fine cumulatively ("and shall also be liable to fine").
- suggested fix: Encode the fine as a direct cumulative penalty alongside the imprisonment term, without an `alternative {}` wrapper.

**Canonical text (first 500 chars):**

> Whoever, being entrusted with property for the purpose of transportation for hire or storage for rent or charge, commits criminal breach of trust in respect of such property, shall be punished with imprisonment for a term which may extend to 15 years, and shall also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr407-#pr407-
/// @amendment [15/2019]

statute 407 "Criminal breach of trust of property entrusted for purposes of transportation or storage" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// Section 407 is conjunctive: qualifying entrustment plus criminal breach of trust of that property.
        all_of {
            any_of {
                circumstance entrusted_for_transportation_for_hire := "Being entrusted with property for the purpose of transportation for hire";
                circumstance entrusted_for_storage_for_rent_or_charge := "Being entrusted with property for the purpose of storage for rent or charge";
            }

            actus_reus criminal_breach_of_trust := "Commits criminal breach of trust in respect of such property";
        }
    }

    penalty cumulative {

        imprisonment := 0 years .. 15 years;
        supplementary := "Whoever, being entrusted with property for the purpose of transportation for hire or storage for rent or charge, commits criminal breach of trust in respect of such property, shall be punish
```

---

### s438 — Punishment for the mischief described in section 437 when committed by fire or any explosive substance

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The encoding leaves the statute’s imprisonment-for-life alternative only in supplementary prose instead of preserving it as a structured penalty branch, so the punishment is not faithfully captured.
- suggested fix: Encode imprisonment for life as an explicit structured alternative alongside the up-to-10-years branch, while retaining the conditional unlimited fine for non-life sentences.

**Canonical text (first 500 chars):**

> Whoever commits or attempts to commit by fire or any explosive substance, such mischief as is described in section 437, shall be punished with imprisonment for life, or with imprisonment for a term which may extend to 10 years, and shall, if he is not sentenced to imprisonment for life, also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr438-#pr438-
/// @amendment [15/2019]

referencing penal_code/s437_mischief_intent_destroy_make_unsafe_decked

statute 438 "Punishment for the mischief described in section 437 when committed by fire or any explosive substance" effective 1872-01-01 effective 2019-12-31 {
    /// Punishment for the predicate offence in section 437 where the offender commits or attempts to commit that mischief by fire or any explosive substance.
    penalty alternative {
        imprisonment := 0 days .. 10 years;
        supplementary := "Whoever commits or attempts to commit by fire or any explosive substance, such mischief as is described in section 437, shall be punished with imprisonment for life, or with imprisonment for a term which may extend to 10 years. [15/2019]";
    }

    penalty when non_life_sentence {
        fine := unlimited;
        supplementary := "The offender shall, if he is not sentenced to imprisonment for life, also be liable to fine. [15/2019]";
    }
}

```

---

### s447 — Punishment for criminal trespass

**Verdict:** `INVESTIGATE` — penalty discrepancy needs side-by-side comparison

**Flag** (check 7):
- reason: The canonical text makes the fine discretionary up to $1,500, but the encoding fixes it at exactly `$1,500.00`, which fabricates the penalty ceiling into a mandatory amount.
- suggested fix: Change the fine encoding to a capped range that preserves "may extend to $1,500" rather than a fixed sum.

**Canonical text (first 500 chars):**

> Whoever commits criminal trespass shall be punished with imprisonment for a term which may extend to 3 months, or with fine which may extend to $1,500, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr447-#pr447-

referencing penal_code/s441_criminal_trespass

statute 447 "Punishment for criminal trespass" effective 1872-01-01 {
    /// Punishment for the offence of criminal trespass under section 441.
    penalty or_both {
        imprisonment := 0 days .. 3 months;
        fine := $1,500.00;
    }
}

```

---

