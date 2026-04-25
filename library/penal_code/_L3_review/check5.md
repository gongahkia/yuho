# L3 flags — failed check 51 sections in this group.---### s96 — Nothing done in private defence is an offence

**Verdict:** `INVESTIGATE` — exception preservation needs canonical-vs-encoded comparison

**Flag** (check 5):
- reason: The encoding fabricates an `exception private_defence` block even though the canonical section is a single operative sentence with no canonical exceptions or sub-items.
- suggested fix: Re-encode section 96 as a direct faithful rule without introducing a non-canonical exception structure.

**Canonical text (first 500 chars):**

> Nothing is an offence which is done in the exercise of the right of private defence.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr96-#pr96-
statute 96 "Nothing done in private defence is an offence" effective 1872-01-01 {
    definitions {
        no_offence_private_defence := "Nothing is an offence which is done in the exercise of the right of private defence.";
        right_of_private_defence := "The right of private defence.";
    }

    exception private_defence {
        "Nothing is an offence which is done in the exercise of the right of private defence."
        "Nothing is an offence."
        when facts.right_of_private_defence == TRUE
    }
}

```

---

