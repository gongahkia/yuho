# L3 flags — failed check 610 sections in this group.---### s74E — Application of enhanced penalties

**Verdict:** `INVESTIGATE` — subsection structure needs comparison

**Flag** (check 6):
- reason: Canonical subsection (2) contains operative limbs (a) and (b), but the encoding preserves only the introductory phrase and omits both substantive rules.
- suggested fix: Encode subsection (2)(a) and (2)(b) as structured content under `subsection (2)` so the statutory rule is fully preserved.

**Canonical text (first 500 chars):**

> —(1) Where 2 or more of the sections from amongst sections 73 to 74D are applicable to enhance the punishment for an offence from that which the offender would otherwise have been liable for — ( a ) the punishment for the same offence shall not be enhanced by the application of more than one of those sections; and ( b ) the court may determine which section should apply to enhance the punishment. (2) Where any punishment prescribed for an offence is —

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr74E-#pr74E-
/// @amendment [15/2019]
statute 74E "Application of enhanced penalties" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// Subsection (1) governs overlap where two or more enhanced-penalty sections from sections 73 to 74D would otherwise apply to the same offence.
            all_of {
                circumstance multiple_enhancement_sections_applicable := "Where 2 or more of the sections from amongst sections 73 to 74D are applicable to enhance the punishment for an offence from that which the offender would otherwise have been liable for";
                prohibition multiple_enhancement_application := "the punishment for the same offence shall not be enhanced by the application of more than one of those sections";
                permission court_determines_applicable_section := "the court may determine which section should apply to enhance the punishment";
            }
        }
    }

    subsection (2) {
        definitions {
            prescribed_punishment_rule_intro := "Where any punishment pr
```

---

### s80 — Accident in the doing of a lawful act

**Verdict:** `INVESTIGATE` — subsection structure needs comparison

**Flag** (check 6):
- reason: Subsection (2) is not faithfully preserved because the encoding drops items (a) and (b) and the sentence requiring the prosecution to prove the fault element.
- suggested fix: Re-encode subsection (2) so both conjunctive limbs and the prosecution-proof requirement are explicitly represented within the subsection block.

**Canonical text (first 500 chars):**

> —(1) Nothing is an offence which is done by accident or misfortune in the doing of a lawful act in a lawful manner, by lawful means, and with proper care and caution. (2) To avoid doubt, where —

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr80-#pr80-
/// @amendment [15/2019]
/// @amendment [Act 23 of 2021 wef 01/03/2022]
statute 80 "Accident in the doing of a lawful act" effective 1872-01-01 effective 2020-01-01 effective 2022-03-01 {
    subsection (1) {
        definitions {
            no_offence_accident_lawful_act := "Nothing is an offence which is done by accident or misfortune in the doing of a lawful act in a lawful manner, by lawful means, and with proper care and caution. [15/2019]";
        }

        exception accident_or_misfortune_lawful_act {
            "Done by accident or misfortune in the doing of a lawful act in a lawful manner, by lawful means, and with proper care and caution."
            "Nothing is an offence."
        }
    }

    subsection (2) {
        definitions {
            avoid_doubt_intro := "To avoid doubt, where — [15/2019] [Act 23 of 2021 wef 01/03/2022]";
        }
    }

    definitions {
        lawful_act := "Explanation .—A lawful act in this section is any act which is not an offence under this Code or any written law and which is not otherwise prohibited b
```

---

### s376AA — Exploitative sexual penetration of minor of or above 16 but below 18 years of age

**Verdict:** `INVESTIGATE` — subsection structure needs comparison

**Flag** (check 6):
- reason: Canonical subsection (2) contains operative consent-related text, but the encoded `subsection (2)` block is empty and therefore does not faithfully preserve the statute.
- suggested fix: Encode subsection (2)(a) and (2)(b) explicitly within `subsection (2)` using the same structured preservation standard as the neighboring Penal Code sections.

**Canonical text (first 500 chars):**

> —(1) Any person ( A ) who is in a relationship that is exploitative of a person of or above 16 years of age but below 18 years of age ( B ) shall be guilty of an offence if A — ( a ) penetrates, with A ’s penis, if A is a man, the vagina, anus or mouth, as the case may be, of B ; ( b ) sexually penetrates, with a part of A ’s body (other than A ’s penis, if A is a man) or anything else, the vagina or anus, as the case may be, of B ; ( c ) causes B , if a man, to penetrate, with B ’s penis, the v…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr376AA-#pr376AA-
/// @amendment [15/2019]
statute 376AA "Exploitative sexual penetration of minor of or above 16 but below 18 years of age" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        definitions {
            exploitative_relationship := "A relationship that is exploitative of a person of or above 16 years of age but below 18 years of age, within the meaning of section 377CA.";
        }

        elements {
            /// Subsection (1) is conjunctive overall: the accused must be in the exploitative relationship with B, B must be within the stated age range, and one of the four penetration acts must occur.
            all_of {
                circumstance exploitative_relationship_with_b := "Any person ( A ) is in a relationship that is exploitative of a person of or above 16 years of age but below 18 years of age ( B )";
                circumstance b_age_range := "B is of or above 16 years of age but below 18 years of age";
                /// The statutory penetration acts are alternatives separated by paragraphs (a) to (d).
       
```

---

### s377BK — Possession of or gaining access to child abuse material

**Verdict:** `INVESTIGATE` — subsection structure needs comparison

**Flag** (check 6):
- reason: The encoding includes subsection (3) as a shell with only an illustration, but the canonical source also contains substantive paragraph (3)(a) and (3)(b) text that is omitted.
- suggested fix: Add the omitted subsection (3)(a) and (3)(b) definitions as structured content under subsection (3) while preserving the existing illustration verbatim.

**Canonical text (first 500 chars):**

> —(1) Any person shall be guilty of an offence who — ( a ) has in the person’s possession or has gained access to child abuse material; and ( b ) knows or has reason to believe that the material is child abuse material. (2) A person who is guilty of an offence under subsection (1) shall on conviction be punished with imprisonment for a term which may extend to 5 years, and shall also be liable to fine or to caning. (3) For the purposes of subsection (1) —

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr377BK-#pr377BK-
/// @amendment [15/2019]

statute 377BK "Possession of or gaining access to child abuse material" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// Subsection (1) is conjunctive overall: possession or access to the material, and knowledge or reason to believe of its child-abuse nature.
            all_of {
                any_of {
                    actus_reus possession := "Any person has in the person’s possession child abuse material";
                    actus_reus gained_access := "Any person has gained access to child abuse material";
                }
                any_of {
                    mens_rea knows_material_is_child_abuse_material := "Knows that the material is child abuse material";
                    mens_rea has_reason_to_believe_material_is_child_abuse_material := "Has reason to believe that the material is child abuse material. [15/2019]";
                }
            }
        }
    }

    subsection (2) {
        penalty cumulative {
            imprisonment := 0 years ..
```

---

### s377C — Interpretation of sections 375 to 377BO (sexual offences)

**Verdict:** `INVESTIGATE` — subsection structure needs comparison

**Flag** (check 6):
- reason: The encoding does not preserve the canonical subsection content because subsection (3) omits items (a) to (f)(iii) and subsection (1) leaves several definitions as incomplete stubs rather than carrying the full statutory text.
- suggested fix: Re-encode subsection (1) and subsection (3) so every canonical definition limb and paragraph in `act.json` is represented explicitly in `statute.yh`.

**Canonical text (first 500 chars):**

> —(1) In this section and in sections 375 to 377BO — “buttocks”, in relation to a person, includes the anal region of the person; “child abuse material” means material that depicts an image of any of the following: “distribute” includes any of the following conduct, whether done in person, electronically, digitally or in any other way: “image” means a still, moving, recorded or unrecorded image and includes an image produced by any means and, where the context requires, a three‑dimensional image;…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr377C-#pr377C-
/// @amendment [Act 23 of 2021 wef 01/03/2022]
/// @amendment [15/2019]

statute 377C "Interpretation of sections 375 to 377BO (sexual offences)" effective 1872-01-01 effective 2019-12-31 effective 2022-03-01 {
    subsection (1) {
        definitions {
            application_subsection_1 := "In this section and in sections 375 to 377BO —";
            buttocks := "“buttocks”, in relation to a person, includes the anal region of the person; [Act 23 of 2021 wef 01/03/2022]";
            child_abuse_material := "“child abuse material” means material that depicts an image of any of the following:";
            distribute := "“distribute” includes any of the following conduct, whether done in person, electronically, digitally or in any other way:";
            image_general := "“image” means a still, moving, recorded or unrecorded image and includes an image produced by any means and, where the context requires, a three-dimensional image;";
            image_in_relation_to_person := "“image”, in relation to a person, means an image of a human being that 
```

---

### s416B — Cheating by remote communication

**Verdict:** `INVESTIGATE` — subsection structure needs comparison

**Flag** (check 6):
- reason: The encoding does not faithfully preserve subsection (2), omitting paragraphs (a) to (d) and the exclusion clause after "means communication through —".
- suggested fix: Re-encode subsection (2) with all paragraph items and the full exclusion text from the canonical statute.

**Canonical text (first 500 chars):**

> —(1) A person ( A ) is said to “cheat by remote communication” if A cheats by deceiving another person ( Z ), and the deception is conducted mainly by way of remote communication with Z . (2) In this section, “remote communication” means communication through —

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr416B-#pr416B-
/// @amendment [Act 21 of 2025 wef 30/12/2025]

statute 416B "Cheating by remote communication" effective 1872-01-01 effective 2025-12-30 {
    subsection (1) {
        definitions {
            cheat_by_remote_communication := "A person ( A ) is said to “cheat by remote communication” if A cheats by deceiving another person ( Z ), and the deception is conducted mainly by way of remote communication with Z .";
        }
    }

    subsection (2) {
        definitions {
            remote_communication := "In this section, “remote communication” means communication through — [Act 21 of 2025 wef 30/12/2025]";
        }
    }
}

```

---

### s420A — Obtaining services dishonestly or fraudulently

**Verdict:** `INVESTIGATE` — subsection structure needs comparison

**Flag** (check 6):
- reason: The canonical entry includes subsection (1)(c) plus sub-items (c)(i) and (c)(ii), but the encoding omits them and therefore does not fully preserve subsection structure/content.
- suggested fix: Re-encode paragraph (c) and its two sub-items as part of subsection (1) without changing the canonical wording.

**Canonical text (first 500 chars):**

> —(1) A person shall be guilty of an offence if he obtains services for himself or another person dishonestly or fraudulently and — ( a ) the services are made available on the basis that payment has been, is being or will be made for or in respect of them; ( b ) the person obtains the services without any payment having been made for or in respect of them or without payment having been made in full; and ( c ) when the person obtains the services — (2) A person who is guilty of an offence under s…

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr420A-#pr420A-
/// @amendment [15/2019]
statute 420A "Obtaining services dishonestly or fraudulently" effective 1872-01-01 effective 2020-01-01 {
    subsection (1) {
        elements {
            /// The canonical source preserves subsection (1) as obtaining services plus the statutory payment conditions in paragraphs (a) and (b), but truncates paragraph (c) after its lead-in.
            all_of {
                actus_reus obtaining_services := "A person obtains services for himself or another person";

                any_of {
                    mens_rea dishonestly := "The person obtains the services dishonestly";
                    mens_rea fraudulently := "The person obtains the services fraudulently";
                }

                circumstance payment_basis := "The services are made available on the basis that payment has been, is being or will be made for or in respect of them";
                circumstance unpaid_or_not_paid_in_full := "The person obtains the services without any payment having been made for or in respect of them or without payment 
```

---

### s424A — Fraud by false representation, non-disclosure or abuse of position not connected with contracts for goods or services

**Verdict:** `INVESTIGATE` — subsection structure needs comparison

**Flag** (check 6):
- reason: Subsection (5) is not fully preserved because the encoding omits the chapeau that its definitions apply "for the purposes of this section and section 424B", which drops a substantive cross-section scope statement.
- suggested fix: Preserve subsection (5)'s introductory scope text explicitly in the encoding so the definitions are not represented as applying only within section 424A.

**Canonical text (first 500 chars):**

> —(1) A person shall be guilty of an offence if he, fraudulently or dishonestly — ( a ) makes a false representation; ( b ) fails to disclose to another person information which he is under a legal duty to disclose; or ( c ) abuses, whether by act or omission, a position which he occupies in which he is expected to safeguard, or not to act against, the financial interests of another person. (2) A person may be guilty of an offence under subsection (1) whether or not the acts in subsection (1)( a …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr424A-#pr424A-
/// @amendment [15/2019]

statute 424A "Fraud by false representation, non-disclosure or abuse of position not connected with contracts for goods or services" effective 1872-01-01 effective 2020-01-01 {
    subsection (1) {
        elements {
            /// The offence requires fraudulent or dishonest fault plus one of the three prohibited acts.
            all_of {
                any_of {
                    mens_rea fraudulent := "He acts fraudulently";
                    mens_rea dishonest := "He acts dishonestly";
                }

                any_of {
                    actus_reus false_representation := "Makes a false representation";
                    actus_reus failure_to_disclose := "Fails to disclose to another person information which he is under a legal duty to disclose";
                    actus_reus abuse_of_position := "Abuses, whether by act or omission, a position which he occupies in which he is expected to safeguard, or not to act against, the financial interests of another person";
                }
            }
      
```

---

### s453 — Possession of house-breaking implements or offensive weapons

**Verdict:** `INVESTIGATE` — subsection structure needs comparison

**Flag** (check 6):
- reason: Subsection (3) in the canonical text includes operative paragraphs (a) to (d), but the encoding preserves only the lead-in presumption sentence and drops all four categories.
- suggested fix: Encode subsection (3)(a) to (d) explicitly instead of reducing subsection (3) to a single definition line.

**Canonical text (first 500 chars):**

> —(1) Any person who is found — ( a ) armed with any instrument for shooting, stabbing or cutting, or any instrument which, used as a weapon of offence, is likely to cause death, without lawful authority or a lawful purpose; ( b ) having his face covered or otherwise found disguised with intent to commit any offence; or ( c ) equipped with any article or instrument for use in the course of or in connection with any house‑breaking, shall be guilty of an offence and shall on conviction be punished …

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr453-#pr453-
/// @amendment [15/2019]
/// @amendment [Act 43 of 2024 wef 24/03/2025]

statute 453 "Possession of house-breaking implements or offensive weapons" effective 1872-01-01 effective 2019-12-31 effective 2025-03-24 {
    subsection (1) {
        elements {
            any_of {
                all_of {
                    actus_reus armed_with_weapon := "Any person who is found armed with any instrument for shooting, stabbing or cutting, or any instrument which, used as a weapon of offence, is likely to cause death";
                    circumstance without_lawful_authority_or_purpose := "Without lawful authority or a lawful purpose";
                }
                all_of {
                    actus_reus face_covered_or_disguised := "Any person who is found having his face covered or otherwise found disguised";
                    mens_rea intent_to_commit_offence := "With intent to commit any offence";
                }
                actus_reus equipped_for_house_breaking := "Any person who is found equipped with any article or instrument for use in th
```

---

### s489A — Forging or counterfeiting currency or bank notes

**Verdict:** `INVESTIGATE` — subsection structure needs comparison

**Flag** (check 6):
- reason: Subsection (2) is not faithfully preserved because the encoding drops the statutory definitions of "bank note", "coin", and "currency" and keeps only the lead-in.
- suggested fix: Encode subsection (2) with all three canonical definitions from `_raw/act.json` instead of the placeholder lead-in-only definition.

**Canonical text (first 500 chars):**

> —(1) Whoever forges or counterfeits, or knowingly performs any part of the process of forging or counterfeiting, any currency or bank note shall be guilty of an offence and shall on conviction be punished with imprisonment for a term which may extend to 20 years, and shall also be liable to fine. (2) In this section and sections 489B to 489I —

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr489A-#pr489A-
/// @amendment [15/2019]

statute 489A "Forging or counterfeiting currency or bank notes" effective 1872-01-01 effective 2019-12-31 {
    subsection (1) {
        elements {
            /// The subsection is conjunctive overall: one prohibited making limb and the specified subject matter.
            all_of {
                /// The physical conduct is disjunctive across the three statutory alternatives.
                any_of {
                    actus_reus forges_currency_or_bank_note := "Forges any currency or bank note";
                    actus_reus counterfeits_currency_or_bank_note := "Counterfeits any currency or bank note";
                    all_of {
                        mens_rea knowingly := "Knowingly";
                        actus_reus performs_part_of_process := "Performs any part of the process of forging or counterfeiting any currency or bank note";
                    }
                }
                circumstance subject_matter := "Any currency or bank note";
            }
        }

        penalty cumulative {
            
```

---

