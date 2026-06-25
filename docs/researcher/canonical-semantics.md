# Yuho Canonical Semantics

This page defines the contract between Yuho syntax, AST construction, type
checking, runtime evaluation, verifiers, and transpilers.

Yuho's canonical executable semantics are the Python AST plus semantic checker
plus runtime evaluator for the covered fragment. Z3, Alloy, Lean, and export
formats are projections from that model unless a backend document explicitly
states a narrower fragment.

## Semantic Order

1. Parse `.yh` source with `src/tree-sitter-yuho/grammar.js`.
2. Build immutable AST nodes from `src/yuho/ast/nodes.py`.
3. Run type inference/checking and statute lint.
4. Evaluate executable statute elements against facts with the runtime
   evaluator.
5. Project the checked AST to verifiers and transpilers.

Backend output is not canonical by itself. The trust boundary is the encoder
from the checked AST into that backend.

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

## Current Canonical Boundaries

Runtime:

- Canonical for core expressions, literals, struct values, function calls,
  basic statute element satisfaction, and fixed-unit duration comparison.
- Calendar durations with years/months require a reference date for exact
  ordering.
- Money arithmetic is Decimal-based, currency-aware, and rejects implicit
  rounding.

Z3:

- Conformance-tested for retained criminal-statute verification fixtures.
- Penalty duration bounds use exact runtime month-end clamping when a
  verifier reference date is supplied; otherwise calendar units use explicitly
  labeled approximate day counts.
- Case-law semantics and typed fact burden/proof-standard metadata are
  explicitly rejected by Z3 consistency checking rather than silently encoded.

Alloy:

- Secondary bounded-shape smoke backend. Unsupported verifier features fail
  explicitly; Alloy is not a parity trust boundary for penalties, case-law,
  typed burden metadata, cross-section reasoning, or exception priority/defeat
  semantics.

Lean:

- Proof-bearing for the mechanised fragment documented in
  `../../mechanisation/README.md`.
- Not a proof of full Yuho source semantics.

Transpilers:

- JSON should preserve AST structure or make loss explicit.
- Legal-facing exports should retain source traceability and avoid inventing
  executable meaning from opaque text.

## Change Rule

When adding a grammar construct, update this chain in the same change:

1. parser grammar
2. AST builder/node
3. type or lint behavior
4. runtime/verifier status
5. transpiler status
6. `tests/fixtures/conformance/constructs.json`
7. focused tests for the highest-risk implemented layer
