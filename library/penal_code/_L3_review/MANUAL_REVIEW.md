# L3 flag manual review — 126 sections

Per-section thorough review of every flagged encoding, with categorised
recommendations. Generated after reading every `_L3_FLAG.md` reason +
suggested fix and cross-referencing against the canonical SSO text in
`_raw/act.json`.

**Three action labels:**

| Label | Meaning | Typical effort |
|---|---|---|
| `BATCH-FIX` | Mechanical pattern shared with several other flagged sections; can be done in one sweep with a targeted script. | low |
| `SINGLE-FIX` | Specific issue that needs a per-section edit but the diff is small. | medium |
| `RE-ENCODE` | Subsection / element structure needs substantive re-encoding from the canonical text. Best handled by a flag-fix dispatcher pass. | high |
| `OVERRIDE` | Flag is debatable or borderline; encoding is defensible. Document the decision and stamp. | low |

**Distribution of action labels** across the 126 flags:

| Action | Count |
|---|--:|
| BATCH-FIX | 47 |
| SINGLE-FIX | 22 |
| RE-ENCODE | 56 |
| OVERRIDE | 1 |

---

## Group A — Effective date sanity (check 9, 38 sections)

The largest cluster. Two sub-patterns dominate:

- **A1** — encoding uses `effective 2019-12-31` for sections marked `[15/2019]`; should be `2020-01-01` per the rest of the repo.
- **A2** — section was introduced by a later amendment but encoding only carries `effective 1872-01-01`; missing the introduction date.
- **A3** — section carries multiple amendment markers but encoding only has one or zero of them.

Sub-pattern A1 is a one-line `sed`. Sub-pattern A2 needs SSO history lookup per section but the value is small (~6 known commencement dates cover the cluster).

### A1 — `2019-12-31` → `2020-01-01` (Act 15 of 2019)

| Section | Title | Action | Fix |
|---|---|---|---|
| s99  | Right of private defence against act of person of unsound mind | BATCH-FIX | sed s/2019-12-31/2020-01-01/ |
| s106 | When right of private defence ext. (harm other than death) | BATCH-FIX | sed |
| s137 | Deserter concealed on board merchant vessel | BATCH-FIX | sed |
| s175 | Omission to produce document to public servant | BATCH-FIX | sed |
| s186 | Obstructing public servant in discharge of his public functions | BATCH-FIX | sed |
| s292A | Possession, distribution etc. of child sex-doll | BATCH-FIX | sed |
| s301 | Culpable homicide by causing the death of another person | BATCH-FIX | sed |
| s323A | Punishment for voluntarily causing hurt | BATCH-FIX | sed |
| s334 | Voluntarily causing hurt on provocation | BATCH-FIX | sed |
| s334A | Punishment for voluntarily causing hurt on provocation (gh) | BATCH-FIX | sed |
| s342 | Punishment for wrongful confinement | BATCH-FIX | sed |
| s367 | Kidnapping or abducting in order to subject person to gh | BATCH-FIX | sed |
| s410 | Stolen property | BATCH-FIX | sed |
| s448 | Punishment for house-breaking | BATCH-FIX | sed |
| s450 | House-breaking in order to commit offence punishable w/ life | BATCH-FIX | sed |
| s489B | Using as genuine forged currency | BATCH-FIX | sed |
| s157 | Harbouring persons hired for unlawful assembly | BATCH-FIX | sed |

**Sweep**: `find library/penal_code -name statute.yh -exec sed -i '' 's/effective 2019-12-31/effective 2020-01-01/g' {} +`. Then re-run `yuho check` and re-dispatch L3 over those sections.

### A2 — missing amendment date entirely

| Section | Title | Action | Specific fix |
|---|---|---|---|
| s76 | Act done by person bound or justified by law | SINGLE-FIX | add `effective 2020-01-01` |
| s97 | Right of private defence of body and property | SINGLE-FIX | add `effective 2020-01-01` |
| s108B | Abetment outside SG of an offence in SG | SINGLE-FIX | replace 1872 with `effective 2008-02-01` (Act 51/2007) |
| s130A | "Harbour" definition | SINGLE-FIX | add `effective 2008-02-01` |
| s130B | Piracy by law of nations | SINGLE-FIX | confirm SSO history, add insertion date |
| s130C | Piratical acts | SINGLE-FIX | confirm SSO history, add insertion date |
| s179 | Refusing to answer public servant authorised to question | SINGLE-FIX | add `effective 2020-01-01` |
| s183 | Resistance to taking of property by lawful authority | SINGLE-FIX | add `effective 2020-01-01` |
| s294 | Obscene acts | SINGLE-FIX | add `effective 2020-01-01` |
| s29B | "Electronic record" definition | SINGLE-FIX | add `effective 2008-02-01` |
| s426 | Punishment for committing mischief | SINGLE-FIX | add `effective 2020-01-01` |
| s442 | House-breaking | SINGLE-FIX | add `effective 2020-01-01` |
| s473A | Making or possessing equipment for making a false instrument | SINGLE-FIX | confirm SSO history, add insertion date |
| s121B | Offences against authority | SINGLE-FIX | verify Act 15/2019 wef date against an authoritative source |
| s204B | Bribery of witnesses | SINGLE-FIX | confirm SSO history, add insertion date |
| s267B | Punishment for committing affray | SINGLE-FIX | confirm SSO history, add insertion date |

