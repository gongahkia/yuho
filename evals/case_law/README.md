# Case-law differential testing — `evals/case_law/`

The first Yuho-evaluation surface that scores against an *external*
authoritative source (Singapore courts), rather than against
Yuho's own ground truth.

Catala's flagship empirical claim is *"our compiled tax calculator
matches the French government's official tax calculator on N
filings"*. This directory builds the Yuho analogue: *"`yuho
recommend` agrees with the actual charge in N reported Singapore
criminal cases; `yuho contrast` recovers a structural distinguisher
between actual and alternative charges in 100% of cases; the
encoded model expressively hosts the court's stated reasoning in
100% of cases"*.

## Layout

```
evals/case_law/
├── README.md                          (this file)
├── score_recommend.py                 (top-k accuracy + MRR + per-chapter)
├── score_contrast.py                  (Z3 contrast vs court reasoning, F1)
├── score_contrast_constrained.py      (encoded-model expressivity check)
└── fixtures/                          (curated case-law fixtures, YAML)
    ├── case-pp-v-kho-jabing.yaml
    ├── case-pp-v-lim-poh-lye.yaml
    ├── …
```

## Three orthogonal scorers

The harness ships three scoring drivers, each measuring a
different kind of agreement-with-courts:

### 1. `score_recommend.py` — prosecutorial-choice alignment

Runs `ChargeRecommender` over each fixture's encoded fact pattern
and scores the ranked output against `actual_charge` (the section
the prosecution brought). Headline metrics:

- **Top-1 / Top-3 / Top-5 accuracy** — does the actual charge
  appear in the top-k ranked candidates?
- **Mean Reciprocal Rank (MRR)** — averaged over fixtures.
- **Per-chapter agreement** — stratified by Penal Code chapter.
- **Confusion matrix** — when wrong, what does the recommender
  predict instead?

Run::

    python evals/case_law/score_recommend.py
    python evals/case_law/score_recommend.py --json --out results.json

### 2. `score_contrast.py` — element-pick vs court reasoning

For fixtures with both `actual_charge` and `alternative_charge`,
runs `yuho contrast(actual_charge, alternative_charge)` and
scores the surfaced distinguishing-elements set against
`court_distinguished_on` — the elements the court itself said
distinguished the two sections.

Headline metric:

- **Mean F1** over predicted-vs-court element sets, averaged
  across fixtures.

This is the *unconstrained* contrast: Z3 picks *any* valid
distinguisher. Where multiple disjunctive elements distinguish
two sections (e.g. s300's four limbs all qualify a fact pattern
as murder), Z3's pick may differ from the court's specific
reasoning — a structural feature, not a bug.

### 3. `score_contrast_constrained.py` — encoded-model expressivity

The deeper question: *given the court's stated distinguisher,
is it satisfiable in the encoded model?* For each fixture, the
court's element is asserted as a hard Z3 constraint alongside
the contrast formula `s_A_conviction AND NOT s_B_conviction`.

- **`consistent`** → the court's specific reasoning has a model
  in the encoding (the encoding can express it).
- **`unsat`** → the encoding rejects the court's reading
  (falsification signal — investigate).
- **`no-element-in-encoding`** → the court named an element the
  encoded section's vocabulary doesn't carry (encoding gap, not
  a falsification).

Headline metric:

- **Consistency-rate** = `n_consistent / (n - n_no_encoding)`.

This is the soundness-style claim: a high consistency-rate is
evidence that the encoding is expressively complete enough to
host the body of court reasoning we tested.

## Fixture schema

Each YAML file under `fixtures/` carries:

```yaml
id: case-pp-v-kho-jabing
case_citation: "PP v Kho Jabing [2015] SGCA 1"
actual_charge: "300"               # section the court convicted of
alternative_charge: "299"          # section considered/argued as alternative
court_distinguished_on: [intent3]  # element names the court relied on
outcome: "Convicted of s300(c) murder; death sentence affirmed."
case_summary: |
  ...natural-language summary for paper presentation...

# Below: simulator-shape fields used by ChargeRecommender
section: "300"
description: |
  ...natural-language fact pattern fed to the recommender...
parties: { A: {role: accused}, B: {role: victim} }
acts: [...]
mental_states: { A: {...} }
circumstances: [...]
outcomes: [...]
fact_facts:
  causeDeath: true
  intent1: false
  intent2: false
  intent3: true
  intent4: false
tags: [source:case-law, chapter:xvi, category:homicide, ...]
```

