# Contributing to Yuho

Yuho welcomes focused changes to its Haskell language, Lean semantics, native diagrams and Singapore research corpus. Read the [README](../README.md), [architecture](../docs/architecture.md), [language reference](../docs/language-reference.md) and [assurance boundary](../docs/assurance.md) before changing semantics.

## Development setup

Use GHC 9.8.4, the checked-in Cabal freeze file and Lean 4.10.0 from `mechanisation/lean-toolchain`.

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
cabal v2-test yuho-test --offline -j1 --with-compiler=ghc-9.8.4 --test-show-details=direct
```

Run `make protocols`, `make conformance`, `make lean`, `make corpus`, `make docs` and `make release-verify` for the boundaries touched by a change. `make verify` runs the complete current gate. Test-orchestration scripts require Python and `jsonschema`; the product executable does not.

## Change discipline

- Keep the Haskell parser, checker, normalized Core, lowering, explanation and diagrams aligned.
- Extend Lean definitions and the theorem/conformance registries when Core semantics change.
- Preserve KernelInput and retained response bytes unless the change explicitly versions a boundary.
- Use saved sources for corpus work; never invent doctrine or upgrade structural coverage to executable coverage without support.
- Keep supplied facts distinct from computation, legal interpretation, evidence assessment and judicial outcomes.
- Add source-located refusal tests for invalid syntax and resource excess.
- Update the current docs rather than adding milestone or handoff reports.

Before opening a pull request, run `git diff --check`, describe skipped verification, and confirm generated artifacts are current. Follow the [Code of Conduct](../CODE_OF_CONDUCT.md) and report security issues through the private channel in [SECURITY.md](../SECURITY.md).