### A3 — multi-amendment sections needing more than one new clause

| Section | Title | Action | Specific fix |
|---|---|---|---|
| s166 | Public servant disobeying direction (Act 25/2021) | SINGLE-FIX | add `effective 2022-04-01` alongside 1872 |
| s311 | Punishment for infanticide | SINGLE-FIX | add `effective 2020-01-01` and `effective 2022-03-01` |
| s26D | "Knowingly" definition | SINGLE-FIX | add `effective 2020-01-01` (15/2019) plus existing 2020-02-10 |
| s376C | Commercial sex with minor below 18 outside SG | SINGLE-FIX | verify against repo precedent (encoding currently uses 2020-01-01 — flag is conservative) — likely **OVERRIDE** acceptable |
| s477A | Falsification of accounts | SINGLE-FIX | add `effective 2022-03-01` |

**Group A summary: 38 sections, all mechanical or near-mechanical fixes once the canonical commencement dates are confirmed.**

---

## Group B — Fabricated penalty facts (check 7, 31 sections)

Several recurring sub-patterns:

- **B1** — fabricated `caning := 0 .. 24 strokes` for sections where canonical only says "liable to caning" without a stroke count. Fix: replace with `caning := unspecified` (G14 sentinel).
- **B2** — missing structured caning branch where canonical says "liable to fine or to caning". Fix: add `caning := unspecified` as alternative to fine.
- **B3** — life-imprisonment alternative left in supplementary prose instead of a structured penalty branch. Fix: add an `imprisonment := life` alternative branch.
- **B4** — wrong combinator (`or_both` where canonical is cumulative; `alternative` where canonical is cumulative).
- **B5** — fabricated structured penalty on a section that has no penalty clause at all.

### B1 — fabricated `caning := 0 .. 24 strokes` (delete the cap)

| Section | Title | Fix |
|---|---|---|
| s324 | Voluntarily causing hurt by dangerous weapons | replace numeric range with `caning := unspecified` |
| s327 | Voluntarily causing hurt to extort property | same |
| s328 | Causing hurt by means of poison | same |
| s329 | Voluntarily causing grievous hurt to extort property | same |
| s365 | Kidnapping or abducting with intent to confine | same |
| s366 | Kidnapping or abducting a woman | same |

**Action: BATCH-FIX**. All six follow the same pattern. Sed sweep:
`sed -i '' 's/caning := 0 \.\. 24 strokes/caning := unspecified/g'` then verify visually.

### B2 — missing caning branch

| Section | Title | Fix |
|---|---|---|
| s330 | Voluntarily causing hurt to extort confession | add `caning := unspecified` as alternative to fine |
| s331 | Voluntarily causing grievous hurt to extort confession | same |
| s332 | Voluntarily causing hurt to deter public servant | same |
| s333 | Voluntarily causing grievous hurt to deter public servant | same |
| s377BF | Sexual exposure (subsection 4) | same |
| s377BI | Distributing or selling child abuse material (subsection 2) | same |
| s377BJ | Advertising or seeking child abuse material | same |
| s385 | Putting person in fear of harm to commit extortion | same |
| s387 | Putting person in fear of death/grievous hurt to commit extortion | same |
| s115 | Abetment of offence punishable with death | same |

**Action: BATCH-FIX**. Single template: add `caning := unspecified` inside the existing penalty block as an `alternative` sibling to `fine`.

### B3 — missing life-imprisonment branch

