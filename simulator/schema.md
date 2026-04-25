# Fact-pattern schema

A fact pattern is a YAML or JSON document describing a hypothetical
scenario in terms an encoded statute can reason over. The schema is
deliberately narrow: structured facts in, element-by-element trace out.
The simulator is a teaching and research demo; **it does not predict
case outcomes or provide legal advice**.

## Top-level shape

```yaml
name: "A intentionally deceives B about a worthless article"
section: "415"                       # section to evaluate against
description: |
  Optional prose framing. Free-form text, not parsed.

parties:
  A:
    role: accused
  B:
    role: victim

acts:
  - actor: A
    description: "deceives B into believing a worthless article is valuable"
    timestamp: "2025-01-01"

mental_states:
  A:
    intent: "to defraud"
    knowledge: "the article is worthless"

circumstances:
  - "B has not encountered the article before"
  - "A is known to B and trusted"

outcomes:
  - actor: B
    description: "B buys the worthless article from A"

asserted_exceptions:
  - name: consent
    raised_by: A

fact_facts:
  # Direct boolean fact assertions to map onto encoded element names.
  # Used when prose facts can't be matched automatically.
  deception: true
  fraudulent: true
  inducement: true
  harm: true
```

## Field meanings

- `name`: short label for the scenario.
- `section`: which encoded section to evaluate against. Required.
- `description`: free-form prose framing. Optional, ignored by the matcher.
- `parties`: named participants with roles (`accused`, `victim`,
  `witness`, `third party`, etc.). Used by the trace renderer.
- `acts`: things parties do. Each carries an `actor` and a free-form
  `description`. Map onto `actus_reus` elements.
- `mental_states`: per-party mental-state attestations. Map onto
  `mens_rea` elements.
- `circumstances`: contextual facts. Map onto `circumstance` elements.
- `outcomes`: results of the acts (separate from acts because the same
  act can produce multiple outcomes).
- `asserted_exceptions`: the accused's invoked defences. Match against
  encoded `exception` blocks; the matcher reports whether the asserted
  exception is recognised by the section's encoded grammar.
- `fact_facts`: direct boolean overrides. Maps element names (as they
  appear in the encoded `.yh`) to `true` / `false`. Used when prose
  facts can't be matched automatically and for unit-test fixtures.

## Matching semantics

The simulator does **not** decide whether the offence is made out. It
walks the encoded section's elements and exceptions, and reports for
each element whether the supplied facts satisfy, contradict, or leave
the element unresolved. This is a structural trace, not a legal
adjudication.

Matching today is deliberately simple:

1. If an element name appears in `fact_facts`, use that boolean directly.
2. Otherwise, attempt a substring match between the element's
   description and any `acts` / `mental_states` / `circumstances`
   strings; if a non-trivial overlap exists, mark the element
   *suggested* (not satisfied).
3. Elements not in `fact_facts` and without prose overlap are marked
   *unresolved*.

A future version may use the encoded LSP types and grammar primitives to
reason more precisely about which fact field maps to which element kind.

## Output

The simulator emits a structured trace:

```json
{
  "section_number": "415",
  "section_title": "Cheating",
  "satisfied": ["deception", "fraudulent", "inducement", "harm"],
  "contradicted": [],
  "unresolved": [],
  "suggested": [],
  "exceptions_raised": ["consent"],
  "exceptions_matched": [],
  "verdict": "all elements satisfied; no recognised exception applies",
  "warnings": []
}
```

`verdict` is a one-sentence structural summary (not a legal conclusion).

## Disclaimer

The simulator is a teaching / research demo over an encoded representation
of the Singapore Penal Code 1871. It does not adjudicate cases, predict
outcomes, replace legal advice, or constitute an opinion. Use it to
understand how the elements of a section break down against a fact
pattern, not to decide anything.
