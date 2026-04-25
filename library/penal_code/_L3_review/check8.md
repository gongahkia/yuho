# L3 flags — failed check 820 sections in this group.---### s154 — Owner or occupier of land on which an unlawful assembly is held

**Verdict:** `FIX_NEEDED` — raw uses 'or' but encoding uses all_of without any_of — switch element grouping to any_of.

**Flag** (check 8):
- reason: The encoding collapses the prevention and dispersal/suppression omission limbs into one clause and drops the second canonical "do not", changing the section's conjunctive logic.
- suggested fix: Split the omission requirements so the notice, prevention, and dispersal/suppression failures are each preserved with the same negated conjunctions as the canonical text.

**Canonical text (first 500 chars):**

> Whenever any unlawful assembly or riot takes place, the owner or occupier of the land upon which such unlawful assembly is held or such riot is committed, and any person having or claiming an interest in such land, shall be punishable with fine not exceeding $5,000, if he or his agent or manager, knowing that such offence is being or has been committed, or having reason to believe it is likely to be committed, do not give the earliest notice thereof in his or their power to the principal officer…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr154-#pr154-

statute 154 "Owner or occupier of land on which an unlawful assembly is held" effective 1872-01-01 {
    elements {
        /// The section is conjunctive: the qualifying status, the assembly-or-riot event, the knowledge threshold, and both omission limbs must all be present.
        all_of {
            circumstance qualifying_person := "The person is the owner or occupier of the land upon which such unlawful assembly is held or such riot is committed, or a person having or claiming an interest in such land";
            circumstance event := "An unlawful assembly takes place on that land or a riot is committed on that land";
            mens_rea knowledge_threshold := "He or his agent or manager knows that such offence is being or has been committed, or has reason to believe it is likely to be committed";
            actus_reus no_earliest_notice := "He or his agent or manager does not give the earliest notice thereof in his or their power to the principal officer at the nearest police station";
            actus_reus no_lawful_means := "He or his ag
```

---

### s190 — Threat of injury to induce any person to refrain from applying for protection to a public servant

**Verdict:** `FIX_NEEDED` — raw uses 'or' but encoding uses all_of without any_of — switch element grouping to any_of.

**Flag** (check 8):
- reason: The `elements` split changes the statutory meaning by encoding the application as being for protection against injury to the public servant, instead of an application made to a legally empowered public servant for protection against injury.
- suggested fix: Re-encode the application/public-servant relationship so the offence matches the canonical sentence structure without changing who the protection is sought from.

**Canonical text (first 500 chars):**

> Whoever holds out any threat of injury to any person for the purpose of inducing that person to refrain or desist from making a legal application, for protection against any injury, to any public servant legally empowered as such to give such protection or to cause such protection to be given, shall be punished with imprisonment for a term which may extend to one year, or with fine, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr190-#pr190-

statute 190 "Threat of injury to induce any person to refrain from applying for protection to a public servant" effective 1872-01-01 {
    definitions {
        legal_application := "A legal application for protection against any injury";
        public_servant := "A public servant legally empowered as such to give such protection or to cause such protection to be given";
    }

    elements {
        all_of {
            actus_reus threat := "Holding out any threat of injury to any person";
            mens_rea purpose := "For the purpose of inducing that person to refrain or desist from making a legal application";
            circumstance protection_application := "The legal application is for protection against any injury to a public servant legally empowered as such to give such protection or to cause such protection to be given";
        }
    }

    penalty or_both {
        imprisonment := 0 years .. 1 year;
        fine := unlimited;
    }
}

```

---

### s26C — “Intentionally”

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: Canonical subsection (2) contains two disjunctive limbs, `(2)(a)` and `(2)(b)`, but the encoding stops after the em dash and does not represent either branch.
- suggested fix: Preserve subsection (2)(a) and (2)(b) as explicit alternative branches under subsection (2), with the canonical text verbatim.

**Canonical text (first 500 chars):**

> —(1) A person is said to do an act intentionally where that person does an act deliberately. (2) A person is said to cause an effect intentionally where that person does anything that causes an effect — (3) To avoid doubt, a person does not intend or foresee a result of his acts by reason only of it being a natural and probable consequence of those acts. (4) To avoid doubt, nothing in this section prevents a court from relying on a person’s foresight that a certain effect was a probable conseque…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr26C-#pr26C-
/// @amendment [15/2019]
statute 26C "“Intentionally”" effective 1872-01-01 effective 2020-01-01 {
    subsection (1) {
        definitions {
            intentionally_do_act := "A person is said to do an act intentionally where that person does an act deliberately. [15/2019]";
        }
    }

    subsection (2) {
        definitions {
            intentionally_cause_effect := "A person is said to cause an effect intentionally where that person does anything that causes an effect —";
        }
    }

    subsection (3) {
        definitions {
            natural_and_probable_consequence_not_enough := "To avoid doubt, a person does not intend or foresee a result of his acts by reason only of it being a natural and probable consequence of those acts. [15/2019]";
        }
    }

    subsection (4) {
        definitions {
            foresight_supports_inference := "To avoid doubt, nothing in this section prevents a court from relying on a person’s foresight that a certain effect was a probable consequence of his act as a basis to draw an inference that t
```

---

### s38 — Several persons engaged in the commission of a criminal act may be guilty of different offences

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The operative rule in the canonical text is flattened into two standalone definitions, so the section’s conjunctive "Where ..., they may ..." proposition is not actually encoded as a rule.
- suggested fix: Encode the main clause as a structured rule or elements block that preserves the conditional relationship, while keeping the illustration unchanged.

**Canonical text (first 500 chars):**

> Where several persons are engaged or concerned in the commission of a criminal act, they may be guilty of different offences by means of that act.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr38-#pr38-

statute 38 "Several persons engaged in the commission of a criminal act may be guilty of different offences" effective 1872-01-01 {
    definitions {
        engaged_or_concerned_persons := "Several persons are engaged or concerned in the commission of a criminal act";
        different_offences_by_same_act := "Those persons may be guilty of different offences by means of that act";
    }

    illustration illustration {
        "A attacks Z under such circumstances of grave provocation that his killing of Z would be only culpable homicide not amounting to murder. B , having ill will towards Z , and intending to kill him, and not having been subject to the provocation, assists A in killing Z . Here, though A and B are both engaged in causing Z ’s death, B is guilty of murder, and A is guilty only of culpable homicide."
    }
}

```

---

### s78 — Act done pursuant to the judgment or order of a court of justice

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The encoding treats the “notwithstanding the court may have had no jurisdiction” clause as a required conjunctive circumstance, even though the canonical text makes it a non-limiting proposition.
- suggested fix: Remove that clause from the mandatory `all_of` conditions and preserve it only as a non-required qualification while keeping the good-faith jurisdiction belief as the operative condition.

**Canonical text (first 500 chars):**

> Nothing which is done in pursuance of, or which is warranted by, the judgment or order of a court of justice, if done while the judgment or order remains in force, is an offence, notwithstanding the court may have had no jurisdiction to pass the judgment or order, provided the person doing the act in good faith believes that the court had such jurisdiction.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr78-#pr78-
statute 78 "Act done pursuant to the judgment or order of a court of justice" effective 1872-01-01 {
    definitions {
        rule := "Nothing which is done in pursuance of, or which is warranted by, the judgment or order of a court of justice, if done while the judgment or order remains in force, is an offence, notwithstanding the court may have had no jurisdiction to pass the judgment or order, provided the person doing the act in good faith believes that the court had such jurisdiction.";
        judgment_or_order := "The judgment or order of a court of justice.";
        jurisdictional_defect := "The court may have had no jurisdiction to pass the judgment or order.";
    }

    elements {
        /// Defence applies only when the act is connected to a court judgment or order, the judgment or order remains in force, and the actor has the required good-faith belief about jurisdiction.
        all_of {
            /// The statute covers either an act done in pursuance of the judgment or order, or an act warranted by it.
            any_of {
            
```

---

### s90 — Consent given under fear or misconception, by person of unsound mind, etc., and by child

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The encoding flattens the section into quoted definition strings and does not represent the operative disjunctive limbs in canonical paragraphs (a)(i), (a)(ii), (b), and (c), so the English connective structure is not faithfully encoded.
- suggested fix: Re-encode section 90 with explicit nested logical branches for paragraph (a) and the alternative limbs in paragraphs (b) and (c) instead of storing them as freeform definitions.

**Canonical text (first 500 chars):**

> A consent is not such a consent as is intended by any section of this Code — ( a ) if the consent is given by a person — ( b ) if the consent is given by a person who, from unsoundness of mind, mental incapacity, intoxication, or the influence of any drug or other substance, is unable to understand the nature and consequence of that to which he gives his consent; or ( c ) unless the contrary appears from the context, if the consent is given by a person who is below 12 years of age.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr90-#pr90-

statute 90 "Consent given under fear or misconception, by person of unsound mind, etc., and by child" effective 1872-01-01 {
    definitions {
        consent_rule := "A consent is not such a consent as is intended by any section of this Code —";
        condition_a := "( a ) if the consent is given by a person —";
        condition_b := "( b ) if the consent is given by a person who, from unsoundness of mind, mental incapacity, intoxication, or the influence of any drug or other substance, is unable to understand the nature and consequence of that to which he gives his consent; or";
        condition_c := "( c ) unless the contrary appears from the context, if the consent is given by a person who is below 12 years of age.";
    }
}

```

---

### s115 — Abetment of offence punishable with death or imprisonment for life

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The statute’s disjunctive penalty phrase "liable to fine or to caning" is not fully captured structurally because the encoding machine-encodes only `fine := unlimited` and leaves caning only in supplementary text.
- suggested fix: Encode the additional liability as a disjunctive penalty structure that preserves both fine and caning as separate machine-readable alternatives.

**Canonical text (first 500 chars):**

> Whoever abets the commission of an offence punishable with death or imprisonment for life, shall, if that offence is not committed in consequence of the abetment, and no express provision is made by this Code or by any other written law for the punishment of such abetment, be punished with imprisonment for a term that may extend to 20 years, and shall also be liable to fine or to caning.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr115-#pr115-
/// @amendment [Act 23 of 2021 wef 01/03/2022]
statute 115 "Abetment of offence punishable with death or imprisonment for life" effective 1872-01-01 effective 2022-03-01 {
    elements {
        /// The offence requires abetment of a qualifying offence plus the two statutory limiting conditions.
        all_of {
            actus_reus abetment := "Abets the commission of an offence punishable with death or imprisonment for life";
            circumstance offence_not_committed := "That offence is not committed in consequence of the abetment";
            circumstance no_express_provision := "No express provision is made by this Code or by any other written law for the punishment of such abetment";
        }
    }

    penalty cumulative {

        imprisonment := 0 years .. 20 years;
        supplementary := "The offender shall be punished with imprisonment for a term that may extend to 20 years.";

        alternative {
            fine := unlimited;
            supplementary := "The offender shall also be liable to fine or to caning.";
    
        }
 
```

---

### s139 — Saving

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The canonical section is a single conditional saving rule, but the encoding reduces it to three definitions and does not preserve the statute's operative logical structure.
- suggested fix: Re-encode the section as an explicit conditional rule that captures the "where ... no person ... shall be subject" logic rather than as standalone definitions.

**Canonical text (first 500 chars):**

> Where provision is made in any law relating to the discipline of the Singapore Armed Forces for the punishment of an offence corresponding to an offence defined in this Chapter, no person who is subject to such provision shall be subject to punishment under this Code for the offence defined in this Chapter.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr139-#pr139-

statute 139 "Saving" effective 1872-01-01 {
    definitions {
        service_discipline_provision := "Provision is made in any law relating to the discipline of the Singapore Armed Forces for the punishment of an offence corresponding to an offence defined in this Chapter";
        person_subject_to_service_discipline_law := "A person is subject to such provision";
        saving_rule := "No person who is subject to such provision shall be subject to punishment under this Code for the offence defined in this Chapter";
    }
}

```

---

### s155 — Liability of person for whose benefit a riot is committed

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The encoding decouples who had reason to believe from who failed to use lawful means, which broadens the statutory logic in a way the English text does not clearly permit.
- suggested fix: Model the person and the agent-or-manager as correlated alternative branches so each branch carries both the foresight and failure-to-act condition together.

**Canonical text (first 500 chars):**

> Whenever a riot is committed for the benefit or on behalf of any person who is the owner or occupier of any land respecting which such riot takes place, or who claims any interest in such land, or in the subject of any dispute which gave rise to the riot, or who has accepted or derived any benefit therefrom, such person shall be punishable with fine, if he or his agent or manager, having reason to believe that such riot was likely to be committed, or that the unlawful assembly by which such riot…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr155-#pr155-

statute 155 "Liability of person for whose benefit a riot is committed" effective 1872-01-01 {
    elements {
        all_of {
            actus_reus riot_benefit := "A riot is committed for the benefit or on behalf of a person";

            /// The section applies if the person is connected to the land, the dispute, or the benefit derived from the riot.
            any_of {
                circumstance owner_of_land := "The person is the owner of land respecting which the riot takes place";
                circumstance occupier_of_land := "The person is the occupier of land respecting which the riot takes place";
                circumstance claims_interest_in_land := "The person claims an interest in such land";
                circumstance claims_interest_in_dispute_subject := "The person claims an interest in the subject of a dispute which gave rise to the riot";
                circumstance accepted_or_derived_benefit := "The person has accepted or derived a benefit from the riot";
            }

            /// Liability attaches if the person, 
```

---

### s185 — Illegal purchase or bid for property offered for sale by authority of public servant

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The encoding factors the offence into `purchase_or_bid` plus an alternative mens rea block, which incorrectly makes a purchase without intent to perform punishable even though the canonical second limb applies only to a bid.
- suggested fix: Restructure the elements as two disjunctive branches: `(purchase or bid) + knowledge of legal incapacity`, and `bid + no intention to perform`.

**Canonical text (first 500 chars):**

> A person who, at any sale of property held by the lawful authority of a public servant as such, purchases or bids for any property on account of the person or another person, whom the person knows to be under a legal incapacity to purchase that property at that sale, or bids for such property not intending to perform the obligations under which the person lays himself by such bidding, shall — ( a ) in the case of an individual, be punished with imprisonment for a term which may extend to one mon…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr185-#pr185-
/// @amendment [15/2019]

statute 185 "Illegal purchase or bid for property offered for sale by authority of public servant" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// Section 185 requires a sale held by lawful authority of a public servant, a purchase or bid on account of self or another, and one of the two prohibited mental states.
        all_of {
            circumstance lawful_authority_sale := "At any sale of property held by the lawful authority of a public servant as such";
            actus_reus purchase_or_bid := "Purchases or bids for any property on account of the person or another person";
            any_of {
                mens_rea knowledge_of_legal_incapacity := "The person knows that the person on whose account the purchase or bid is made is under a legal incapacity to purchase that property at that sale";
                mens_rea no_intention_to_perform := "Bids for such property not intending to perform the obligations under which the person lays himself by such bidding";
            }
            /// The
```

---

### s204 — Destruction of document or electronic record to prevent its production as evidence

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The encoding rewrites the canonical sentence into `all_of` plus two `any_of` groups in a way that appears to make the prevention intent mandatory and treat lawful summons as a sibling alternative circumstance, which is not clearly faithful to the statute's original connective structure.
- suggested fix: Re-encode the operative clause more literally, preserving the placement of the final `or after he has been lawfully summoned or required...` limb before seeking L3 stamp.

**Canonical text (first 500 chars):**

> Whoever secretes or destroys any document or electronic record which he may be lawfully compelled to produce as evidence before a court of justice, or in any proceeding lawfully held before a public servant as such, or obliterates or renders illegible the whole or any part of such document or electronic record with the intention of preventing the same from being produced or used as evidence before such court or public servant as aforesaid, or after he has been lawfully summoned or required to pr…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr204-#pr204-

statute 204 "Destruction of document or electronic record to prevent its production as evidence" effective 1872-01-01 {
    elements {
        /// Section 204 is satisfied only if the prohibited handling of the document or electronic record and the prevention purpose coexist.
        all_of {
            /// The actus reus is disjunctive: concealment or destruction of the whole, or obliteration/rendering illegible of the whole or any part.
            any_of {
                actus_reus secretes_or_destroys := "Whoever secretes or destroys any document or electronic record";
                actus_reus obliterates_or_renders_illegible := "Obliterates or renders illegible the whole or any part of such document or electronic record";
            }
            /// The evidential setting is also disjunctive: the document may be lawfully compelled for evidence, or the person has already been lawfully summoned or required to produce it for that purpose.
            any_of {
                circumstance lawfully_compellable_evidence := "Which he may be lawfull
```

---

### s207 — Fraudulent claim to property to prevent its seizure as a forfeiture, in execution of a decree or under or pursuant to an enforcement order

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The encoding places `deceptive_practice` inside the same `all_of` bundle as `no_right_or_rightful_claim`, but the statute reads as a disjunctive branch where that knowledge qualifier attaches to accepting/receiving/claiming property, not necessarily to practising deception.
- suggested fix: Restructure the elements so the act branches track the statute’s syntax, with the knowledge qualifier scoped only to the acceptance/receipt/claim branch and the common seizure-prevention intent applied to both branches.

**Canonical text (first 500 chars):**

> Whoever fraudulently accepts, receives or claims any property or any interest therein, knowing that he has no right or rightful claim to such property or interest, or practises any deception touching any right to any property or any interest therein, intending thereby to prevent that property or interest therein from being taken as a forfeiture or in satisfaction of a fine under a sentence which has been pronounced, or which he knows to be likely to be pronounced by a court of justice or other c…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr207-#pr207-
/// @amendment [Act 25 of 2021 wef 01/04/2022]

statute 207 "Fraudulent claim to property to prevent its seizure as a forfeiture, in execution of a decree or under or pursuant to an enforcement order" effective 1872-01-01 effective 2022-04-01 {
    elements {
        /// The offence requires a fraudulent claim-or-deception act, lack of right, and a seizure-prevention purpose.
        all_of {
            any_of {
                actus_reus fraudulent_acceptance := "Fraudulently accepts any property or any interest therein";
                actus_reus fraudulent_receipt := "Fraudulently receives any property or any interest therein";
                actus_reus fraudulent_claim := "Fraudulently claims any property or any interest therein";
                actus_reus deceptive_practice := "Practises any deception touching any right to any property or any interest therein";
            }
            mens_rea no_right_or_rightful_claim := "Knowing that he has no right or rightful claim to such property or interest";
            circumstance seizure_target :=
```

---

### s217 — Public servant disobeying a direction of law with intent to save person from punishment or property from forfeiture

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The `.yh` uses an `all_of` structure in the person-saving limb that turns “save any person from legal punishment, or subject him to a lesser punishment” into a required sibling element instead of preserving the statute’s disjunctive object of the intent/knowledge clause.
- suggested fix: Re-encode the person-facing limb so the “save from legal punishment” and “subject to a lesser punishment” alternatives remain within the same disjunctive intent/knowledge branch.

**Canonical text (first 500 chars):**

> Whoever, being a public servant, knowingly disobeys any direction of the law as to the way in which he is to conduct himself as such public servant, intending thereby to save, or knowing it to be likely that he will thereby save, any person from legal punishment, or subject him to a lesser punishment than that to which he is liable, or with intent to save, or knowing that he is likely thereby to save, any property from forfeiture or any charge to which it is liable by law, shall be punished with…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr217-#pr217-

statute 217 "Public servant disobeying a direction of law with intent to save person from punishment or property from forfeiture" effective 1872-01-01 {
    elements {
        /// The offence is conjunctive as to public-servant status, knowing disobedience, and one prohibited saving outcome.
        all_of {
            circumstance public_servant_status := "Whoever, being a public servant";
            actus_reus disobedience := "Knowingly disobeys any direction of the law as to the way in which he is to conduct himself as such public servant";
            any_of {
                all_of {
                    any_of {
                        mens_rea intent_save_person := "Intending thereby to save any person from legal punishment";
                        mens_rea knowledge_likely_save_person := "Knowing it to be likely that he will thereby save any person from legal punishment";
                    }
                    actus_reus lesser_punishment_or_escape := "Save any person from legal punishment, or subject him to a lesser punishment than that t
```

---

### s308A — Causing death in furtherance of group’s object

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: Subsection (1)(b) is not faithfully encoded because the canonical disjunction between items (b)(i) and (b)(ii) is replaced by the truncated placeholder `paragraph_b_truncated := "Knowing that —"` and the two alternatives are omitted.
- suggested fix: Encode subsection (1) so paragraph (b) contains an explicit `any_of` that preserves both canonical alternatives in items (b)(i) and (b)(ii).

**Canonical text (first 500 chars):**

> —(1) Any person shall be guilty of an offence who is or acts as a member of a group — ( a ) knowing that the common object of the members of the group is to commit an offence under this Code or any written law; ( b ) knowing that — ( c ) the death of a person was caused in furtherance of the group’s common object. (2) A person who is guilty of an offence under subsection (1) shall be punished with imprisonment for life or imprisonment for a term which may extend to 20 years, and shall also be li…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr308A-#pr308A-
/// @amendment [15/2019]

statute 308A "Causing death in furtherance of group’s object" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// Subsection (1) is conjunctive in the canonical text: membership, knowledge, and death caused in furtherance of the group's common object must all be present.
            all_of {
                circumstance member_of_group := "Any person is or acts as a member of a group";
                mens_rea knows_common_object_is_offence := "Knowing that the common object of the members of the group is to commit an offence under this Code or any written law";
                mens_rea paragraph_b_truncated := "Knowing that —";
                actus_reus death_caused_in_furtherance := "The death of a person was caused in furtherance of the group’s common object";
            }
        }

        /// Illustration
        illustration illustration {
            "Three members of a group including A decide to rob a neighbourhood shop. The group leader, B brings a sharp knife but B
```

---

### s368 — Wrongfully concealing or keeping in confinement a kidnapped person

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The encoding uses top-level `all_of` with freeform strings for "kidnapped or abducted" and "conceals or keeps such person in confinement" instead of preserving those disjunctive alternatives as structured `any_of` branches.
- suggested fix: Split the knowledge and actus reus limbs into explicit `any_of` alternatives while keeping the overall offence conjunctive.

**Canonical text (first 500 chars):**

> Whoever, knowing that any person has been kidnapped or has been abducted, wrongfully conceals or keeps such person in confinement, shall be punished in the same manner as if he had kidnapped or abducted such person with the same intention or knowledge or for the same purpose as that with or for which he conceals or detains such person in confinement.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr368-#pr368-

statute 368 "Wrongfully concealing or keeping in confinement a kidnapped person" effective 1872-01-01 {
    elements {
        all_of {
            mens_rea knowledge_of_kidnapping_or_abduction := "Knowing that any person has been kidnapped or has been abducted";
            actus_reus wrongful_concealment_or_confinement := "Wrongfully conceals or keeps such person in confinement";
        }
    }

    penalty {
        supplementary := "Whoever, knowing that any person has been kidnapped or has been abducted, wrongfully conceals or keeps such person in confinement, shall be punished in the same manner as if he had kidnapped or abducted such person with the same intention or knowledge or for the same purpose as that with or for which he conceals or detains such person in confinement."
    }
}

```

---

### s404 — Dishonest misappropriation of property possessed by a deceased person at the time of his death

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The encoding introduces an `any_of` split between an invented `ordinary_case` and `clerk_or_servant_case`, but the canonical text states one offence with a higher imprisonment ceiling if the offender was the deceased's clerk or servant.
- suggested fix: Remove the fabricated offence-level disjunction and model the clerk-or-servant status only as the predicate for the enhanced penalty branch.

**Canonical text (first 500 chars):**

> Whoever dishonestly misappropriates or converts to his own use property, knowing that such property was in the possession of a deceased person at the time of that person’s decease, and has not since been in the possession of any person legally entitled to such possession, shall be punished with imprisonment for a term which may extend to 3 years, and shall also be liable to fine; and if the offender at the time of such person’s decease was employed by him as a clerk or servant, the imprisonment …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr404-#pr404-

statute 404 "Dishonest misappropriation of property possessed by a deceased person at the time of his death" effective 1872-01-01 {
    elements {
        /// Section 404 requires dishonest misappropriation or conversion, knowledge of the deceased's possession at death, and that no legally entitled person has since possessed the property.
        all_of {
            mens_rea dishonesty := "Whoever dishonestly";
            actus_reus misappropriation_or_conversion := "Misappropriates or converts to his own use property";
            mens_rea knowledge_of_deceased_possession := "Knowing that such property was in the possession of a deceased person at the time of that person’s decease";
            circumstance no_intervening_legal_possession := "The property has not since been in the possession of any person legally entitled to such possession";
            any_of {
                circumstance ordinary_case := "The offender is not shown to have been employed by the deceased as a clerk or servant at the time of that person’s decease";
                c
```

---

### s460 — House-breaking when death or grievous hurt caused

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The encoding flattens the statute's disjunctive aggravated-act phrase ("causes or attempts to cause death or grievous hurt") into a single element instead of modeling the alternatives with `any_of`.
- suggested fix: Refine the aggravated-act limb into explicit disjunctive branches so the connective structure matches the English text.

**Canonical text (first 500 chars):**

> If, at the time of the committing of house‑breaking, any person guilty of such offence voluntarily causes or attempts to cause death or grievous hurt to any person, every person jointly concerned in committing such house‑breaking, shall be punished with imprisonment for a term of not less than 3 years and not more than 20 years.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr460-#pr460-
/// @amendment [15/2019]

referencing penal_code/s442_house_breaking
referencing penal_code/s320_grievous_hurt

statute 460 "House-breaking when death or grievous hurt caused" effective 1872-01-01 effective 2019-12-31 {
    elements {
        /// Section 460 is conjunctive: the offender must be jointly concerned in the house-breaking, and during that house-breaking a guilty participant voluntarily causes or attempts to cause death or grievous hurt.
        all_of {
            actus_reus house_breaking := "Committing house-breaking";
            circumstance timing := "At the time of the committing of house-breaking";
            actus_reus aggravated_violence := "Any person guilty of such offence voluntarily causes or attempts to cause death or grievous hurt to any person";
            circumstance joint_participation := "The offender is every person jointly concerned in committing such house-breaking";
        }
    }

    penalty {
        imprisonment := 3 years .. 20 years;
    }
}

```

---

### s468 — Forgery for the purpose of cheating

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The encoding uses `penalty or_both`, but the canonical text makes imprisonment and liability to fine conjunctive, not disjunctive.
- suggested fix: Replace the disjunctive penalty form with the standard conjunctive penalty encoding used for sections that say the offender "shall also be liable to fine".

**Canonical text (first 500 chars):**

> Whoever commits forgery, intending that the document or electronic record forged shall be used for the purpose of cheating, shall be punished with imprisonment for a term which may extend to 10 years, and shall also be liable to fine.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr468-#pr468-

statute 468 "Forgery for the purpose of cheating" effective 1872-01-01 {
    elements {
        all_of {
            actus_reus commits_forgery := "Commits forgery";
            circumstance forged_object := "The document or electronic record is forged";
            mens_rea intention_for_cheating := "Intending that the document or electronic record forged shall be used for the purpose of cheating";
        }
    }

    penalty or_both {
        imprisonment := 0 days .. 10 years;
        fine := unlimited;
    }
}

```

---

### s473B — Making or possessing equipment for making a false instrument with intent to induce prejudice

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: The English in paragraph (b) requires conjunctive intent content in both `(b)(i)` and `(b)(ii)`, but the encoding stops at `mens_rea intent_clause := "Intends that —";` and omits those operative limbs entirely.
- suggested fix: Encode paragraph `(b)` so the intent element explicitly captures both `(b)(i)` and `(b)(ii)` as conjunctive requirements instead of a placeholder clause.

**Canonical text (first 500 chars):**

> Any person ( A ) who — ( a ) makes or has in his custody or under his control a machine or implement, or paper or other material, which is or has been specifically designed or adapted for the making of any instrument; and ( b ) intends that — shall be punished with imprisonment for a term which may extend to 10 years, or with fine, or with both.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr473B-#pr473B-

statute 473B "Making or possessing equipment for making a false instrument with intent to induce prejudice" effective 1872-01-01 {
    elements {
        all_of {
            /// paragraph (a) is disjunctive: making the equipment or having it in custody/control suffices
            any_of {
                actus_reus makes_equipment := "Makes a machine or implement, or paper or other material, which is or has been specifically designed or adapted for the making of any instrument";
                actus_reus possesses_equipment := "Has in his custody or under his control a machine or implement, or paper or other material, which is or has been specifically designed or adapted for the making of any instrument";
            }
            mens_rea intent_clause := "Intends that —";
        }
    }

    penalty or_both {
        imprisonment := 0 days .. 10 years;
        fine := unlimited;
    }
}

```

---

### s473C — Meaning of “prejudice” and “induce”

**Verdict:** `INVESTIGATE` — connective mismatch unclear without close read

**Flag** (check 8):
- reason: Subsection (1) encodes the `(a)` to `(f)` alternatives as opaque definition strings instead of preserving their disjunctive structure, so the English "or" logic is not represented faithfully.
- suggested fix: Refine subsection `(1)` into structured alternatives that preserve the `(a)` to `(f)` list and its disjunctive connective.

**Canonical text (first 500 chars):**

> —(1) For the purposes of section 473B and subject to subsections (2) and (4), an act or omission intended to be induced is to a person’s prejudice if, and only if, it is one which, if it occurs, will — ( a ) result in his permanent or temporary loss of property; ( b ) result in his being deprived of an opportunity to earn remuneration or greater remuneration; ( c ) result in his being deprived of an opportunity to gain a financial advantage otherwise than by way of remuneration; ( d ) result in …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr473C-#pr473C-

statute 473C "Meaning of “prejudice” and “induce”" effective 1872-01-01 effective 2008-02-01 {
    subsection (1) {
        definitions {
            application_to_section_473B := "For the purposes of section 473B and subject to subsections (2) and (4), an act or omission intended to be induced is to a person’s prejudice if, and only if, it is one which, if it occurs, will —";
            prejudice_loss_of_property := "( a ) result in his permanent or temporary loss of property;";
            prejudice_loss_of_remuneration_opportunity := "( b ) result in his being deprived of an opportunity to earn remuneration or greater remuneration;";
            prejudice_loss_of_financial_advantage_opportunity := "( c ) result in his being deprived of an opportunity to gain a financial advantage otherwise than by way of remuneration;";
            prejudice_gain_of_remuneration_opportunity_from_him := "( d ) result in somebody being given an opportunity to earn remuneration or greater remuneration from him;";
            prejudice_gain_of_financial_advantage_fr
```

---

