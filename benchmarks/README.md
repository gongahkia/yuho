# Yuho benchmark pack (`benchmarks/`)

Reusable evaluation tasks generated from the encoded Singapore Penal Code
1871 corpus. Five task types as of v0.1.0; ~3,300 rows total.

> **Sibling: `evals/`.** The repo also ships a separate `evals/`
> directory containing a **scenario-fixture LLM evaluation
> harness** — 205 natural-language fact patterns + a runner with
> Anthropic / OpenAI / Fake clients + per-fixture and stratified
> accuracy reports. That's a *runner deliverable* — point it at
> a model and get accuracy numbers. This `benchmarks/` directory
> is the *dataset deliverable* — five JSONL files you drop into
> any evaluation harness of your choice. They evaluate
> complementary surfaces; see `evals/README.md` for the runner.

## Why

Yuho's encoded library is a structured, audited representation of a real
penal code. That makes it a natural source of evaluation tasks for legal-AI
work: every task carries a citable provenance back to a specific section,
a SHA-256 hash of the canonical SSO text, and the Yuho version that
encoded it.

The benchmark complements the DSL paper. It is *not* a chatbot benchmark
or a legal-advice task; it is a structured-reasoning evaluation grounded
in publicly-available statute text.

## Tasks

| Task | Rows | Input | Answer | Scorer |
|---|---:|---|---|---|
| `citation_grounding` | 519 | a fragment of canonical SSO text | the section number it came from | exact-match on section number |
| `penalty_extraction` | 290 | canonical text of a section that has a penalty clause | the encoded `penalty { … }` block | whitespace-normalised exact match |
| `element_classification` | 2,165 | one element string + name | element kind (`actus_reus` / `mens_rea` / `circumstance` / `obligation` / `prohibition` / `permission`) | exact-match on label |
| `cross_reference` | 91 | a section's canonical text | the set of section numbers it references (subsumes / amends / implicit) | F1 over section-number set + strict exact-match |
| `illustration_recognition` | 254 | a verbatim illustration string | the section number it belongs to | exact-match on section number |

Row counts are deterministic given the corpus + a fixed RNG seed (default
`20260425`); re-runs of the generator produce stable diffs.

## Layout

```
benchmarks/
├── manifest.json                     # generation metadata
├── build_benchmarks.py               # generator
├── tasks/
│   ├── citation_grounding.jsonl
│   ├── penalty_extraction.jsonl
│   ├── element_classification.jsonl
│   ├── cross_reference.jsonl
│   └── illustration_recognition.jsonl
├── scorers/
│   └── score.py                      # scorer
└── README.md                          # this file
```

## Build

```sh
# pre-req: encoded corpus
python3 scripts/build_corpus.py

# generate tasks
python3 benchmarks/build_benchmarks.py

# smoke run (50 rows per task)
python3 benchmarks/build_benchmarks.py --max 50

# single task only
python3 benchmarks/build_benchmarks.py --task penalty_extraction
```

## Score

Predictions go into a JSONL file with one prediction per line:

```jsonl
{"id": "cite_s415", "task": "citation_grounding", "prediction": {"section_number": "415"}}
{"id": "elem_s415_deception", "task": "element_classification", "prediction": {"kind": "actus_reus"}}
```

Then:

```sh
python3 benchmarks/scorers/score.py --predictions out.jsonl
python3 benchmarks/scorers/score.py --task penalty_extraction --predictions out.jsonl
python3 benchmarks/scorers/score.py --predictions out.jsonl --detail   # per-row CSV
```

Scorer output is JSON: per-task accuracy plus mean-F1 for set-valued tasks.

## Provenance

Every task row carries a `provenance` block:

```json
{
  "source_section": "415",
  "raw_sha256": "9f963c…",
  "yuho_version": "5.1.0",
  "encoding_commit": "<git sha at corpus build time>"
}
```

`raw_sha256` is the SHA-256 of the canonical SSO text for that section as
stored in `library/penal_code/_raw/act.json`. If the upstream SSO text
changes, the hash changes and the task can be flagged stale.

## Limitations

- **Single jurisdiction.** Singapore-only. Cross-jurisdiction generalisation
  (Indian Penal Code, etc.) is future work.
- **Encoder + reviewer overlap.** The encoded corpus the tasks draw from
  was authored by the same team that drafted the L3 review prompts. External
  L3 review by a Singapore-qualified lawyer is the natural next step before
  the benchmark is treated as a definitive evaluation.
- **Task scope is narrow.** These are structured-reasoning tasks tied to the
  encoded representation, not open-ended legal-reasoning challenges. The
  benchmark scores how well a system can recover Yuho's structural
  decisions, not how well it can reason about the law from first principles.
- **`cross_reference` only catches what the encoded library and G10 resolver
  surface today.** Implicit references inside long prose-only sections are
  approximate; subsumes / amends edges are exact.

## Citation

If you use this benchmark, cite the project:

```bibtex
@software{yuho_benchmark_2026,
  author  = {Gabriel Ong Zhe Mian},
  title   = {Yuho benchmark pack: structured reasoning over the
             Singapore Penal Code 1871},
  year    = {2026},
  url     = {https://github.com/gongahkia/yuho/tree/main/benchmarks},
  version = {0.1.0}
}
```

## Disclaimer

This benchmark is a research / educational artefact. It does not provide
legal advice. Its source corpus is the publicly-available Singapore Penal
Code 1871 as encoded in the Yuho library; cross-reference with the
[canonical SSO source](https://sso.agc.gov.sg/Act/PC1871) for any decision
that matters.
