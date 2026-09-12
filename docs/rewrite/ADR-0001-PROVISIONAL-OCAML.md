# ADR-0001: Provisional OCaml preference for the Yuho rewrite

**Status:** Provisional; comparative spike pending  
**Date:** 12 September 2026  
**Owner:** Yuho maintainer  
**Supersedes:** No accepted ADR

## Context

Yuho currently ships a Python 5.1.0 CLI/LSP, Tree-sitter C parser, AST-dependent runtime/exporters, Canonical IR v1.2 and bounded Lean models. The [repository audit](REPOSITORY-AUDIT.md) found no closed production/proof wire format, no proof of whole-program correctness and no measured Yuho host-language comparison. The maintainer has authorised free redesign of the new surface language; current .yh is migration evidence and a differential oracle, not a permanent syntax obligation. The first replacement is a closed Boolean semantic kernel behind a versioned subprocess, with Tree-sitter and Python parser retained initially.

## Provisional decision

Prefer **OCaml** for the production implementation **if** it passes the identical [OCaml-versus-Haskell spike](LANGUAGE-SPIKE-SPEC.md) and is not materially worse on reviewed clarity, resource use, packaging or proof-boundary mapping. Ordinary variants/records/modules and explicit validation are the default; advanced GADTs or module machinery require a demonstrated reduction in invalid states. Dune and Menhir/Sedlex are candidate build/parser choices after language selection, not authorised scaffolding or an immediate parser replacement. Proof tooling is selected independently.

This preference is an engineering hypothesis, not a claim that OCaml is intrinsically faster, easier for coding agents or stronger in proof assurance than Haskell. External tooling precedent can justify a probe; only repository-specific measurements and maintainers' review can settle this ADR. The prior report's weighted 8.95-versus-8.38 score and 0.80 confidence did not come from a Yuho spike and are not accepted evidence.

## Evidence that would confirm OCaml

Both candidates use the same yuho.kernel-protocol/v1, KernelInput v1 and frozen fixtures. OCaml would be confirmed if it passes all mandatory parity, deterministic serialization, parser-diagnostic transport and packaging gates; meets cold-start/RSS thresholds; presents a clear finite All/Any/subsection implementation with no hidden partial operations; preserves IDs, spans and trace edges in the Lean-neutral proof vector; and Haskell supplies no material advantage after two-reviewer inspection. The scorecard must include raw measurements, diffs and build/install transcripts.

## Evidence that would reverse the preference

Choose Haskell if it passes all mandatory gates while OCaml fails one after a bounded correction attempt, or if both pass but Haskell yields materially clearer reviewed invariants and proof mapping without an operational regression. A sustained Haskell advantage in cold-start and RSS may support reversal when code clarity is comparable. Maintainer fluency, reproducible packaging and reliable debugging of actual Yuho fixture failures are decision evidence; claims about language popularity or theoretical type-system power alone are not.

If neither candidate passes, keep the ADR provisional, investigate the failed boundary or revise the spike, and do not begin a broad rewrite. If both pass every mandatory gate with no material clarity, proof-boundary, packaging, latency or memory advantage, maintainer preference decides the technical tie. The maintainer currently leans toward Haskell; that preference is evidence about maintainability, not a reason to bias the spike. The ADR remains provisional until the maintainer reviews the scorecard and both independent clarity reviews. No production-code change follows from this provisional ADR.

## Consequences while provisional

Keep Canonical IR v1.2 and its source/semantic/artifact hash semantics unchanged. Specify a separate KernelInput v1, make ClosedBooleanBranches-v1 the first production/proof fragment, then AcyclicGuardedExceptions-v1. Keep Tree-sitter/Python parsing behind the common subprocess until replacement gates pass. Treat section 84 plus CPC disposition as a later reviewed product slice, not the first parity oracle. Preserve the existing CLI/LSP/schema/export/packaging workflows temporarily under the [migration contract](MIGRATION-CONTRACT.md), while the new surface language can change freely.
