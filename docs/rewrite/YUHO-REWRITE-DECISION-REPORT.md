# Yuho rewrite language decision

**Status:** Provisional recommendation; implementation language undecided  
**Date:** 12 September 2026  
**Decision owner:** Yuho maintainer  
**Recommendation:** Compare OCaml and Haskell on the same Yuho fixtures and protocol; OCaml is a provisional engineering hypothesis, not an automatic tie-break.

## Decision in context

Yuho should migrate in stages from the Python 5.1.0 toolchain to a small, typed semantic kernel. The maintainer has authorised free redesign of the new surface language. Existing .yh syntax, parser quirks and exact export bytes are migration evidence, not permanent language obligations. Reviewed semantic behaviour needs equivalence or an explicit recorded correction. [MIGRATION-CONTRACT.md](MIGRATION-CONTRACT.md) makes this distinction concrete.

OCaml remains the **provisional** production-language preference. Variants, modules, strict evaluation and compiler tooling appear suitable for the proposed small kernel. Haskell can express the same invariants and may prove clearer or easier to package. There is no measured Yuho OCaml-versus-Haskell result, nor evidence of maintainer proficiency in either. The earlier numerical ranking and 0.80 confidence were judgments, not measurements; they are withdrawn as decision evidence. [ADR-0001-PROVISIONAL-OCAML.md](ADR-0001-PROVISIONAL-OCAML.md) records the reversal criteria.

## Repository facts that constrain the choice

The current product is a Python CLI and stdio LSP with a Tree-sitter C parser, Python AST builder, Canonical IR v1.2, runtime evaluator, optional in-process Z3, an Alloy/Java subprocess and bounded Lean models. The package defines the yuho and yuho-lsp executables in [pyproject.toml](../../pyproject.toml). The builder consumes Tree-sitter node types, UTF-8 byte spans and doc comments. The LSP uses incremental parsing, although analysis reparses. These are migration costs; a native parser is not needed for the first kernel.

Canonical IR v1.2 is not a closed executable wire format. It stores opaque AST snapshots for some descriptions, exceptions and penalties, omits source spans, and runtime and verifiers still take AST adapters ([canonical.py](../../src/yuho/ir/canonical.py), [statute_evaluator.py](../../src/yuho/eval/statute_evaluator.py)). Its semantic hash excludes source_hash; its artifact hash includes it. Both use compact sorted-key UTF-8 JSON. **Do not change v1.2 fields or hash semantics.** The initial new boundary is separately versioned **yuho.kernel-input/v1**, a closed typed subset with explicit source IDs/spans, validation failures and canonical results. No v1.2 hash is comparable to a KernelInput digest merely because both use SHA-256. A later IR v1.3 remains possible after its schema and migration rules are reviewed.

