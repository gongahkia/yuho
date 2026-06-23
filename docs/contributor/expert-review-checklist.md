# Expert Review Checklist

Use this before claiming a Yuho feature is semantically supported. A feature is
not complete just because it parses or transpiles.

## Canonical Semantics

- What is the canonical rule for this construct?
- Is it stated in `docs/researcher/formal-semantics.md` or a successor
  canonical semantics doc?
- Does the implementation match that rule, or is there an explicit caveat?

## Proof Boundary

- Which layer is trusted: parser, AST builder, runtime evaluator, Z3 encoder,
  Alloy encoder, Lean model, transpiler, or source map?
- Is there a test that catches encoder drift?
- Are solver/tool assumptions documented?

## Opaque Text

- Is executable meaning encoded as predicates, types, or graph edges?
- Which parts remain human-readable strings only?
- Does lint warn when opaque text is used in executable mode?

## Backend Parity

- Does runtime evaluation agree with Z3 on representative facts?
- Does Alloy either encode the construct or fail with an explicit diagnostic?
- Does Lean cover the construct, or is the gap documented?
- Does `yuho verify --capabilities --json` expose the backend status honestly?

## Fact Model

- Are facts typed?
- Are source, date, jurisdiction, evidential status, burden, standard of proof,
  and provenance represented when the feature depends on them?
- Does explanation output show why the fact satisfies the legal element?

## Case Law And Doctrine

- Does the feature distinguish statute text, definition, holding, ratio,
  obiter, treatment, and citation?
- Can treatment such as overruling or distinguishing change a result in a test?
- Are priority rules explicit?

## Cross-Section Semantics

- Are `apply_scope` and `is_infringed` resolved through a bounded registry?
- Are cycles diagnosed?
- Are substituted facts type-checked before runtime?

## Numeric And Temporal Semantics

- Are currencies, rounding, units, intervals, and calendar arithmetic exact
  enough for the claim being made?
- Are approximations visible in docs and diagnostics?

## Transpiler Conformance

- Does each emitted target have source-map coverage for elements and exceptions?
- Does the target preserve the semantics Yuho claims, or is it export-only?
- Is the output included in snapshot or round-trip tests?

## Corpus Methodology

- Which corpus sections exercise this feature?
- Does `make verify-coverage` still pass?
- Does a representative rich `test_statute.yh` exist?
- Are review gaps tracked instead of hidden in generated output?
