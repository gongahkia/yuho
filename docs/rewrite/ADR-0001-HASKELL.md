# ADR-0001: Haskell for the Yuho production implementation

**Status:** Accepted by the Yuho maintainer, 12 September 2026  
**Scope:** Production implementation language, beginning with `ClosedBooleanBranches-v1`  
**Evidence:** [frozen scorecard](../../experiments/language-spike/results/SCORECARD.md), [independent review](../../experiments/language-spike/results/INDEPENDENT-REVIEW.md), [migration contract](MIGRATION-CONTRACT.md)

## Decision

Use **Haskell** for Yuho's new production implementation. Begin in [rewrite/haskell](../../rewrite/haskell/README.md) with a closed, versioned KernelInput/Result v1 subprocess and only `ClosedBooleanBranches-v1`. Keep the current Python CLI, LSP, Tree-sitter parser, AST, exporters, corpus tooling and Canonical IR v1.2 unchanged during coexistence. The new source language is a later, separate design decision; legacy `.yh` syntax is migration evidence, not a permanent grammar promise. Retain both frozen candidate prototypes and the original comparative evidence.

## Evidence and tradeoff

Both spike candidates passed every mandatory protocol, byte/structural parity, deterministic serialization, parser-diagnostic transport, trace, packaging and proof-vector gate. The separate non-implementing runtime scored Haskell **4.33/5** and OCaml **4.15/5** for clarity; both exceed the 4/5 threshold. Its review replayed OCaml 15/15 locally, inspected the complete Haskell source and originating-host evidence, and could not rebuild Haskell because GHC/Cabal were unavailable in that review environment. The maintainer accepts the review's Haskell recommendation as the maintainability decision; no second numerical maintainer code-review score is asserted.

OCaml's measured advantages remain evidence: cold median **2.060 versus 4.713 ms**, cold median peak RSS **3,822 versus 8,130 KiB**, 1,000-request elapsed **417.1 versus 887.6 ms**, steady peak RSS **6,736 versus 9,704 KiB**, clean offline build **0.436 versus 3.001 s**, and fewer runtime shared-library dependencies on the measured Fedora x86_64 host. Haskell's executable was 2,998,272 bytes versus OCaml's 3,094,112 bytes. The relative operational differences are real; the absolute cold-start difference is about 2.65 ms and 4.2 MiB, with both candidates far inside the agreed 250/500 ms and 128 MiB gates. The one-host sequence always measured Haskell first, so the figures are comparative observations rather than a distribution guarantee. At the present kernel scale they do not outweigh Haskell's clearer reviewed failure/semantic flow, smaller core, narrow API, and the maintainer's long-term language preference. Future parser, LSP, trace-volume and packaging measurements remain necessary.

## Architectural guardrails

Use ordinary ADTs, newtypes, explicit modules and `Either`/validation results first. Keep module exports small, effects at the subprocess boundary, and `Text` versus UTF-8 `ByteString` ownership explicit. Treat strictness as a measured choice. Strong warnings are errors. Avoid partial semantic functions and advanced type/effect frameworks unless a concrete invariant and review justify them. Use maintained JSON and SHA-256 libraries, explicit canonical encoding, duplicate-key rejection, bounded parsing, and in-process closed-shape/invariant checks. A rejected or unsupported request must never become a negative legal result. The [independent review](../../experiments/language-spike/results/INDEPENDENT-REVIEW.md) identifies the shared protocol gaps that the production foundation must close.

Haskell's type system does **not** make Yuho automatically pure, correct or legally faithful, nor does it supply a formal verification result. Proof-tool choice is independent: existing Lean work is a bounded baseline, not a production correspondence proof, and Lean, Rocq or F* require a named reference relation and an explicit implementation bridge before such a claim. No Z3 or proof-tool work is authorised by this ADR.

## Reversal conditions

Reopen this ADR if repository-specific evidence shows a material Haskell-specific failure that a bounded repair cannot resolve: a native parser/LSP route missing reviewed recovery, incremental-editor, formatter or UTF-8 span gates; platform packaging or operational memory/latency failing declared targets; semantic scaling/trace retention becoming impractical on representative supported cases; or a proof-correspondence bridge becoming materially harder or less trustworthy than an alternative. Compare the same fixtures, acceptance criteria and maintenance effort before reversing. OCaml remains a viable measured alternative; the frozen prototype is not production code.

The separately approved [AcyclicGuardedExceptions-v1 technical fragment](ACYCLIC-GUARDED-EXCEPTIONS-V1.md) follows the initial Boolean foundation; it does not change this language ADR or select a proof tool. Typed facts, penalties, outcomes, CPC packages, new syntax and Python retirement still require separate decisions and gates. Section 84 plus CPC disposition remains a later legally reviewed product slice.
