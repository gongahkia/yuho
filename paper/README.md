# Yuho — research paper

Skeleton for the Yuho research paper. arXiv-style preprint, attributed,
acmart `manuscript` mode.

## Layout

```
paper/
  main.tex              # entry point, metadata, abstract, \input wiring
  references.bib        # seeded citations (Catala, lam4, LexScript, AKN, etc.)
  Makefile              # paper / stats / figures / arxiv / clean
  .gitignore            # latex aux + generated stats.tex
  scripts/
    gen_stats.py        # coverage.json -> stats.tex
  sections/
    introduction.tex
    background.tex
    design.tex
    implementation.tex
    evaluation.tex
    related.tex
    limitations.tex
    conclusion.tex
  figures/              # *.mmd (Mermaid sources) -> *.pdf via mmdc
    architecture.mmd
    penalty-tree.mmd
    exception-priority.mmd
```

Sections are skeletons: outline + structured `\todo{...}` markers in red
in the rendered PDF, ready to be expanded paragraph-by-paragraph.

## Build

```sh
cd paper
make stats     # regenerate stats.tex from ../library/penal_code/_coverage/coverage.json
make figures   # render Mermaid sources to PDF (requires mmdc)
make paper     # latexmk -> build/main.pdf -> ./main.pdf
make watch     # live rebuild (latexmk -pvc)
make arxiv     # arxiv.tar.gz for upload
make clean     # remove build artefacts
```

## Requirements

- `latexmk`, `lualatex`, `acmart.cls` (full TeX Live, or
  `brew install --cask mactex`)
- `mmdc` for figures (`npm install -g @mermaid-js/mermaid-cli`)
- `python3` for `make stats` and `make arxiv`

## Stats injection

`stats.tex` is regenerated from `../library/penal_code/_coverage/coverage.json`
before each build. `main.tex` falls back to hard-coded values if `stats.tex`
is missing, so `pdflatex main.tex` works standalone in a pinch.

## Venue retargeting

This is `manuscript,nonacm` (preprint mode). For ICAIL/JURIX submission,
swap the documentclass line in `main.tex`:

```tex
\documentclass[sigconf,review,anonymous]{acmart}    % ICAIL / Onward!
\documentclass[lncs]{llncs}                         % JURIX (Springer LNCS)
```

For LNCS, also remove the `\IfFileExists{stats.tex}` block (LNCS doesn't
play well with manuscript-mode commands) and replace with hard-coded
`\newcommand` values, or keep as-is and accept a warning.