| Section | Title | Fix |
|---|---|---|
| s130 | Aiding escape, rescue, harbouring | encode life-imprisonment as alternative; gate fine on non-life branch |
| s130E | Punishment for genocide (limb b) | add life-imprisonment alternative to up-to-20-years branch |
| s132 | Abetment of mutiny if mutiny committed | add life-imprisonment branch |
| s194 | Giving/fabricating false evidence to procure conviction | model base as life-or-up-to-20-years; scope death-eligible to 'gives' |
| s222 | Public servant intentional omission to apprehend | encode life-imprisonment alternative explicitly |
| s314 | Death caused by act done with intent to cause miscarriage | encode life-or-up-to-N as alternatives w/o non-canonical condition |
| s326 | Voluntarily causing grievous hurt by dangerous weapons | encode life branch; remove `non_life_sentence` invented condition |
| s400 | Punishment for belonging to gang-robbers | encode life branch; preserve only minimum strokes for caning |
| s438 | Mischief by fire (s437 enhanced) | encode life as structured alternative |

**Action: SINGLE-FIX each**. Same shape — add `imprisonment := life` as `alternative` sibling — but the surrounding penalty structure varies, so each needs an individual edit.

### B4 — wrong combinator

| Section | Title | Fix |
|---|---|---|
| s259 | Possession of counterfeit Government stamp | replace `or_both` with cumulative; canonical says "and shall also be liable" |
| s407 | CBT of property entrusted for transport | unwrap `alternative {}`; fine is cumulative not optional |
| s468 | Forgery for the purpose of cheating | replace `or_both` with cumulative |
| s476 | Counterfeiting authentication device | replace `or_both` with cumulative |

**Action: BATCH-FIX**. Four sections, each needs one combinator swap from `or_both` (or `alternative`) to default `cumulative`.

### B5 — non-penalty sections with fabricated penalty

| Section | Title | Fix |
|---|---|---|
| s113 | Liability of abettor for different offence caused | move "liable for the effect" out of `penalty {}` into refinement |
| s158 | Being hired to take part in unlawful assembly/riot | make penalty triggers mutually exclusive at element/condition level |
| s287 | Rash conduct re: machinery (subsection 3) | encode subsection (3)(a)-(d) as conditional penalty branches |
| s308 | Attempt to commit culpable homicide | add caning to `when hurt_caused` branch |
| s393 | Attempt to commit robbery | add explicit caning entry; keep minimum strokes language |
| s447 | Punishment for criminal trespass | replace fixed `$1,500.00` with capped range "up to 1500" |

**Action: SINGLE-FIX or RE-ENCODE**. Each is a per-section judgement call.

**Group B summary: 31 sections. 16 are pure batch fixes (B1+B2+B4); 15 need individual penalty restructuring.**

---

## Group C — `all_of` vs `any_of` mismatch (check 8, 20 sections)

Almost every flag here means the encoder collapsed disjunctive English ("or") into `all_of`, definitions, or freeform strings. The fix in each case is to refine the elements block into explicit `any_of` branches that match the canonical English.

| Section | Title | Action | Notes |
|---|---|---|---|
| s115 | Abetment of offence punishable w/ death (penalty side) | RE-ENCODE | already in B2 above; fold both fixes |
| s139 | Saving | RE-ENCODE | re-encode as conditional rule, not three definitions |
| s154 | Owner/occupier of land for unlawful assembly | RE-ENCODE | split prevention vs dispersal limbs; keep each negation |
| s155 | Liability of person for whose benefit a riot is committed | RE-ENCODE | correlated person-or-agent branches |
| s185 | Illegal purchase or bid (offered for sale) | RE-ENCODE | restructure to `(purchase or bid) + knowledge`, `bid + no intent` |
| s190 | Threat of injury to induce refrain from applying | RE-ENCODE | re-encode application/public-servant relationship correctly |
| s204 | Destruction of document to prevent production as evidence | RE-ENCODE | re-encode operative clause more literally |
| s207 | Fraudulent claim to property to prevent its seizure | RE-ENCODE | scope knowledge qualifier to receipt/claim branch |
| s217 | Public servant disobeying direction with intent to save | RE-ENCODE | preserve disjunctive object of intent/knowledge clause |
| s26C | "Intentionally" definition | RE-ENCODE | add (2)(a) and (2)(b) as alternative branches |
| s308A | Causing death in furtherance of group's object | RE-ENCODE | encode (1)(b)(i) and (1)(b)(ii) as `any_of` |
| s368 | Wrongfully concealing a kidnapped person | RE-ENCODE | split kidnapped/abducted + conceals/keeps as `any_of` |
| s38 | Several persons engaged in commission may be guilty | RE-ENCODE | encode "Where ..., they may ..." rule, not standalone defs |
| s404 | Dishonest misappropriation of deceased's property | RE-ENCODE | remove fabricated offence-level disjunction |
| s460 | House-breaking when death/grievous hurt caused | SINGLE-FIX | refine aggravated-act limb into `any_of` |
| s468 | Forgery for purpose of cheating | (also B4) | combinator + element fix together |
| s473B | Making or possessing equipment to make false instrument | RE-ENCODE | encode (b)(i) and (b)(ii) as conjunctive intent |
| s473C | Meaning of "prejudice" and "induce" | RE-ENCODE | refine (a)-(f) alternatives instead of opaque defs |
| s78 | Act done pursuant to court judgment/order | SINGLE-FIX | move "no jurisdiction" out of mandatory `all_of` |
| s90 | Consent given under fear/misconception | RE-ENCODE | encode (a)(i), (a)(ii), (b), (c) as nested branches |

