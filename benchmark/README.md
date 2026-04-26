# Yuho LLM legal-reasoning benchmark

A graded benchmark for LLM legal-reasoning over the Singapore Penal
Code 1871, scored against the structural ground truth Yuho's
evaluator computes from the same encoded library that powers the
rest of the toolchain.

The benchmark is **not** a legal accuracy test. It scores whether
an LLM can recover the *structural shape* of the answer that the
encoded statute already commits to. Position alongside LegalBench
and LawBench: same evaluation surface, different ground-truth
backing — Yuho's evaluator over the encoded `.yh` corpus.

## Tasks

Each fixture exercises three tasks:

| Task | Question | Scoring |
|---|---|---|
| **T1** | Which Penal Code section best applies to this scenario? | Exact match on the canonical section string (`"415"`, `"376AA"`). |
| **T2** | Which encoded elements does the scenario satisfy? | F1 over predicted vs ground-truth element name set. Exact-match accuracy reported alongside. |
| **T3** | Which defeating exception fires (if any)? | Exact match (case-insensitive); `"none"` is the canonical no-exception answer. |

## Layout

```
benchmark/
├── README.md            (this file)
├── schema.json          (JSON-schema for fixture files)
├── run.py               (runner — fixture loader + LLM client + scorer)
└── fixtures/            (205 fixtures: 22 hand-authored + 183 synthesised)
    ├── s415-classic.yaml
    ├── s415-no-deception.yaml
    ├── s378-classic.yaml
    ├── s378-with-consent.yaml
    ├── s319-classic.yaml
    ├── …
```

The 183 synthesised fixtures are generated from the canonical
illustrations in the encoded library by
`scripts/synthesise_benchmark_fixtures.py`. They're tagged
`synth:true`; pass `--no-per-fixture` and inspect the stratified
report's `synth` axis to compare hand-authored vs synthesised
performance.

## Running

The runner is single-file Python with two clients: an Anthropic
SDK client (for real benchmark runs) and a `FakeClient` that
returns ground truth verbatim (for end-to-end CI without API
calls).

```sh
# Smoke-test the full pipeline with no API calls — every fixture
# scores 100% on every task.
python benchmark/run.py --fake

# Real run against Claude (requires ANTHROPIC_API_KEY).
python benchmark/run.py --model claude-sonnet-4-6
python benchmark/run.py --model claude-opus-4-7

# Cap fixtures for a quick spot-check.
python benchmark/run.py --max-fixtures 5

# Machine-readable output to a file.
python benchmark/run.py --json --out benchmark/results.json

# Stratified accuracy slices (per chapter / category / difficulty / synth):
python benchmark/run.py --fake --no-per-fixture
```

### Bulk-generating fixtures from the encoded library

```sh
python scripts/synthesise_benchmark_fixtures.py
```

For every encoded section that has both leaf elements AND
illustrations, this writes one fixture per illustration into
`benchmark/fixtures/`. Existing fixture files are not overwritten.
Polarity-negative illustrations (text containing "is not", "no
offence", etc.) are auto-tagged `polarity:negative` and emit an
empty `satisfied_elements` set so the LLM is graded on identifying
the negative case.

### Plugging in a different model

Implement the `BenchmarkClient` protocol — one method,
`query(prompt, *, system="", task_kind="") -> str`. The runner
calls it three times per fixture (T1 / T2 / T3) and scores the
returned string. See `AnthropicClient` and `FakeClient` for
reference implementations.

## Fixture format

```yaml
id: s415-classic
section: "415"
scenario: |
  Natural-language fact pattern. The LLM sees this verbatim.
ground_truth:
  section: "415"                # the answer to T1
  satisfied_elements:           # the answer to T2
    [deception, fraudulent, inducement, harm]
  fired_exception: null         # the answer to T3 (null = "none")
fact_facts:                     # boolean facts fed to Yuho's evaluator
  deception: true
  fraudulent: true
  inducement: true
  harm: true
tags: [chapter:xvii, category:deception, difficulty:basic]
```

The element names in `satisfied_elements` must match the leaf
`name` fields on the encoded section's element graph (visible via
`yuho transpile -t json library/penal_code/sNNN_*/statute.yh`).
This is what makes the ground truth structural rather than
authored: the same names the evaluator computes are the names the
LLM is graded against.

## Adding fixtures

1. Pick a section. Read `library/penal_code/sNNN_*/statute.yh`,
   note the element names.
2. Compose a neutral, unambiguous scenario in prose. Don't name
   the answer in the scenario.
3. Run the scenario through Yuho's evaluator (or compute by
   inspection) to derive `satisfied_elements` and
   `fired_exception`.
4. Drop the YAML in `benchmark/fixtures/`.

The runner's `FakeClient` end-to-end test confirms the fixture
loads cleanly. Add a tag or two so the runner's per-tag breakdown
(future) can stratify results.

## What this is not

The benchmark scores the **structural shape** of an LLM's answer
against the encoded statute. It does not score:

- Whether the LLM's answer would prevail in court (that is
  evidentiary).
- Whether the encoded section is the *only* applicable section
  (concurrent charges are real; the benchmark picks the most
  directly applicable one).
- Generated prose quality, citation style, or pedagogical tone.

Every output carries the same `not_legal_advice` envelope used
elsewhere in the toolchain.
