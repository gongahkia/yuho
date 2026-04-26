# Reproducibility — verifying every empirical claim in the paper

This document is the **single source of truth** for what the paper
claims and how a reader can verify each claim independently. Every
numerical claim in §5 / §7 / §7.8 of the paper has a corresponding
command listed below; running them on a clean checkout reproduces
the table / figure / paragraph.

The repo is set up so reproducibility is one Make target deep:

```sh
make paper-reproduce
```

…which runs every claim and writes a one-page summary at
`logs/paper-reproduce-summary.txt`.

If you don't want to install the toolchain locally, use the
Dockerfile:

```sh
docker build -t yuho:latest .
docker run --rm yuho:latest
```

The container's default entrypoint is `make paper-reproduce`.

## Per-claim verification commands

| Paper section | Command | Expected output |
|---|---|---|
| §1 Introduction (524-section coverage claim) | `yuho ci-report` | "524/524 sections at L1+L2; 524/524 author-stamped at L3" |
| §5 Coverage | `make verify-coverage` | per-chapter breakdown matching `paper/sections/evaluation.tex` Table 5.1 |
| §5 SCC findings | `yuho refs --scc --json` | 4 non-trivial cycles: s292↔s293, s85↔s86, s424A↔s424B, s304B↔s74A |
| §5 Fidelity diagnostics | `python scripts/paper_methodology.py` | regenerates `paper/methodology/{fidelity_hits,throughput,gap_frequency}.json` |
| §5 Encoding throughput | `python scripts/paper_methodology.py` | same script — emits the throughput stats |
| §7 AKN OASIS XSD round-trip | `make verify-akn-xsd` | "AKN round-trip: 524/524 validate clean" |
| §7.5 Z3-driven scenario synthesis | `make verify-bulk-contrast` | "143 candidate pairs, 115 landed (100% subsumes, 79% referenced)" |
| §7.6 LLM benchmark | `make verify-evals` | FakeClient at 100% on all 205 fixtures |
| §7.8 Case-law differential testing | `make verify-case-law` | top-1 30.4% / mean F1 0.188 / consistency 100% |
| Paper smoke build | `make -C paper smoke` | 32-page PDF at `paper/main_smoke.pdf` |
| §6.6 Mechanisation | `cd mechanisation && lake build` | Lean 4 lib typechecks; Lemmas 6.2 + 6.4 kernel-checked. Requires `elan` (Lean toolchain manager). |

## Expected wall-clock times (clean container, 2025-vintage laptop)

| Step | Time |
|---|---|
| `docker build` | 5-8 minutes (cold, mostly Python deps) |
| `make verify-coverage` | 30 seconds |
| `make verify-akn-xsd` | 90 seconds (524 sections × xmllint round-trip) |
| `make verify-evals` (FakeClient) | 5 seconds |
| `make verify-case-law` | 60 seconds (Z3 solver per fixture) |
| `make verify-bulk-contrast` | 10 minutes (143 Z3 contrasts) |
| `make -C paper smoke` | 90 seconds (3-pass LaTeX) |
| **End-to-end `make paper-reproduce`** | **~5 minutes** |

## What's *not* reproduced by `make paper-reproduce`

These steps are heavy enough to live separately:

- **Full corpus build with rendered SVGs** — `python scripts/build_corpus.py` followed by `python scripts/render_svg_cache.py --workers 8`. Takes ~10 minutes with mmdc + Chrome installed (see `editors/explorer-site/build/`). Required only if you want to rebuild the explorer site.
- **Full LLM benchmark against a real model** — needs `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`. The FakeClient end-to-end above confirms the *runner* works; real-LLM scores require credentials and are reported separately at `evals/results-<model>.json`.
- **Full IPC / MPC scrape (§8)** — `python scripts/scrape_indiacode.py act --out library/indian_penal_code/_raw/act.json`. Takes ~1 hour at the 6 s/request crawl-delay convention. Independent of paper-reproduce since the encoded library doesn't yet ship the IPC data.

## Reproducing the paper PDF

```sh
make -C paper smoke      # ~90s — article-class build, basic TeX Live
make -C paper paper      # ~3 min — full acmart manuscript (needs latexmk + acmart)
```

The smoke build is what `make paper-reproduce` includes by default;
the full acmart build needs additional CTAN packages and is
documented under `paper/Makefile`.

## Versioning

The paper's headline numbers are pinned to the Yuho version at the
git commit recorded in `paper/main_smoke.tex` near the top under
`% commit:`. To reproduce a specific paper version, check out that
commit and re-run `make paper-reproduce`.

The encoded library's per-section `metadata.toml` carries the same
version pin so any single statute can be traced to the exact Yuho
version that produced it.

## NOT legal advice

Every reproducibility command produces structural-shape outputs.
None of them is legal advice. The paper is explicit on this point;
this document inherits the same disclaimer.
