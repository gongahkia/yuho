# L3 flags — failed check 938 sections in this group.---### s26D — “Knowingly”

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding omits the earlier commencement date for material tagged `[15/2019]` and only records `effective 2020-02-10`, so the effective-date history is incomplete.
- suggested fix: Add the missing amendment commencement date (likely `2019-12-31`) alongside `2020-02-10` after confirming it against the section’s amendment history.

**Canonical text (first 500 chars):**

> —(1) Whoever does an act with awareness that a circumstance exists, will exist, or is virtually certain (barring an unforeseen intervention) to exist, is said to do that act knowingly in respect of that circumstance. (2) Whoever does an act with awareness that an effect will be caused, or is virtually certain (barring an unforeseen intervention) to be caused, is said to do that act knowingly in respect of that effect. (3) Where doing an act knowingly is a fault element of an offence, that fault …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr26D-#pr26D-
/// @amendment [15/2019]
/// @amendment [15/2019; 2/2020]

statute 26D "“Knowingly”" effective 1872-01-01 effective 2020-02-10 {
    subsection (1) {
        definitions {
            knowingly_circumstance := "Whoever does an act with awareness that a circumstance exists, will exist, or is virtually certain (barring an unforeseen intervention) to exist, is said to do that act knowingly in respect of that circumstance. [15/2019]";
        }
    }

    subsection (2) {
        definitions {
            knowingly_effect := "Whoever does an act with awareness that an effect will be caused, or is virtually certain (barring an unforeseen intervention) to be caused, is said to do that act knowingly in respect of that effect. [15/2019]";
        }
    }

    subsection (3) {
        definitions {
            knowingly_fault_element := "Where doing an act knowingly is a fault element of an offence, that fault element is also established where that act is done intentionally or with wilful blindness. [15/2019; 2/2020]";
        }
    }
}

```

---

### s29B — “Electronic record”

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding uses only `effective 1872-01-01`, but section 29B was introduced later, with external legislative history indicating Act 51 of 2007 commenced on 1 February 2008.
- suggested fix: Add the later commencement date as an `effective` clause after confirming the source amendment metadata for section 29B.

**Canonical text (first 500 chars):**

> The expression “electronic record” has the same meaning as in the Electronic Transactions Act 2010.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr29B-#pr29B-

statute 29B "“Electronic record”" effective 1872-01-01 {
    definitions {
        electronic_record := "has the same meaning as in the Electronic Transactions Act 2010";
    }
}

```

---

### s76 — Act done by person bound, or justified by law

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding includes amendment marker `[15/2019]` but only declares `effective 1872-01-01`, so it omits a later effective date required by the checklist.
- suggested fix: Add the correct post-amendment effective date for the `[15/2019]` revision as an `effective` clause in `statute.yh`.

**Canonical text (first 500 chars):**

