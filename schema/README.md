# Yuho schemas

This directory contains the closed machine-readable boundaries used by the Haskell release:

- `request.schema.json` and `result.schema.json` cover the seven specialised KernelInput v1 variants;
- `typed-finite-rules-request.schema.json` and `typed-finite-rules-result.schema.json` cover `TypedFiniteRules-v1`;
- `model-bundle-*.schema.json` retain the bounded offline package/review checks used by section 84 assurance records;
- `core-yuho-conformance-v0.*.json` map public constructs to parser, checker, Core, lowering, kernel, explanation, diagram and test evidence.

The protocol suites under [`test/`](../test/) validate schemas, accepted and rejected requests, canonical bytes and persistent-process recovery. Model-bundle schemas are auxiliary assurance tooling, not another `.yh` implementation or kernel variant.

See [Formal semantics](../docs/formal-semantics.md), [Mechanisation](../docs/mechanisation.md), and [Architecture](../docs/architecture.md).