The first production/proof correspondence claim is **ClosedBooleanBranches-v1**: finite closed named Boolean requirements, recursive All/Any, inherited subsection paths, sibling alternatives, a total Boolean fact map and definition-only failure. It excludes arbitrary expressions, exceptions, penalties, outcomes and external dependencies. The next fragment is **AcyclicGuardedExceptions-v1**, after registered target resolution, same-fact context, guard order, cycles and unresolved status have explicit semantics. Typed facts and guarded penalties are subsequent extensions. Singapore Penal Code section 84 with a Criminal Procedure Code disposition is a later product-discriminating slice: cross-Act packages and that CPC corpus are open work (#63/#66), outcomes are partial (#51), and present s84 Boolean-fact tests do not establish doctrine or procedure.

The checked-in 524 Singapore Penal Code .yh files and 4,192 text-export snapshot hashes are valuable coverage and migration data, not 524 legally reviewed executable conclusions or independent semantic assertions. Existing Lean artefacts are handwritten bounded models; their fixture generator flattens subsections and substitutes guard atoms. Python/Lean structural comparisons are not a proof of production-evaluator correspondence. Runtime, Z3, Alloy, Lean and exporter support must be reported separately. The README's unqualified whole-language verification wording cannot be inherited as a rewrite claim. See the [repository audit](REPOSITORY-AUDIT.md).

## Compatibility disposition

| Category | Decision | Examples |
|---|---|---|
| Semantic behaviour to preserve | Compare reviewed judgments and structured traces; correct known errors explicitly. | Ancestor requirements, alternative leaves, definition-only failure, supported Boolean/typed-fact evaluation, registered acyclic guards, unresolved dependencies, guarded penalty source IDs and limited case effects. |
| Temporary migration compatibility | Keep Python workflows operational behind versioned process boundaries until replacements pass their gates. | Current .yh reader/formatter, CLI, LSP, facts JSON, diagnostic codes, CI JSON, SARIF, JUnit, AST JSON, exports/source maps and wheel/installer paths. |
| Intentionally redesigned behaviour | Specify and version new behaviour; record old/new fixture divergences. | New syntax and pragma, parser mitigation Y0103, export prose/whitespace, legacy overall_satisfied projection, full proof-status algebra, typed outcomes and cross-Act doctrine. |

The current universal exit-code table is not implemented uniformly: check can return 0 for warning-only results, lint uses 2, verify also uses 2 for unavailable/invalid prerequisites, and Click uses 2 for usage errors. A prospective per-command contract must be reviewed before cutover. The detailed compatibility inventory is [MIGRATION-CONTRACT.md](MIGRATION-CONTRACT.md).

## Comparative language spike

Both candidates must implement the **same yuho.kernel-protocol/v1** one-line UTF-8 JSON stdin/stdout request/response, consume the **same yuho.kernel-input/v1** fixtures, and emit the same canonical result schema and ordered diagnostics. The legacy Python parser/projector is the identical subprocess adapter for both. Candidate-native parsers are separate experiments and cannot bias semantic comparison. The exact fixtures, workloads, measurement method, thresholds and decision rubric are in [LANGUAGE-SPIKE-SPEC.md](LANGUAGE-SPIKE-SPEC.md).

The spike measures implementation clarity, cold-start latency, peak RSS, deterministic serialization, parser diagnostic preservation, trace parity, packaging and proof-boundary ergonomics. Passing the small fragment does not imply whole-backend parity, legal correctness or whole-program proof. The language decision becomes final only after reviewed results and an ADR update.

If both candidates satisfy every mandatory gate and neither has a material clarity, proof-boundary, packaging, latency or memory advantage, the maintainer's preference decides the result. The maintainer currently leans toward Haskell; that is legitimate maintainability evidence and must not alter fixtures, effort, measurements or reporting. Two independent clarity reviews remain required before a final choice.

## Formal-methods decision

Proof tooling is independent of the production language. Keep Lean's existing work as evidence, then compare a small Lean reference evaluator with Rocq or F* only once the **same closed fragment and trace relation** are defined. Report four assurance levels separately: host-language type/smart-constructor validation; property and differential tests; Z3 agreement on an explicitly supported common subset; and a kernel-checked theorem about a named formal model. Production-implementation correspondence additionally needs a verified bridge or explicitly bounded conformance argument. Solver agreement and generated Lean fixtures alone do not supply it.

The first theorem target is a reference-level property for ClosedBooleanBranches-v1, such as deterministic branch results on well-formed closed input. A later refinement theorem must state how parsed KernelInput and executable code relate to the Lean model. AcyclicGuardedExceptions-v1 follows with missing targets, cycles and unsupported guards represented explicitly rather than collapsed to false.

## Migration and retirement gates

Retain Tree-sitter and the Python parser/AST builder initially behind the versioned subprocess protocol. Replace them with Menhir/Sedlex only after new-syntax grammar/diagnostics are specified, generated artefacts are reproducible, Unicode byte spans and doc-comment/source-map handling pass, malformed-input recovery and editor incremental tests pass, accepted/rejected migration fixtures have reviewed dispositions, and LSP/formatter consumers run against the replacement. A Haskell win permits its native parser under the same gates. Two authoritative parsers require a shared acceptance and recovery suite.

The Python CLI, LSP, runtime, verifiers, exporters and corpus tools retire independently only after supported workflows and machine schemas have replacement owners, reviewed divergences, regression tests and packaging checks. The CLI inventory is doctor, init, check, ci-report, upgrade, lint, fmt, ast, transpile, diff, test, verify, debug, explain, irac, literate, refs, schema, completion; the second executable is yuho-lsp. New commands do not automatically replace these workflows.

This document authorises no implementation scaffolding, grammar regeneration, corpus migration, v1.2 change or Python retirement.
