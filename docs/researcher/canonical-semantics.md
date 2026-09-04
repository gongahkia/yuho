# Yuho Canonical Semantics

This page defines the contract between Yuho syntax, AST construction, type
checking, runtime evaluation, verifiers, and transpilers.

Yuho lowers a parsed module to `yuho.canonical-ir` version `1.0` before
semantic analysis, runtime evaluation, and verifier lowering. The artifact has
a deterministic semantic serialization/hash and a separate optional
normalized source-text hash. It is not a proof of legal correctness or of equivalence
between every backend.

The required durable boundary is:

```text
grammar/CST -> versioned canonical IR -> semantic analysis -> runtime
            -> backend lowerings -> exports
```

Parser acceptance is not a semantic or backend guarantee. A consumer must be
classified as `modeled`, `ast_adapter`, or `unsupported` for each IR feature;
unsupported combinations produce a structured `YIR…` diagnostic.

## Semantic Order

1. Parse `.yh` source with `src/tree-sitter-yuho/grammar.js`.
2. Build immutable AST nodes from `src/yuho/ast/nodes.py`.
3. Lower them with `src/yuho/ir/canonical.py` into Canonical IR v1.0.
4. Run canonical capability checks and AST-adapter type/lint analysis.
5. Evaluate the covered runtime fragment through `evaluate_canonical`.
6. Lower through a named adapter to verifiers and exports, or reject the
   unsupported feature/backend pair.

Backend output is not canonical by itself. The trust boundary is the lowering
from checked canonical semantics into that backend. The v1 adapters are only a
retained-test boundary; they are not an equivalence proof.

## Construct Matrix

The machine-readable construct matrix lives at
`tests/fixtures/conformance/constructs.json`.

Each public grammar rule must have a matrix row containing:

- parse node
- AST node or syntax component
- type-rule status
- runtime-rule status
- Z3 status
- Alloy status
- Lean status
- transpiler obligations

`tests/test_conformance_matrix.py` fails when a public grammar rule is added,
removed, or left without semantic/backend status fields.

Backend parity claim rows live at
`tests/fixtures/backend_parity/claims.json`. The report generator
`scripts/verify_backend_parity.py` reads that fixture, and tests verify that
the fixture, capability metadata, and status docs stay aligned.

## Backend Status Policy

Use these status meanings consistently:

- `modeled`: implemented in the backend for the documented fragment.
- `metadata`: preserved for traceability but not executable.
- `unsupported`: rejected or reported explicitly, not silently approximated.
- `experimental`: emitted with known gaps and not part of canonical semantics.
- `not directly modeled`: consumed through a parent construct or irrelevant to
  that backend.
- `ast_adapter`: deliberately consumes canonical IR but delegates the named
  transition surface to an AST implementation; it is not a modeled claim.

## Current Canonical Boundaries

Runtime:

- Canonical IR v1 models statutes, provision paths, requirement trees, and
  element burden metadata. The public AST entry point lowers immediately and
  records the semantic IR hash in `EvaluationResult`.
- Expression execution and exception handling still use a required AST adapter.
- Subsection branch execution and guarded/sibling penalty selection currently
  fail closed with a runtime capability diagnostic until their dedicated IR
  evaluators are complete.
- Calendar durations with years/months require a reference date for exact
  ordering.
- Money arithmetic is Decimal-based, currency-aware, and rejects implicit
  rounding.

Z3:

- Enters through a canonical-IR adapter and records the IR hash used for the
  lowering. Its current statute/expression/penalty adapter is not a parity
  claim for unmigrated semantics.
- Conformance-tested for retained criminal-statute verification fixtures.
- Penalty duration bounds use exact runtime month-end clamping when a
  verifier reference date is supplied; otherwise calendar units use explicitly
  labeled approximate day counts.
- Case-law semantics and typed fact burden/proof-standard metadata are
  explicitly rejected by Z3 consistency checking rather than silently encoded.

Alloy:

- Secondary bounded-shape backend. It rejects canonical subsection semantics
  at the boundary and rejects its other unsupported verifier features with its
  detailed diagnostics. It is not a parity trust boundary for penalties,
  case-law, typed burden metadata, cross-section reasoning, or exception
  priority/defeat semantics.

Lean:

- Proof-bearing for the mechanised fragment documented in
  `../../mechanisation/README.md`.
- Does not consume production canonical IR v1; its entire v1 capability
  surface is explicitly unsupported pending the bounded refinement work.
- Not a proof of full Yuho source semantics.

Transpilers:

- JSON should preserve AST structure or make loss explicit.
- Legal-facing exports should retain source traceability and avoid inventing
  executable meaning from opaque text.

## Change Rule

When adding a grammar construct, update this chain in the same change:

1. parser grammar and CST shape
2. canonical-IR representation, version, deterministic serialization, and
   capability status
3. named AST adapter while the migration remains incomplete
4. type or lint behavior
5. runtime/verifier status
6. transpiler status
7. `tests/fixtures/conformance/constructs.json`
8. focused tests for the highest-risk implemented layer