The fixture is *both* an evals-pack fixture (loadable by the eval
runner) and a simulator fixture (loadable by the recommender) by
construction — same file serves both surfaces.

## Adding a new case fixture

1. Read the judgment from LawNet / Singapore Law Watch.
2. Identify the principal charge → `actual_charge`.
3. If the court considered / rejected an alternative section →
   `alternative_charge`.
4. Note the element-level reasons the court gave for choosing
   actual over alternative → `court_distinguished_on`. Use the
   element names the encoded section already carries (run
   `yuho transpile -t json library/penal_code/sNNN_*/statute.yh`
   to see them).
5. Compose the `description` / `acts` / `circumstances` /
   `outcomes` from the judgment's fact recital.
6. Set `fact_facts` to the boolean fact map — every encoded
   element name on `actual_charge` should appear with the
   corresponding truth value.
7. Drop the YAML in `fixtures/`. Run all three scorers; if any
   scorer raises, fix the fixture.

## Coverage gaps — sample growth roadmap

The 2026-04-29 corpus covers n=40 fixtures. Chapter coverage is
uneven; the following pockets are explicit gaps to drive
sample-growth runs against:

* **Chapter II (offences against the State).** Absent. Modern
  prosecutions go through the Internal Security Act / repealed
  Sedition Act, so reported Penal Code-track judgments are rare.
  Targeted citation candidates require a LawNet sweep on
  `s121` / `s121A` / `s124A` / `s124B` charge tags; expect zero
  hits in many years.
* **Chapter XX (marriage offences).** Absent. Bigamy
  prosecutions are typically routed through the Women's Charter
  rather than s494 PC. Same constraint applies.
* **Chapter XXIII (insulting modesty / voyeurism).** Single
  fixture (`case-nicholas-tan-siew-chye.yaml`, s377BB(4),
  [2023] SGHC 35). Pre-2020 s509 cases (the repealed
  word/gesture-insulting-modesty provision) and post-2020
  s377BA (word/gesture insulting modesty, the s509 successor)
  cases are both absent. Most s377BA-tier fact patterns surface
  at District Court level and don't generate reported judgments;
  s509-era reported judgments exist on LawNet/eLitigation but
  haven't been encoded yet. Targeted citation candidates require
  an eLitigation search on the s509 / s377BA / s377BB charge
  tags (user action — Claude lacks LawNet/eLitigation access).
* **Kidnapping (ss363–367).** Absent. Most kidnapping
  prosecutions use the Kidnapping Act 1961 rather than the Penal
  Code; the 2026-04-29 eLitigation sweep located no reported
  s363A PC cases.

### Authoring a chapter-XXIII fixture (template)

When LawNet/eLitigation access is available, copy and fill in
the YAML skeleton at
[`fixtures/case-template-chapter-xxiii.yaml.template`](./fixtures/case-template-chapter-xxiii.yaml.template).
The template carries the s377BB / s377BA element-name
conventions already, so the boolean `fact_facts` keys line up
with the encoded library; only the citation, fact recital, and
truth values need to be filled.

## Caveats / threats to validity

The paper §7.8 enumerates these alongside the headline numbers:

- **Charge-selection bias.** Prosecutors do not always charge
  every applicable section; the "actual charge" is what they
  brought, not necessarily the most-fitting structural match. We
  report top-k, not just top-1, to mitigate.
- **Fact-extraction subjectivity.** The encoded fact pattern is
  the curator's reading of the judgment; inter-rater reliability
  would help. Out of scope for v1.
- **Encoded-statute drift from court reasoning.** Some courts read
  statutes creatively; disagreement may reflect either a
  Yuho-encoding error or a court innovation. The
  constrained-contrast scorer flags this directly via the
  `unsat` and `no-element-in-encoding` paths.
- **s304 negative-definition limit.** s304 is encoded as
  `intention + causation + not_murder` — it doesn't carry
  s300-limb-specific names (`intent3` etc.), so contrasts of
  the form `s300 vs s304` cannot name `intent3` as the
  distinguisher even when the court's reasoning identifies it.
  The constrained-contrast scorer's `no-element-in-encoding`
  status surfaces this honestly.

## NOT legal advice

Every output carries the `not_legal_advice` flag. The scorers
measure *structural* agreement between Yuho and court reasoning;
they are not legal-correctness measures. Disagreement can mean
encoding error, court creativity, or genuine doctrinal
divergence — the harness surfaces structure, not law.
