# Yuho fact-pattern simulator

Structured-fact-pattern → element-trace tool for the encoded Singapore
Penal Code 1871 corpus. Teaching / research demo for executable statutes.

**The simulator does not predict case outcomes, decide whether an offence
is made out, or provide legal advice.** It walks the encoded section's
elements and reports for each whether the supplied facts satisfy,
contradict, or leave the element unresolved. That's it.

## Layout

```
simulator/
├── schema.md                 # fact-pattern schema reference
├── simulator.py              # the tool itself (Python stdlib only)
├── fixtures/                 # worked example fact patterns
│   ├── s415_classic.yaml
│   ├── s415_with_consent.yaml
│   └── s378_theft.yaml
└── README.md
```

## Run

```sh
# Pre-req: encoded corpus
python3 scripts/build_corpus.py

# Human-readable trace
python3 simulator/simulator.py simulator/fixtures/s415_classic.yaml

# JSON
python3 simulator/simulator.py simulator/fixtures/s415_classic.yaml --json
```

Sample output (s415, classic facts):

```
Section: s415 · Cheating
Fact pattern: A intentionally deceives B about a worthless article

Verdict: all 5 elements satisfied; no exceptions asserted

Elements (5):
  ✓ satisfied:    deception
  ✓ satisfied:    fraudulent
  ✓ satisfied:    inducement
  ✓ satisfied:    harm
  ✓ satisfied:    dishonest
```

## Writing a fact pattern

See `schema.md` for the full reference. Short version:

```yaml
name: "Short label for the scenario"
section: "415"

parties:
  A: { role: accused }
  B: { role: victim }

acts:
  - actor: A
    description: "what A did"

mental_states:
  A:
    intent: "what A meant"
    knowledge: "what A knew"

circumstances:
  - "context fact 1"
  - "context fact 2"

asserted_exceptions:
  - name: consent
    raised_by: A

fact_facts:
  # Direct boolean overrides for encoded element names.
  # Use this when the prose facts above don't map automatically.
  deception: true
  fraudulent: true
  inducement: true
  harm: true
```

Element names in `fact_facts` must match the names in the encoded `.yh`
file (e.g. `library/penal_code/s415_cheating/statute.yh`). The
simulator reports unresolved elements when no `fact_facts` entry exists
and the prose facts don't overlap; that's the cue to add either prose
or a `fact_facts` boolean.

## What it does and doesn't do

| | |
|---|---|
| ✓ Walks the encoded section's elements | ✗ Adjudicates whether the offence is made out |
| ✓ Reports satisfied / contradicted / unresolved per element | ✗ Predicts a verdict |
| ✓ Matches asserted defences against encoded `exception` blocks | ✗ Decides whether a defence applies |
| ✓ Renders a structural trace for teaching | ✗ Provides legal advice |
| ✓ Outputs JSON for downstream tooling | ✗ Replaces a Singapore-qualified lawyer |

## Roadmap

- Use the LSP's typed AST instead of regex for element extraction.
- Per-element burden qualifier handling: trace shows which side bears
  the burden for each unresolved element.
- Worked fixtures for: s390 (robbery), s392 (extortion), s379 (punishment
  for theft), s107 (abetment), s34 (common intention), s302 (murder vs
  s299 culpable homicide).
- MCP tool surface: `yuho_simulate` so AI clients can drive the
  simulator over user-supplied facts.

## Disclaimer

The simulator is a research / educational artefact. It does not provide
legal advice. The encoded statute is a structural representation of the
Penal Code drafted from publicly available SSO text; cross-reference with
the [canonical SSO source](https://sso.agc.gov.sg/Act/PC1871) for any
decision that matters.
