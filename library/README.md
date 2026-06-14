# Yuho Statute Library

Pre-built statute encodings in Yuho v5 syntax.

> **Disclaimer:** These models are provided for educational and research
> purposes only and do not constitute legal advice. Cross-reference any
> real decision with the official source text, including Singapore
> Statutes Online.

## Structure

Each encoded statute directory contains some or all of:

```
s<number>_<slug>/
  statute.yh         # canonical Yuho source
  illustrations.yh   # additional illustration material, if split out
  test_statute.yh    # behavioural smoke tests, where present
  metadata.toml      # section metadata, source URL, verification notes
```

Generated corpus files live under `_corpus/` and are intentionally
rebuildable from the checked-in sources.

## Singapore Penal Code 1871

`library/penal_code/` contains the full Singapore Penal Code proof of
concept:

| Measure | Current value |
|---|---:|
| Raw sections in `_raw/act.json` | 524 |
| Encoded `.yh` sections | 524 |
| L1 parse pass | 524 / 524 |
| L2 build + lint pass | 524 / 524 |
| L3 author-stamped fidelity pass | 524 / 524 |

Coverage data is stored in `library/penal_code/_coverage/coverage.json`.
The generated reference/corpus layer can be rebuilt with:

```bash
python scripts/build_corpus.py --no-mermaid-svg
```

Use the supported project environment (`uv run ...` or an installed
editable environment) so `tree-sitter` and `tree-sitter-yuho` are
available.

## Indian Penal Code 1860

`library/indian_penal_code/` is a phase-1 cross-jurisdiction corpus:

- 493 raw sections in `_raw/act.json`.
- 8 representative encoded sections:
  `s300`, `s302`, `s375`, `s376`, `s378`, `s420`, `s497`, and `s509`.

The IPC corpus is used for structural-overlap and portability checks; it
is not yet a full encoded IPC library.

## Usage

Reference a library statute from a `.yh` file:

```yh
referencing penal_code/s415_cheating
```

Or query the library through the CLI:

```bash
yuho library search cheating
yuho refs s415
yuho explain library/penal_code/s415_cheating/statute.yh
```

## `metadata.toml` Schema

```toml
[statute]
section_number = "415"
title = "Cheating"
jurisdiction = "Singapore"
version = "5.1.0"

[description]
summary = "..."
source = "Singapore Penal Code 1871, Section 415"
notes = "..."

[study]
offence_family = "property_offences"
related_sections = ["378", "379", "390", "392"]
exception_topics = ["claim_of_right"]
doctrine_tags = ["actus_reus", "mens_rea", "dishonesty"]
difficulty = "introductory"

[verification]
last_verified = "2026-03-08"
sso_url = "https://sso.agc.gov.sg/Act/PC1871?ProvIds=pr415-#pr415-"
verified_by = "Yuho Team"
disclaimer = "Educational purposes only. Cross-reference with official SSO text."
```