**Group C summary: 20 sections. 18 need substantive re-encoding (RE-ENCODE), 2 are smaller targeted fixes (SINGLE-FIX). Best handled by a flag-fix dispatcher run scoped to this group with a tightened prompt that emphasises "preserve the canonical English connectives".**

---

## Group D — Subsections preserved (check 6, 10 sections)

Every flag in this group is the same shape: encoding has the right `subsection (N) {}` blocks but one or more is empty or only carries the introductory sentence; the canonical text has substantive content underneath that's being dropped.

| Section | Title | Empty/short subsection | Fix |
|---|---|---|---|
| s376AA | Exploitative sexual penetration of minor (16-18) | (2) | encode (2)(a), (2)(b) verbatim |
| s377BK | Possession/access to child abuse material | (3) | add (3)(a), (3)(b) text |
| s377C | Interpretation of sections 375 to 377BO | (1), (3) | full re-encode of (1) defs + (3)(a)-(f)(iii) |
| s416B | Cheating by remote communication | (2) | encode (2)(a)-(d) plus exclusion clause |
| s420A | Obtaining services dishonestly or fraudulently | (1) (paragraph c) | add (c) and (c)(i), (c)(ii) sub-items |
| s424A | Fraud by false representation | (5) | preserve "for the purposes of this section and section 424B" chapeau |
| s453 | Possession of house-breaking implements | (3) | encode (3)(a)-(d) instead of just lead-in |
| s489A | Forging or counterfeiting currency | (2) | encode all 3 definitions: bank note, coin, currency |
| s74E | Application of enhanced penalties | (2) | encode (2)(a), (2)(b) |
| s80 | Accident in the doing of a lawful act | (2) | encode (2) limbs + prosecution-proof requirement |

**Action: RE-ENCODE all 10**. The fix shape is identical (fill an empty subsection with verbatim canonical text), but the content per section is bespoke. Best handled by a targeted flag-fix dispatcher prompt: *"For each flagged section, identify the empty `subsection (N) { }` block, copy the verbatim canonical paragraph items from `_raw/act.json`'s `sub_items` for that subsection, and inline them as definitions or explicit nested elements."*

---

## Group E — Explanations preserved (check 4, 2 sections)

| Section | Fix |
|---|---|
| s53 | Re-encode "Caning shall be with a rattan" as `/// Explanation` doc comment, not bare definition. SINGLE-FIX. |
| s94 | Preserve Explanation 1 + Explanation 2 explicitly; remove unsupported self-placement condition. SINGLE-FIX. |

---

## Group F — Single-flag groups

| Group | Section | Fix |
|---|---|---|
| Check 5 (exceptions) | s96 | Remove fabricated `exception private_defence` block. SINGLE-FIX. |
| Check 3 (illustrations) | s148 | Convert illustration in comment to a real `illustration { }` block. SINGLE-FIX. |

---

## Group G — Uncategorised flags (check -1, 23 sections)

These came back without a machine-readable failed-check code; the flag reasons cover a mix of issues, often combining multiple checklist items. Per-section recommendations:

