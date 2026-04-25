# L3 flags — failed check 42 sections in this group.---### s53 — Punishments

**Verdict:** `INVESTIGATE` — check whether canonical explanations are present as `///` comments or structured refinements

**Flag** (check 4):
- reason: The canonical explanation ("Explanation. —Caning shall be with a rattan.") is retained only as a bare definition string rather than as an explicit explanation/refinement form.
- suggested fix: Re-encode the explanation as a labelled `/// Explanation` comment or another explicit explanation/refinement construct without changing the statute text.

**Canonical text (first 500 chars):**

> The punishments to which offenders are liable under the provisions of this Code are — ( a ) death; ( b ) imprisonment; ( c ) forfeiture of property; ( d ) fine; ( e ) caning.

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr53-#pr53-

statute 53 "Punishments" effective 1872-01-01 {
    definitions {
        punishments_under_code := "The punishments to which offenders are liable under the provisions of this Code are";
        punishment_death := "death";
        punishment_imprisonment := "imprisonment";
        punishment_forfeiture_of_property := "forfeiture of property";
        punishment_fine := "fine";
        punishment_caning := "caning";
        explanation_caning_with_rattan := "Explanation. —Caning shall be with a rattan.";
    }
}

```

---

### s94 — Act to which a person is compelled by threats

**Verdict:** `INVESTIGATE` — check whether canonical explanations are present as `///` comments or structured refinements

**Flag** (check 4):
- reason: The two canonical explanations are not preserved as explanations or structured refinements, and the encoding adds a substantive self-placement condition not present in the canonical `text` or `sub_items`.
- suggested fix: Preserve Explanation 1 and Explanation 2 explicitly in explanatory form and remove unsupported substantive conditions unless they appear in the canonical source.

**Canonical text (first 500 chars):**

> Except murder and offences against the State punishable with death, nothing is an offence which is done by a person who is compelled to do it by threats, which, at the time of doing it, reasonably cause the apprehension that instant death to that person or any other person will otherwise be the consequence:

**Encoded `.yh` (first 1200 chars):**

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr94-#pr94-

statute 94 "Act to which a person is compelled by threats" effective 1872-01-01 {
    definitions {
        defence_rule := "Except murder and offences against the State punishable with death, nothing is an offence which is done by a person who is compelled to do it by threats, which, at the time of doing it, reasonably cause the apprehension that instant death to that person or any other person will otherwise be the consequence:";
        explanation_1 := "Explanation 1.—A person who, of his own accord, or by reason of a threat of being beaten, joins gang-robbers knowing their character, is not entitled to the benefit of this exception on the ground of his having been compelled by his associates to do anything that is an offence by law.";
        explanation_2 := "Explanation 2.—A person seized by gang-robbers, and forced by threat of instant death to do a thing which is an offence by law — for example, a smith compelled to take his tools and to force the door of a house for the gang‑robbers to enter and plunder it — is entitled to the benefit of this e
```

---

