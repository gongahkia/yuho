# Getting started

Yuho Haskell Research Language v1.0 checks, compiles, runs, explains and diagrams finite authored `.yh` models. It evaluates supplied classifications and values; it does not assess evidence or decide legal outcomes.

## Prerequisites

- GHC 9.8.4;
- Cabal compatible with the checked-in `cabal.project.freeze`;
- the frozen dependencies already available locally when using offline mode;
- Lean 4.10.0 through the checked-in `mechanisation/lean-toolchain` only when rebuilding proofs.

## Build

From the repository root:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
YUHO="$(cabal list-bin exe:yuho --offline --with-compiler=ghc-9.8.4)"
"$YUHO" version
"$YUHO" doctor --root "$PWD"
```

The normal CLI is entirely Haskell and has no network or external-renderer dependency.

## Create a project

```sh
"$YUHO" init /tmp/yuho-starter
find /tmp/yuho-starter -maxdepth 2 -type f -print | sort
```

The starter contains an exact-version module, a typed model, a scenario, a case and a README. `init` creates the directory atomically and refuses any existing destination.

## Check, compile, run and explain

```sh
"$YUHO" check /tmp/yuho-starter/model.yh --scenario /tmp/yuho-starter/scenario.yh
"$YUHO" compile /tmp/yuho-starter/model.yh --scenario /tmp/yuho-starter/scenario.yh
"$YUHO" run /tmp/yuho-starter/model.yh --scenario /tmp/yuho-starter/scenario.yh
"$YUHO" explain /tmp/yuho-starter/model.yh --scenario /tmp/yuho-starter/scenario.yh
"$YUHO" check /tmp/yuho-starter/case.yh
```

`check` performs parsing, resolution and static validation. `compile` emits canonical KernelInput bytes. `run` invokes the kernel in process. `explain` gives a structured technical derivation and repeats the no-judicial-outcome limitation.

## Draw the checked model

```sh
"$YUHO" diagram /tmp/yuho-starter/case.yh \
  --view case --format svg --output /tmp/yuho-starter/case.svg
```

Use `--format json` for the deterministic semantic graph. The [diagram guide](diagrams.md) covers all four views.

## Explore the Singapore corpus

```sh
"$YUHO" corpus summary --corpus-root "$PWD"
"$YUHO" corpus show penal-code:84 --corpus-root "$PWD"
"$YUHO" corpus check --corpus-root "$PWD"
```

The corpus has 524 structurally indexed saved rows and a broad partial executable subset. Read [Corpus](corpus.md) before interpreting the counts.

## Verify the release

```sh
"$YUHO" release verify --root "$PWD"
python3 scripts/verify_core_yuho_theorems.py
python3 scripts/verify_core_yuho_conformance.py
python3 scripts/verify_core_yuho_typed_finite_conformance.py
python3 scripts/verify_core_yuho_v03_conformance.py
```

The Python commands above are test orchestration around independent Haskell and Lean evaluators. Python is not part of the Yuho production execution path.

Continue with the [language reference](language-reference.md), [CLI reference](cli-reference.md), and [assurance boundary](assurance.md).