| Section | Issue | Action | Specific fix |
|---|---|---|---|
| s40 | "[15/2019; 2/2020]" is in subsection text body, plus effective clauses incomplete | SINGLE-FIX | strip amendment markers from quoted text; add 2nd effective clause |
| s53 | (also Group E above) | SINGLE-FIX | combined with explanation fix |
| s84 | Subsection (2) reduced to truncated definition string; (2)(a) and (2)(b) lost | RE-ENCODE | encode (2) as cumulative conditions, not just intro |
| s96 | (also Group F) | SINGLE-FIX | combined with exception fix |
| s105 | Subsection (1)(b) limbs and (2)(a)-(f) collapsed to defs | RE-ENCODE | encode all canonical limbs as `any_of` |
| s124 | Missing life-imprisonment alternative + uncertain commencement date | RE-ENCODE | (B3 + A1) — fold both fixes |
| s172 | "ordinary_process / court_process" gating breaks warrant-avoidance route | RE-ENCODE | model warrant-avoidance separately |
| s211 | "ordinary_false_charge" mutually-exclusive condition is fabricated | RE-ENCODE | base offence + aggravated penalty branch shape |
| s259 | (also B4 above) | BATCH-FIX | combinator swap |
| s304B | Subsection (2) empty; missing caning | RE-ENCODE | (D + B2) |
| s312 | Invented `pregnancy_not_more_than_16_weeks` | RE-ENCODE | unconditional miscarriage elements; aggravated penalty branch only |
| s363A | Missing caning + 3-way `fine, caning, or any combination` | RE-ENCODE | (B2 + structural) |
| s376E | Subsection (1)(b)(i)-(iii), (2)(a)-(c), (4) branches missing | RE-ENCODE | full subsection re-encode |
| s376EA | Subsection (1)(b)(i)-(iv) and (2)(a)-(c) truncated | RE-ENCODE | full re-encode |
| s376EB | Subsection (2)(a)-(b) and (3)(a)-(b) missing | RE-ENCODE | full re-encode |
| s376EE | Subsection (2) empty; (1)(c)(i)-(iii) missing; A1 effective date | RE-ENCODE | (D + A1) |
| s377B | Subsection (3) empty; fabricated caning cap; missing 2008 effective | RE-ENCODE | (D + B1 + A2) |
| s377BC | Subsection (2) missing; subsection (3)/(4) caning + combinator | RE-ENCODE | (D + B2 + combinator) |
| s377BH | Subsection (3)(a)-(c) missing; subsection (2) missing caning | RE-ENCODE | (D + B2) |
| s377CA | Subsection (1)/(2) flattened into definitions | RE-ENCODE | full re-encode |
| s379A | Subsection (3) reduced to comment; missing later effective | RE-ENCODE | (D + A2) |
| s414 | Subsection (2)(b) wording wrong (Cap. 276 vs 1961); A1 | SINGLE-FIX | restore canonical Road Traffic Act 1961 + sed effective |
| s416A | Subsections (2), (3), (7) drop content; A1 | RE-ENCODE | (D + A1) |
| s449 | Missing life-imprisonment + A1 | RE-ENCODE | (B3 + A1) |
| s476 | (also B4) | BATCH-FIX | combinator swap |

**Group G summary: 23 sections. 15 need substantive re-encoding; 6 are smaller targeted fixes; 2 are batch combinator swaps.**

---

## Recommended action plan

1. **First pass — pure batch fixes (47 sections, ~5 min)**:
   - **A1**: `find library/penal_code -name statute.yh -exec sed -i '' 's/effective 2019-12-31/effective 2020-01-01/g' {} +`
   - **B1**: `find library/penal_code -name statute.yh -exec sed -i '' 's/caning := 0 \.\. 24 strokes/caning := unspecified/g' {} +`
   - **B2** (manual but uniform): for each of the 10 sections, add `caning := unspecified;` as alternative sibling to `fine` inside the penalty block.
   - **B4**: 4 sections need `or_both` → cumulative or `alternative {}` → cumulative; can be done with targeted greps.

2. **Second pass — single-section fixes (22 sections, ~30-60 min)**:
   - A2 + A3 effective-date additions (16 sections).
   - Group E + F + smaller items in G — small per-section edits.

3. **Third pass — flag-fix dispatcher run (56 sections, ~30-90 min wall-clock)**:
   - Re-encoding-heavy work in groups C, D, and -1-with-RE-ENCODE.
   - Use `scripts/phase_d_flag_fix.py` with a tightened prompt: *"Read `_L3_FLAG.md`'s reason. Read the canonical `_raw/act.json` entry's `text` and `sub_items`. Re-encode the empty/truncated subsection(s) verbatim. Preserve disjunctive English with `any_of` and conjunctive English with `all_of`. Don't fabricate any structure not in canonical text. Run `yuho check`. If green, stamp."*
   - Run with `--parallel 4`.

4. **Fourth pass — re-run L3 review** scoped to the just-fixed sections.

5. **Final pass — rebuild corpus + ledger** to absorb the new stamps.

After this sweep, expected end state: ≥ 480 stamped sections, < 50 still flagged for human review.

---

## Disclaimer

The action labels above are recommendations from a structural read of the
flag reasons + canonical text. Each `BATCH-FIX` should still be visually
inspected on a sample before sweeping. `RE-ENCODE` recommendations
require either a Singapore-qualified lawyer's review or a flag-fix
dispatcher run with an appropriately constrained prompt.