> Nothing is an offence which is done by a person who is bound by law to do it or justified by law in doing it.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr76-#pr76-
/// @amendment [15/2019]
statute 76 "Act done by person bound, or justified by law" effective 1872-01-01 {
    definitions {
        no_offence_rule := "Nothing is an offence which is done by a person who is bound by law to do it or justified by law in doing it.";
        bound_by_law := "done by a person who is bound by law to do it";
        justified_by_law := "done by a person who is justified by law in doing it";
    }

    elements {
        /// The statutory protection is disjunctive: bound by law, or justified by law.
        any_of {
            circumstance bound_by_law := "done by a person who is bound by law to do it";
            circumstance justified_by_law := "done by a person who is justified by law in doing it";
        }
    }

    exception no_offence {
        "Nothing is an offence which is done by a person who is bound by law to do it or justified by law in doing it."
        "No offence"
    }

    illustration illustration_a {
        "( a ) A , a soldier, fires on a mob by the order of his superior officer, in conformity with the
```

---

### s97 — Right of private defence of the body and of property

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding is tagged with amendment marker `[15/2019]` but the statute header only has `effective 1872-01-01`, so the post-2019 amendment date is missing.
- suggested fix: Add the 2019 amendment effective date used for the surrounding private-defence sections instead of leaving section 97 with only the original 1872 date.

**Canonical text (first 500 chars):**

> Every person has a right, subject to the restrictions contained in sections 98 and 106A, to defend — ( a ) his own body, and the body of any other person, against any offence affecting the human body; ( b ) the property, whether movable or immovable, of himself or of any other person, against any act which is an offence falling under the definition of theft, robbery, mischief or criminal trespass, or which is an attempt to commit theft, robbery, mischief or criminal trespass.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr97-#pr97-
/// @amendment [15/2019]

statute 97 "Right of private defence of the body and of property" effective 1872-01-01 {
    definitions {
        private_defence_body := "Every person has a right, subject to the restrictions contained in sections 98 and 106A, to defend his own body, and the body of any other person, against any offence affecting the human body.";
        private_defence_property := "Every person has a right, subject to the restrictions contained in sections 98 and 106A, to defend the property, whether movable or immovable, of himself or of any other person, against any act which is an offence falling under the definition of theft, robbery, mischief or criminal trespass, or which is an attempt to commit theft, robbery, mischief or criminal trespass.";
    }
}

```

---

### s99 — Right of private defence against act of person of unsound mind, etc.

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while Act 15 of 2019 entered into force on 2020-01-01, so the effective-date encoding is not sane.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.

**Canonical text (first 500 chars):**

> When an act, which would otherwise be a certain offence, is not that offence, by reason of the youth, the want of maturity of understanding, the unsoundness of mind, or the intoxication of the person doing that act, or by reason of any misconception on the part of that person, every person has the same right of private defence against that act which he would have if the act were that offence.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr99-#pr99-
/// @amendment [15/2019]

statute 99 "Right of private defence against act of person of unsound mind, etc." effective 1872-01-01 effective 2019-12-31 {
    definitions {
        private_defence_against_act_not_offence_due_to_actor_status := "When an act, which would otherwise be a certain offence, is not that offence, by reason of the youth, the want of maturity of understanding, the unsoundness of mind, or the intoxication of the person doing that act, or by reason of any misconception on the part of that person, every person has the same right of private defence against that act which he would have if the act were that offence. [15/2019]";
    }

    illustration illustration_a {
        "( a ) Z , under the influence of madness, attempts to kill A . Z is guilty of no offence. But A has the same right of private defence which he would have if Z were sane."
    }

    illustration illustration_b {
        "( b ) A enters, by night, a house which he is legally entitled to enter. Z , in good faith, taking A for a housebreaker, attacks A . Here Z , by attac
```

---

### s106 — When such right extends to causing any harm other than death

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.

**Canonical text (first 500 chars):**

> If the offence, the committing or the attempt to commit of which occasions the exercise of the right of private defence, is theft, mischief, or criminal trespass, not of any of the descriptions mentioned in section 105, that right does not extend to the voluntary causing of death, but does extend, subject to the restrictions mentioned in sections 98 and 106A, to the voluntary causing to the wrongdoer of any harm other than death.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr106-#pr106-
/// @amendment [15/2019]

statute 106 "When such right extends to causing any harm other than death" effective 1872-01-01 effective 2019-12-31 {
    definitions {
        scope_of_nonfatal_private_defence_of_property := "If the offence, the committing or the attempt to commit of which occasions the exercise of the right of private defence, is theft, mischief, or criminal trespass, not of any of the descriptions mentioned in section 105, that right does not extend to the voluntary causing of death, but does extend, subject to the restrictions mentioned in sections 98 and 106A, to the voluntary causing to the wrongdoer of any harm other than death. [15/2019]";
    }
}

```

---

### s108B — Abetment outside Singapore of an offence in Singapore

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding uses only `effective 1872-01-01`, but section 108B was introduced by Act 51 of 2007, which commenced on 2008-02-01, so the effective-date encoding is not sane.
- suggested fix: Replace or supplement the generic commencement with an `effective 2008-02-01` clause after confirming the section’s amendment history.

**Canonical text (first 500 chars):**

> A person abets an offence within the meaning of this Code who abets an offence committed in Singapore notwithstanding that any or all of the acts constituting the abetment were done outside Singapore.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr108B-#pr108B-

statute 108B "Abetment outside Singapore of an offence in Singapore" effective 1872-01-01 {
    elements {
        all_of {
            actus_reus abets_offence_in_singapore := "Abets an offence committed in Singapore";
            circumstance abetment_acts_done_outside_singapore := "Any or all of the acts constituting the abetment were done outside Singapore";
        }
    }
}

```

---

### s121B — Offences against authority

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoded statute uses `effective 2020-01-01` for a section marked `[15/2019]`, and I could not verify that as the correct amendment commencement date for section 121B.
- suggested fix: Verify the actual commencement date for the Act 15 of 2019 amendment affecting section 121B and replace the current `effective` date if needed.

**Canonical text (first 500 chars):**

> Whoever plans the unlawful deprivation or deposition of the President from the sovereignty of Singapore, or the overawing by criminal force of the Government, shall be punished with imprisonment for life or for a term which may extend to 20 years and shall, if he is not sentenced to imprisonment for life, also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr121B-#pr121B-
/// @amendment [15/2019]

statute 121B "Offences against authority" effective 1872-01-01 effective 2020-01-01 {
    elements {
        all_of {
            actus_reus planning := "Plans";
            any_of {
                circumstance deprivation_or_deposition := "The unlawful deprivation or deposition of the President from the sovereignty of Singapore";
                circumstance overawing_government := "The overawing by criminal force of the Government";
            }
        }
    }

    penalty alternative when life_sentence {
        supplementary := "Imprisonment for life.";
    }

    penalty cumulative when term_sentence {
        imprisonment := 0 days .. 20 years;
        fine := unlimited;
        supplementary := "If the offender is not sentenced to imprisonment for life, the offender is also liable to fine.";
    }
}

```

---

### s130A — “Harbour”

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding uses only `effective 1872-01-01`, but section 130A appears to have been introduced later and external consolidation history shows `[51/2007]`.
- suggested fix: Add an effective date reflecting the amending Act that introduced section 130A, then re-run L3 review.

**Canonical text (first 500 chars):**

> In this Chapter, “harbour” includes the supplying a person with shelter, food, drink, money, clothes, arms, ammunition, or means of conveyance, or the assisting a person in any way to evade apprehension.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr130A-#pr130A-

statute 130A "“Harbour”" effective 1872-01-01 {
    definitions {
        harbour := "In this Chapter, “harbour” includes the supplying a person with shelter, food, drink, money, clothes, arms, ammunition, or means of conveyance, or the assisting a person in any way to evade apprehension.";
    }
}

```

---

### s130B — Piracy by law of nations. Cf. 12 and 13 Victoria c. 96 (Admiralty Offences (Colonial) Act 1849)

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: Section 130B is a later inserted section number, but the encoding uses only `effective 1872-01-01`, so the effective date is not sane on the present record.
- suggested fix: Verify the insertion commencement date from Singapore Statutes Online legislative history and add that later effective date before stamping.

**Canonical text (first 500 chars):**

> —(1) A person commits piracy who does any act that, by the law of nations, is piracy. (2) Whoever commits piracy shall be punished with imprisonment for life and with caning with not less than 12 strokes, but if while committing or attempting to commit piracy he murders or attempts to murder another person or does any act that is likely to endanger the life of another person he shall be punished with death.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr130B-#pr130B-

statute 130B "Piracy by law of nations. Cf. 12 and 13 Victoria c. 96 (Admiralty Offences (Colonial) Act 1849)" effective 1872-01-01 {
    subsection (1) {
        elements {
            /// The offence is defined by the law of nations test in subsection (1).
            all_of {
                actus_reus does_act := "Does any act";
                circumstance piracy_by_law_of_nations := "That act, by the law of nations, is piracy";
            }
        }
    }

    subsection (2) {
        elements {
            actus_reus commits_piracy := "Commits piracy";
            circumstance aggravated_piracy := "While committing or attempting to commit piracy, the offender murders or attempts to murder another person or does any act that is likely to endanger the life of another person";
        }

        penalty cumulative {
            supplementary := "Whoever commits piracy shall be punished with imprisonment for life and with caning with not less than 12 strokes.";
        }

        penalty when aggravated_piracy {
            death := TRUE;
      
```

---

### s130C — Piratical acts

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding uses only `effective 1872-01-01`, but section 130C is a later inserted provision and therefore needs an amending-act effective date rather than the generic base date alone.
- suggested fix: Add an effective date for the amendment that introduced section 130C, then re-run L3 review.

**Canonical text (first 500 chars):**

> Whoever, while in or out of Singapore — ( a ) steals a Singapore ship; ( b ) steals or without lawful authority throws overboard, damages or destroys anything that is part of the cargo, supplies or fittings in a Singapore ship; ( c ) does or attempts to do a mutinous act on a Singapore ship; or ( d ) counsels or procures a person to do anything mentioned in paragraph ( a ), ( b ) or ( c ), shall be punished with imprisonment for a term not exceeding 15 years and shall be liable to caning.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr130C-#pr130C-

statute 130C "Piratical acts" effective 1872-01-01 {
    elements {
        all_of {
            circumstance location := "While in or out of Singapore";
            any_of {
                actus_reus paragraph_a := "Steals a Singapore ship";
                actus_reus paragraph_b := "Steals or without lawful authority throws overboard, damages or destroys anything that is part of the cargo, supplies or fittings in a Singapore ship";
                actus_reus paragraph_c := "Does or attempts to do a mutinous act on a Singapore ship";
                actus_reus paragraph_d := "Counsels or procures a person to do anything mentioned in paragraph (a), (b) or (c)";
            }
        }
    }

    penalty cumulative {
        imprisonment := 0 years .. 15 years;
        supplementary := "Shall be liable to caning.";
    }
}

```

---

### s137 — Deserter concealed on board merchant vessel through negligence of master

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent treats Act 15 of 2019 commencement as `2020-01-01`, so the effective-date encoding is not sane.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.

**Canonical text (first 500 chars):**

> The master or person in charge of a merchant vessel, on board of which any deserter from the Singapore Armed Forces or any visiting forces lawfully present in Singapore is concealed, shall, though ignorant of such concealment, be punished with a fine not exceeding $1,500, if he might have known of such concealment, but for some neglect of his duty as such master or person in charge, or but for some want of discipline on board of the vessel.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr137-#pr137-
/// @amendment [15/2019]
statute 137 "Deserter concealed on board merchant vessel through negligence of master" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// the offence requires the concealed person to be on board the merchant vessel under the accused's charge
        all_of {
            actus_reus concealment_on_board := "A deserter from the Singapore Armed Forces or any visiting forces lawfully present in Singapore is concealed on board a merchant vessel";
            circumstance accused_status := "The accused is the master or person in charge of that merchant vessel";
            circumstance ignorance := "The accused is ignorant of that concealment";
            any_of {
                circumstance neglect_of_duty := "The accused might have known of that concealment but for some neglect of his duty as such master or person in charge";
                circumstance want_of_discipline := "The accused might have known of that concealment but for some want of discipline on board of the vessel";
            }
        }
    }


```

---

### s157 — Harbouring persons hired for an unlawful assembly

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoded statute uses `effective 2019-12-31` for a provision marked `[15/2019]`, and I could not certify that as the correct commencement date for the section.
- suggested fix: Confirm the actual commencement date for the section 157 amendment under Act 15 of 2019 and replace the unsupported effective date before restamping.

**Canonical text (first 500 chars):**

> Whoever harbours, receives or assembles in any house or premises in his occupation or charge, or under his control, any persons, knowing that such persons have been hired, engaged or employed, or are about to be hired, engaged or employed, to join or become members of an unlawful assembly, with the intention of permitting or facilitating them to join or become members of an unlawful assembly, or of screening them or any of them from punishment, shall be punished with imprisonment for a term whic…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr157-#pr157-
/// @amendment [15/2019]

statute 157 "Harbouring persons hired for an unlawful assembly" effective 1872-01-01 effective 2019-12-31 {
    elements {
        all_of {
            actus_reus harbouring_receiving_or_assembling := "Harbours, receives or assembles any persons in any house or premises";
            circumstance premises_control := "That house or premises is in his occupation or charge, or under his control";
            mens_rea knowledge := "Knowing that such persons have been hired, engaged or employed, or are about to be hired, engaged or employed, to join or become members of an unlawful assembly";
            mens_rea intention := "With the intention of permitting or facilitating them to join or become members of an unlawful assembly, or of screening them or any of them from punishment";
        }
    }

    penalty or_both {
        imprisonment := 0 days .. 2 years;
        fine := unlimited;
    }
}

```

---

### s166 — Public servant disobeying a direction of the law, with intent to cause injury to any person

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[Act 25 of 2021 wef 01/04/2022]` but the statute header encodes only `effective 1872-01-01`, so the later operative date is missing.
- suggested fix: Add `effective 2022-04-01` to the statute header while preserving the original `effective 1872-01-01`.

**Canonical text (first 500 chars):**

> Whoever, being a public servant, knowingly disobeys any direction of the law as to the way in which he is to conduct himself as such public servant, intending to cause, or knowing it to be likely that he will, by such disobedience, cause injury to any person, shall be punished with imprisonment for a term which may extend to one year, or with fine, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr166-#pr166-
/// @amendment [Act 25 of 2021 wef 01/04/2022]

statute 166 "Public servant disobeying a direction of the law, with intent to cause injury to any person" effective 1872-01-01 {
    elements {
        all_of {
            circumstance public_servant_status := "Whoever, being a public servant";
            actus_reus disobedience_of_direction := "Knowingly disobeys any direction of the law as to the way in which he is to conduct himself as such public servant";
            mens_rea injury_intent_or_knowledge := "Intending to cause, or knowing it to be likely that he will, by such disobedience, cause injury to any person";
        }
    }

    penalty or_both {
        imprisonment := 0 days .. 1 years;
        fine := unlimited;
    }

    illustration illustration {
        "A , being an officer directed by law to take property under or pursuant to an enforcement order, or in execution in order to satisfy a decree, pronounced in Z ’s favour by a court of justice, knowingly disobeys that direction of law, with the knowledge that he is likely thereby to ca
```

---

### s175 — Omission to produce document or electronic record to public servant by person legally bound to produce such document or electronic record

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.

**Canonical text (first 500 chars):**

> A person who, being legally bound to produce or deliver up any document or electronic record to any public servant, as such, intentionally omits so to produce or deliver up the same, shall — ( a ) in the case of an individual, be punished with imprisonment for a term which may extend to one month, or with fine which may extend to $1,500, or with both; or ( b ) in any other case, be punished with fine which may extend to $10,000.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr175-#pr175-
/// @amendment [15/2019]

statute 175 "Omission to produce document or electronic record to public servant by person legally bound to produce such document or electronic record" effective 1872-01-01 effective 2019-12-31 {
    definitions {
        document_or_electronic_record := "Any document or electronic record which the person is legally bound to produce or deliver up to any public servant, as such. [15/2019]";
    }

    elements {
        /// Section 175 requires the legal duty, the public-servant recipient, the omission to produce or deliver up, and intentionality.
        all_of {
            circumstance legal_duty := "The person is legally bound to produce or deliver up a document or electronic record to any public servant, as such. [15/2019]";
            actus_reus omission := "The person omits to produce or deliver up the same. [15/2019]";
            mens_rea intentional_omission := "The omission is intentional. [15/2019]";
            /// Paragraphs (a) and (b) split punishment by offender type.
            any_of {
                circum
```

---

### s179 — Refusing to answer public servant authorised to question

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[15/2019]` but the encoding uses only `effective 1872-01-01`, so the effective-date encoding is not sane.
- suggested fix: Add the verified commencement date for the `[15/2019]` amendment as an additional `effective` clause before restamping.

**Canonical text (first 500 chars):**

> A person who, being legally bound to state the truth on any subject to any public servant, refuses to answer any question demanded of the person touching that subject by that public servant, in the exercise of the legal powers of such public servant, shall — ( a ) in the case of an individual, be punished with imprisonment for a term which may extend to 6 months, or with fine which may extend to $5,000, or with both; or ( b ) in any other case, be punished with fine which may extend to $10,000.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr179-#pr179-
/// @amendment [15/2019]
statute 179 "Refusing to answer public servant authorised to question" effective 1872-01-01 {
    elements {
        /// The offence requires a legal duty to state the truth, refusal to answer a demanded question touching that subject, and that the demand is made by a public servant exercising legal powers.
        all_of {
            circumstance legal_truth_duty := "Being legally bound to state the truth on any subject to any public servant";
            actus_reus refusal_to_answer := "Refuses to answer any question demanded of the person touching that subject";
            circumstance authorised_questioning := "The question is demanded by that public servant, in the exercise of the legal powers of such public servant";
            /// The amended text separates punishment between cases involving an individual and any other case.
            any_of {
                circumstance individual_case := "The case is the case of an individual";
                circumstance other_case := "The case is any other case";
            }

```

---

### s183 — Resistance to taking of property by lawful authority of public servant

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoded section is tagged with amendment `[15/2019]` but lists only `effective 1872-01-01`, so it omits a later amendment effective date required by the checklist.
- suggested fix: Add the applicable later effective date for the 2019 amendment to the statute header, consistent with the canonical amendment history and nearby amended sections.

**Canonical text (first 500 chars):**

> A person who offers any resistance to the taking of any property by the lawful authority of any public servant, knowing or having reason to believe that the person is such public servant, shall — ( a ) in the case of an individual, be punished with imprisonment for a term which may extend to 6 months, or with fine which may extend to $5,000, or with both; or ( b ) in any other case, be punished with fine which may extend to $10,000.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr183-#pr183-
/// @amendment [15/2019]

statute 183 "Resistance to taking of property by lawful authority of public servant" effective 1872-01-01 {
    elements {
        /// Section 183 requires resistance to a lawful taking of property by a public servant, with knowledge or reason to believe that status.
        all_of {
            actus_reus resistance := "Offers any resistance to the taking of any property";
            circumstance lawful_authority := "The taking of the property is by the lawful authority of a public servant";
            mens_rea knowledge_of_status := "Knowing or having reason to believe that the person is such public servant";
            /// The amended text separates punishment between the case of an individual and any other case.
            any_of {
                circumstance individual_case := "The case is the case of an individual";
                circumstance other_case := "The case is any other case";
            }
        }
    }

    /// Paragraph (a): in the case of an individual.
    penalty or_both when individual_case {
    
```

---

### s186 — Obstructing public servant in discharge of his public functions

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding uses `effective 2019-12-31` for the `[15/2019]` amendment, but repo-local precedent for comparable Penal Code sections points to `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Confirm the actual commencement date for the Act 15 of 2019 amendment to section 186 and update the `effective` clause accordingly before restamping.

**Canonical text (first 500 chars):**

> —(1) A person who voluntarily obstructs any public servant in the discharge of the public servant’s public functions, shall — ( a ) in the case of an individual, be punished with imprisonment for a term which may extend to 6 months, or with fine which may extend to $2,500, or with both; or ( b ) in any other case, be punished with fine which may extend to $10,000. (2) For the purposes of this section, an obstruction may be caused other than by the use of physical means or threatening language by…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr186-#pr186-
/// @amendment [Act 23 of 2021 wef 01/03/2022]
/// @amendment [15/2019]

statute 186 "Obstructing public servant in discharge of his public functions" effective 1872-01-01 effective 2019-12-31 effective 2022-03-01 {
    subsection (1) {
        elements {
            /// Subsection (1) requires voluntary obstruction, the target being a public servant, the public-function context, and the applicable case-category for punishment.
            all_of {
                mens_rea voluntary := "A person voluntarily obstructs";
                actus_reus obstructs_public_servant := "Any public servant";
                circumstance discharge_of_public_functions := "In the discharge of the public servant’s public functions";
                any_of {
                    circumstance individual_case := "In the case of an individual";
                    circumstance other_case := "In any other case";
                }
            }
        }

        penalty or_both when individual_case {
            imprisonment := 0 days .. 6 months;
            fine := $0.00 .. 
```

---

### s204B — Bribery of witnesses

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding uses only `effective 1872-01-01` for a lettered section `204B`, so the effective-date sanity check cannot be certified without confirming the later insertion date from source history.
- suggested fix: Confirm the actual commencement date for section 204B from SSO or legislative history and add it as an `effective` clause if the section was introduced later.

**Canonical text (first 500 chars):**

> —(1) Whoever — ( a ) gives, confers, or procures, promises or offers to give, confer, or procure or attempts to procure, any gratification to, upon, or for any person, upon any agreement or understanding that any person who is aware of any offence (being an offence which any person is legally bound to give information respecting that offence) will abstain from reporting that offence to the police or any agency charged by law with the duty of investigating offences; ( b ) gives, confers, or procu…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr204B-#pr204B-

statute 204B "Bribery of witnesses" effective 1872-01-01 {
    subsection (1) {
        elements {
            /// Subsection (1) creates four alternative bribery-of-witnesses limbs.
            any_of {
                all_of {
                    actus_reus gratification_for_non_reporting := "Gives, confers, or procures, promises or offers to give, confer, or procure or attempts to procure, any gratification to, upon, or for any person";
                    circumstance non_reporting_agreement := "Upon any agreement or understanding that any person who is aware of any offence will abstain from reporting that offence to the police or any agency charged by law with the duty of investigating offences";
                    circumstance legally_bound_information_offence := "The offence is an offence which any person is legally bound to give information respecting that offence.";
                }
                all_of {
                    actus_reus gratification_for_false_testimony := "Gives, confers, or procures, promises or offers to give, confer, 
```

---

### s267B — Punishment for committing affray

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding uses only `effective 1872-01-01`, but section 267B is an inserted later section and I could not verify a sane later commencement date from the local sources.
- suggested fix: Confirm the actual insertion commencement date from Singapore Statutes Online legislative history and add it as an `effective` clause before restamping.

**Canonical text (first 500 chars):**

> Whoever commits an affray shall be punished with imprisonment for a term which may extend to one year, or with fine which may extend to $5,000, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr267B-#pr267B-

statute 267B "Punishment for committing affray" effective 1872-01-01 {
    /// Punishment for committing an affray; see section 267A for the underlying offence.
    penalty or_both {
        imprisonment := 0 days .. 1 year;
        fine := $0.00 .. $5,000.00;
    }
}

```

---

### s292A — Possession, distribution, etc., of child sex-doll

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent treats Act 15 of 2019 commencement as `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Verify the commencement date for section 292A under Act 15 of 2019 and replace the later `effective` clause with the confirmed date before restamping.

**Canonical text (first 500 chars):**

> —(1) Any person who imports, exports, conveys, sells, lets to hire, distributes, puts into circulation, makes, produces or is in possession of a child sex-doll shall be guilty of an offence and shall on conviction be punished with imprisonment for a term which may extend to 2 years, or with fine, or with both. (2) In subsection (1), “child sex-doll” means an anatomically correct doll, mannequin or robot, with the features of, or with features that appear to a reasonable observer to resemble a pe…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr292A-#pr292A-
/// @amendment [15/2019]

statute 292A "Possession, distribution, etc., of child sex-doll" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// Subsection (1) requires the item to be a child sex-doll and any one prohibited dealing with that item.
            all_of {
                circumstance child_sex_doll := "The item is a child sex-doll.";
                /// The listed dealings are alternative physical acts joined by "or".
                any_of {
                    actus_reus import_child_sex_doll := "Imports a child sex-doll.";
                    actus_reus export_child_sex_doll := "Exports a child sex-doll.";
                    actus_reus convey_child_sex_doll := "Conveys a child sex-doll.";
                    actus_reus sell_child_sex_doll := "Sells a child sex-doll.";
                    actus_reus let_to_hire_child_sex_doll := "Lets to hire a child sex-doll.";
                    actus_reus distribute_child_sex_doll := "Distributes a child sex-doll.";
                    actus_reus put_in
```

---

### s294 — Obscene acts

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The statute is tagged with amendment marker `[15/2019]` but the encoding uses only `effective 1872-01-01`, which fails the amended-section effective-date requirement.
- suggested fix: Add the amendment commencement date as an `effective` clause alongside any historical baseline date if the section remained in force through amendment.

**Canonical text (first 500 chars):**

> Whoever, to the annoyance of others — ( a ) does any obscene act in any public place; or ( b ) sings, recites or utters any obscene words in or near any public place, shall be punished with imprisonment for a term which may extend to 3 months, or with fine, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr294-#pr294-
/// @amendment [15/2019]

statute 294 "Obscene acts" effective 1872-01-01 {
    elements {
        /// Section 294 requires annoyance of others and one of the two obscene public-place acts.
        all_of {
            circumstance annoyance_of_others := "To the annoyance of others";
            any_of {
                actus_reus obscene_act_public_place := "Does any obscene act in any public place";
                actus_reus obscene_words_public_place := "Sings, recites or utters any obscene words in or near any public place";
            }
        }
    }

    penalty or_both {
        imprisonment := 0 days .. 3 months;
        fine := unlimited;
    }
}

```

---

### s301 — Culpable homicide by causing the death of a person other than the person whose death was intended

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is marked `[15/2019]` but the encoding uses `effective 2019-12-31`, while the Criminal Law Reform Act 2019 (Act 15 of 2019) entered into force on 2020-01-01, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later `effective` clause with the verified commencement date `2020-01-01`, then rerun L3 review.

**Canonical text (first 500 chars):**

> —(1) If a person, by doing anything which he intends or knows to be likely to cause death, commits culpable homicide by causing the death of any person whose death he neither intends nor knows himself to be likely to cause, the culpable homicide committed by the offender is of the description of which it would have been if he had caused the death of the person whose death he intended or knew himself to be likely to cause. (2) To avoid doubt, in the circumstances mentioned in subsection (1), the …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr301-#pr301-
/// @amendment [15/2019]

statute 301 "Culpable homicide by causing the death of a person other than the person whose death was intended" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// subsection (1) applies only where both the lethal act and the mistaken victim result are present
            all_of {
                actus_reus doing_act := "doing anything which he intends or knows to be likely to cause death";
                actus_reus causing_other_person_death := "commits culpable homicide by causing the death of any person whose death he neither intends nor knows himself to be likely to cause";
            }
        }

        definitions {
            transferred_description := "the culpable homicide committed by the offender is of the description of which it would have been if he had caused the death of the person whose death he intended or knew himself to be likely to cause. [15/2019]";
        }
    }

    subsection (2) {
        definitions {
            defence_or_exception_rule := "To avo
```

---

### s311 — Punishment for infanticide

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section carries amendment markers `[15/2019]` and `[Act 23 of 2021 wef 01/03/2022]` but the encoding uses only `effective 1872-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Add later `effective` clauses for the post-1872 amendments, including `2022-03-01` and the verified commencement date for Act 15 of 2019, then rerun L3 review.

**Canonical text (first 500 chars):**

> Whoever commits the offence of infanticide shall be punished at the discretion of the court with imprisonment for life, or with imprisonment for a term which may extend to 10 years, and shall, if she is not sentenced to imprisonment for life, also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr311-#pr311-
/// @amendment [15/2019]
/// @amendment [Act 23 of 2021 wef 01/03/2022]

statute 311 "Punishment for infanticide" effective 1872-01-01 {
    /// Punishment for the offence of infanticide under section 310.
    penalty alternative {
        imprisonment := 0 years .. 10 years;
        supplementary := "Whoever commits the offence of infanticide shall be punished at the discretion of the court with imprisonment for life, or with imprisonment for a term which may extend to 10 years. [15/2019] [Act 23 of 2021 wef 01/03/2022]";
    }

    penalty when non_life_sentence {
        fine := unlimited;
        supplementary := "The offender shall, if she is not sentenced to imprisonment for life, also be liable to fine. [15/2019] [Act 23 of 2021 wef 01/03/2022]";
    }
}

```

---

### s323A — Punishment for voluntarily causing hurt which causes grievous hurt

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is marked `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later `effective` clause with the verified commencement date `2020-01-01`, then rerun L3 review.

**Canonical text (first 500 chars):**

> Whoever voluntarily causes hurt, if the hurt which he intends to cause or knows himself to be likely to cause is not grievous, but the hurt which he actually causes is grievous, shall be punished with imprisonment for a term which may extend to 5 years, or with fine which may extend to $10,000, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr323A-#pr323A-
/// @amendment [15/2019]

statute 323A "Punishment for voluntarily causing hurt which causes grievous hurt" effective 1872-01-01 effective 2019-12-31 {
    elements {
        all_of {
            actus_reus voluntarily_causes_hurt := "Whoever voluntarily causes hurt";
            mens_rea intends_or_knows_non_grievous_hurt := "The hurt which he intends to cause or knows himself to be likely to cause is not grievous";
            circumstance actual_hurt_grievous := "The hurt which he actually causes is grievous";
        }
    }

    penalty or_both {
        imprisonment := 0 years .. 5 years;
        fine := $0.00 .. $10,000.00;
        supplementary := "Whoever voluntarily causes hurt, if the hurt which he intends to cause or knows himself to be likely to cause is not grievous, but the hurt which he actually causes is grievous, shall be punished with imprisonment for a term which may extend to 5 years, or with fine which may extend to $10,000, or with both. [15/2019]";
    }

    /// Illustration
    illustration illustration {
        "At a club, 
```

---

### s334A — Punishment for voluntarily causing hurt on provocation which causes grievous hurt

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is marked `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent treats Act 15 of 2019 commencement as `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later `effective` clause with `2020-01-01`, then rerun L3 review.

**Canonical text (first 500 chars):**

> Whoever voluntarily causes hurt on grave and sudden provocation, if he neither intends nor knows himself to be likely to cause hurt to any person other than the person who gave the provocation and if the hurt which he intends to cause or knows himself to be likely to cause is not grievous, but the hurt which he actually causes is grievous, shall be punished with imprisonment for a term which may extend to one year, or with fine which may extend to $7,500, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr334A-#pr334A-
/// @amendment [15/2019]

statute 334A "Punishment for voluntarily causing hurt on provocation which causes grievous hurt" effective 1872-01-01 effective 2019-12-31 {
    elements {
        all_of {
            actus_reus voluntarily_causes_hurt := "Whoever voluntarily causes hurt";
            circumstance grave_and_sudden_provocation := "The hurt is caused on grave and sudden provocation";
            mens_rea no_intent_to_hurt_another := "He neither intends to cause hurt to any person other than the person who gave the provocation";
            mens_rea no_knowledge_likely_to_hurt_another := "He does not know himself to be likely to cause hurt to any person other than the person who gave the provocation";
            mens_rea intended_or_known_hurt_not_grievous := "The hurt which he intends to cause or knows himself to be likely to cause is not grievous";
            circumstance actual_hurt_grievous := "The hurt which he actually causes is grievous";
        }
    }

    penalty or_both {
        imprisonment := 0 years .. 1 years;
        fine :=
```

---

### s334 — Voluntarily causing hurt on provocation

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section carries amendment marker `[15/2019]` but the encoding uses `effective 2019-12-31`, while the Criminal Law Reform Act 2019 commenced on `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later effective date with `2020-01-01` and re-run L3 review.

**Canonical text (first 500 chars):**

> Whoever voluntarily causes hurt on grave and sudden provocation, if he neither intends nor knows himself to be likely to cause hurt to any person other than the person who gave the provocation, shall be punished with imprisonment for a term which may extend to 6 months, or with fine which may extend to $2,500, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr334-#pr334-
/// @amendment [15/2019]

statute 334 "Voluntarily causing hurt on provocation" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// The offence applies only where all stated conditions are present.
        all_of {
            actus_reus voluntarily_causes_hurt := "Whoever voluntarily causes hurt";
            circumstance grave_and_sudden_provocation := "The hurt is caused on grave and sudden provocation";
            mens_rea no_intent_to_hurt_another := "He neither intends to cause hurt to any person other than the person who gave the provocation";
            mens_rea no_knowledge_likely_to_hurt_another := "He knows himself not to be likely to cause hurt to any person other than the person who gave the provocation";
        }
    }

    penalty or_both {
        imprisonment := 0 months .. 6 months;
        fine := $0.00 .. $2,500.00;
        supplementary := "Whoever voluntarily causes hurt on grave and sudden provocation, if he neither intends nor knows himself to be likely to cause hurt to any person other than the person who g
```

---

### s342 — Punishment for wrongful confinement

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding is tagged with amendment marker `[15/2019]` but uses `effective 2019-12-31`, while Act 15 of 2019 commenced on 2020-01-01.
- suggested fix: Replace the later effective date with `2020-01-01` and keep the original `1872-01-01` commencement clause.

**Canonical text (first 500 chars):**

> Whoever wrongfully confines any person shall be punished with imprisonment for a term which may extend to 3 years, or with fine, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr342-#pr342-
/// @amendment [15/2019]

referencing penal_code/s340_wrongful_confinement

statute 342 "Punishment for wrongful confinement" effective 1872-01-01 effective 2019-12-31 {
    /// Punishment for wrongful confinement; see section 340 for the underlying offence.
    penalty or_both {
        imprisonment := 0 days .. 3 years;
        fine := unlimited;
        supplementary := "Whoever wrongfully confines any person shall be punished with imprisonment for a term which may extend to 3 years, or with fine, or with both. [15/2019]";
    }
}

```

---

### s367 — Kidnapping or abducting in order to subject a person to grievous hurt, slavery, etc.

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is marked `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the amendment effective date with the correct commencement date for Act 15 of 2019, then re-run L3 review.

**Canonical text (first 500 chars):**

> Whoever kidnaps or abducts any person in order that such person may be subjected, or may be so disposed of as to be put in danger of being subjected to grievous hurt or slavery, or to non‑consensual penile penetration of the anus or mouth, or knowing it to be likely that such person will be so subjected or disposed of, shall be punished with imprisonment for a term which may extend to 10 years, and shall also be liable to fine or to caning.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr367-#pr367-
/// @amendment [15/2019]

statute 367 "Kidnapping or abducting in order to subject a person to grievous hurt, slavery, etc." effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// Section 367 is conjunctive: the accused must kidnap or abduct, and must do so with the stated purpose or knowledge concerning the listed forms of harm.
        all_of {
            any_of {
                actus_reus kidnaps_person := "Whoever kidnaps any person";
                actus_reus abducts_person := "Whoever abducts any person";
            }

            any_of {
                mens_rea purpose_subject_or_dispose := "In order that such person may be subjected, or may be so disposed of as to be put in danger of being subjected to grievous hurt or slavery, or to non-consensual penile penetration of the anus or mouth";
                mens_rea knowledge_likely_subject_or_dispose := "Knowing it to be likely that such person will be so subjected or disposed of";
            }
        }
    }

    penalty cumulative {

        imprisonment := 0 years .. 10
```

---

### s376C — Commercial sex with minor below 18 years of age outside Singapore

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoded statute uses `effective 2020-01-01` even though comparable Penal Code sections introduced by the same `[15/2019]` amendment in this codebase use `2019-12-31`, so the amendment effective date is not sane enough to stamp.
- suggested fix: Verify the commencement date for Act 15 of 2019 for section 376C and update the `effective` clause to the correct date before rerunning L3 review.

**Canonical text (first 500 chars):**

> —(1) Any person, being a citizen or a permanent resident of Singapore, who does, outside Singapore, any act that would, if done in Singapore, constitute an offence under section 376B, shall be guilty of an offence. (1A) To avoid doubt, any person ( A ) who does in Singapore, any act involving a person below 18 years of age ( B ) who is outside Singapore, that would if B were in Singapore constitute an offence under section 376B, shall be guilty of an offence. (1B) Any person who does outside Sin…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr376C-#pr376C-
/// @amendment [15/2019]

statute 376C "Commercial sex with minor below 18 years of age outside Singapore" effective 1872-01-01 effective 2020-01-01 {
    subsection (1) {
        elements {
            /// Subsection (1) applies only where both the Singapore-status limb and the outside-Singapore conduct limb are satisfied.
            all_of {
                circumstance singapore_status := "Any person, being a citizen or a permanent resident of Singapore";
                actus_reus extraterritorial_act := "Who does, outside Singapore, any act that would, if done in Singapore, constitute an offence under section 376B";
            }
        }
    }

    subsection (1A) {
        elements {
            /// Subsection (1A) covers an act done in Singapore involving a minor who is outside Singapore.
            all_of {
                actus_reus in_singapore_act := "Any person ( A ) who does in Singapore, any act involving a person below 18 years of age ( B ) who is outside Singapore";
                circumstance hypothetical_s376B_offence := "That w
```

---

### s410 — Stolen property

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent for Act 15 of 2019 commencement is `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the later effective date with `2020-01-01` if that is the intended commencement date for this provision.

**Canonical text (first 500 chars):**

> —(1) Property the possession whereof has been transferred by theft, or by extortion, or by robbery, and property which has been criminally misappropriated, or in respect of which criminal breach of trust or cheating has been committed, is designated as “stolen property”, whether the transfer has been made or the misappropriation or breach of trust or cheating has been committed within or without Singapore. But if such property subsequently comes into the possession of a person legally entitled t…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr410-#pr410-
/// @amendment [15/2019]

statute 410 "Stolen property" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        definitions {
            stolen_property := "Property the possession whereof has been transferred by theft, or by extortion, or by robbery, and property which has been criminally misappropriated, or in respect of which criminal breach of trust or cheating has been committed, is designated as “stolen property”, whether the transfer has been made or the misappropriation or breach of trust or cheating has been committed within or without Singapore.";
            stolen_property_ceases := "But if such property subsequently comes into the possession of a person legally entitled to the possession thereof, it then ceases to be stolen property.";
        }
    }

    subsection (2) {
        definitions {
            stolen_property_includes_converted_or_exchanged_property := "The expression “stolen property” includes any property into or for which stolen property has been converted or exchanged and anything acquired by such conversi
```

---

### s426 — Punishment for committing mischief

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is marked `[15/2019]` but the encoding uses only `effective 1872-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Add the verified post-2019 commencement date for the Act 15 of 2019 amendment as an additional `effective` clause, then rerun L3 review.

**Canonical text (first 500 chars):**

> Whoever commits mischief shall be punished with imprisonment for a term which may extend to 2 years, or with fine, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr426-#pr426-
/// @amendment [15/2019]

referencing penal_code/s425_mischief

statute 426 "Punishment for committing mischief" effective 1872-01-01 {
    /// Punishment for the offence of mischief under section 425.
    penalty or_both {
        imprisonment := 0 days .. 2 years;
        fine := unlimited;
    }
}

```

---

### s442 — House-breaking

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is marked `[15/2019]` but the encoding only has `effective 1872-01-01`, so the later amendment effective date is missing and the effective-date encoding is not sane enough to stamp.
- suggested fix: Add the applicable later effective date for the 2019 amendment to the statute header, consistent with the canonical amendment history and nearby amended sections.

**Canonical text (first 500 chars):**

> Whoever commits criminal trespass by entering into, or remaining in, any building, tent, container or vessel used as a human dwelling, or any building used as a place for worship or as a place for the custody of property, is said to commit “house‑breaking”.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr442-#pr442-
/// @amendment [15/2019]

referencing penal_code/s441_criminal_trespass

statute 442 "House-breaking" effective 1872-01-01 {
    definitions {
        house_breaking := "Whoever commits criminal trespass by entering into, or remaining in, any building, tent, container or vessel used as a human dwelling, or any building used as a place for worship or as a place for the custody of property, is said to commit “house‑breaking”.";
        explanation_entering := "Explanation. —The introduction of any part of the criminal trespasser’s body is entering sufficient to constitute house-breaking.";
    }

    elements {
        /// Section 442 applies only where the underlying offence is criminal trespass and the trespass is by entering into, or remaining in, one of the specified premises.
        all_of {
            actus_reus base_criminal_trespass := "Commits criminal trespass";

            any_of {
                actus_reus entering := "By entering into";
                actus_reus remaining := "By remaining in";
            }

            any_of {
        
```

---

### s448 — Punishment for house-breaking

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, which repo-local L3 precedent already treats as an unsound commencement date for Act 15 of 2019.
- suggested fix: Replace the amendment effective date with the correct Act 15 of 2019 commencement date before resubmitting for L3 review.

**Canonical text (first 500 chars):**

> Whoever commits house-breaking shall be guilty of an offence and shall be punished with imprisonment for a term which may extend to 3 years, or with fine, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr448-#pr448-
/// @amendment [15/2019]

referencing penal_code/s442_house_breaking

statute 448 "Punishment for house-breaking" effective 1872-01-01 effective 2019-12-31 {
    /// Section 448 prescribes the punishment for the offence of house-breaking under section 442.
    penalty or_both {
        imprisonment := 0 days .. 3 years;
        fine := unlimited;
    }
}

```

---

### s450 — House-breaking in order to commit an offence punishable with imprisonment for life

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[15/2019]` but the encoding uses `effective 2019-12-31`, while repo-local L3 precedent treats Act 15 of 2019 commencement as `2020-01-01`, so the effective-date encoding is not sane enough to stamp.
- suggested fix: Replace the unsound 2019 amendment effective date with the correct commencement date used consistently for Act 15 of 2019 in this repo, then re-run L3 review.

**Canonical text (first 500 chars):**

> Whoever commits house-breaking in order to commit any offence punishable with imprisonment for life, shall be punished with imprisonment for a term not exceeding 15 years, and shall also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr450-#pr450-
/// @amendment [15/2019]

referencing penal_code/s442_house_breaking

statute 450 "House-breaking in order to commit an offence punishable with imprisonment for life" effective 1872-01-01 effective 2019-12-31 {
    definitions {
        house_breaking := "House-breaking as defined in section 442.";
        offence_punishable_with_imprisonment_for_life := "An offence punishable with imprisonment for life.";
    }

    elements {
        all_of {
            actus_reus commits_house_breaking := "Whoever commits house-breaking";
            mens_rea order_to_commit_life_imprisonment_offence := "In order to commit any offence punishable with imprisonment for life";
        }
    }

    penalty cumulative {
        imprisonment := 0 days .. 15 years;
        fine := unlimited;
    }
}

```

---

### s473A — Making or possessing equipment for making a false instrument

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding uses only `effective 1872-01-01`, but section 473A is a later inserted provision and should include its later commencement date instead of only the original 1872 date.
- suggested fix: Confirm the insertion commencement from the Penal Code legislative history and add that date as an `effective` clause for section 473A.

**Canonical text (first 500 chars):**

> Whoever makes or has in his custody or under his control a machine or implement, or paper or other material, which to his knowledge is or has been specifically designed or adapted for the making of any false instrument shall be punished with imprisonment for a term which may extend to 5 years, or with fine, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr473A-#pr473A-

statute 473A "Making or possessing equipment for making a false instrument" effective 1872-01-01 {
    elements {
        all_of {
            any_of {
                actus_reus makes_equipment := "Makes a machine or implement, or paper or other material";
                actus_reus possesses_equipment := "Has in his custody or under his control a machine or implement, or paper or other material";
            }
            mens_rea knowledge := "To his knowledge";
            circumstance specially_designed_or_adapted := "The machine or implement, or paper or other material, is or has been specifically designed or adapted for the making of any false instrument";
        }
    }

    penalty or_both {
        imprisonment := 0 days .. 5 years;
        fine := unlimited;
    }
}

```

---

### s477A — Falsification of accounts

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The encoding omits the amendment commencement date `2022-03-01` from `[Act 23 of 2021 wef 01/03/2022]`, so the effective clauses are incomplete.
- suggested fix: Add `effective 2022-03-01` to the statute header, preserving any already-valid commencement dates.

**Canonical text (first 500 chars):**

> Whoever, being a clerk, officer or servant, or employed or acting in the capacity of a clerk, officer or servant, intentionally and with intent to defraud destroys, alters, conceals, mutilates or falsifies any book, electronic record, paper, writing, valuable security or account or a set thereof which belongs to or is in the possession of his employer, or has been received by him for or on behalf of his employer, or intentionally and with intent to defraud makes or abets the making of any false …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr477A-#pr477A-
/// @amendment [15/2019]
/// @amendment [Act 23 of 2021 wef 01/03/2022]

statute 477A "Falsification of accounts" effective 1872-01-01 effective 2019-12-31 {
    definitions {
        explanation_1 := "Explanation 1 . —It shall be sufficient in any charge under this section to allege a general intent to defraud without naming any particular person intended to be defrauded, or specifying any particular sum of money intended to be the subject of the fraud or any particular day on which the offence was committed.";
        explanation_2 := "Explanation 2.—Any books, electronic records, papers, writings, valuable securities or accounts or any combination thereof form a set if they serve the same function or purpose in relation to the employer’s affairs or business.";
    }

    elements {
        /// Section 477A requires the employment relationship, the fraudulent mental element, one falsification mode, and the employer-linked record context.
        all_of {
            circumstance clerk_officer_or_servant_status := "Being a clerk, officer or servant, 
```

---

### s489B — Using as genuine forged or counterfeit currency or bank notes

**Verdict:** `INVESTIGATE` — no amendment markers detected; flag reasoning unclear

**Flag** (check 9):
- reason: The section is tagged `[15/2019]`, but the encoding uses `effective 2019-12-31` and the repo contains conflicting guidance on whether Act 15 of 2019 commenced on `2019-12-31` or `2020-01-01`, so the effective-date encoding is not safe to stamp.
- suggested fix: Confirm the commencement date for Act 15 of 2019 from an authoritative source, then update the second `effective` clause and re-run L3 review.

**Canonical text (first 500 chars):**

> Whoever delivers or sells to, or buys or receives from, any other person, or otherwise imports, exports or traffics in or uses as genuine, any forged or counterfeit currency or bank note, knowing or having reason to believe the same to be forged or counterfeit, shall be guilty of an offence and shall on conviction be punished with imprisonment for a term which may extend to 20 years, and shall also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr489B-#pr489B-
/// @amendment [15/2019]

statute 489B "Using as genuine forged or counterfeit currency or bank notes" effective 1872-01-01 effective 2019-12-31 {
    elements {
        all_of {
            actus_reus dealing_or_use := "Delivers or sells to, or buys or receives from, any other person, or otherwise imports, exports or traffics in or uses as genuine, any forged or counterfeit currency or bank note";
            mens_rea knowledge_or_reason_to_believe := "Knowing or having reason to believe the same to be forged or counterfeit";
        }
    }

    penalty cumulative {
        imprisonment := 0 days .. 20 years;
        fine := unlimited;
    }
}

```

---

