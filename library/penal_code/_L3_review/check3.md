# L3 flags — failed check 31 sections in this group.---### s148 — Rioting, armed with a deadly weapon

**Verdict:** `INVESTIGATE` — illustration count needs recounting

**Flag** (check 3):
- reason: The canonical section includes an Illustration heading with a preserved cross-reference note, but the encoding keeps that text only in comments instead of as a separate `illustration` block.
- suggested fix: Replace the comment-only preservation with an explicit `illustration` block containing the canonical text verbatim.

**Canonical text (first 500 chars):**

> Whoever is guilty of rioting, being armed with a deadly weapon, or with anything which, used as a weapon of offence, is likely to cause death, shall be punished with imprisonment for a term which may extend to 10 years and shall also be liable to caning.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr148-#pr148-
statute 148 "Rioting, armed with a deadly weapon" effective 1872-01-01 {
    elements {
        /// Section 148 is conjunctive: the accused must be guilty of rioting and be armed in the specified way.
        all_of {
            circumstance guilty_of_rioting := "Whoever is guilty of rioting";
            circumstance armed_with_deadly_weapon := "Being armed with a deadly weapon, or with anything which, used as a weapon of offence, is likely to cause death";
        }
    }

    penalty {
        imprisonment := 0 years .. 10 years;
        supplementary := "The offender shall also be liable to caning.";
    }

    // Heading
    // Illustration
    // Raw sub-item preserved verbatim from the canonical text.
    // The last section is subject to the same illustration as section 144.
}

```

---

