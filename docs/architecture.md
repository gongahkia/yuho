# Architecture

Yuho is one Haskell application rooted at [`yuho.cabal`](../yuho.cabal).

```text
.yh bytes
  → lexer and source-located surface AST
  → exact-version module/name resolution
  → static checking and resource bounds
  → normalized Core Yuho
  → KernelInput v1 lowering
  → in-process kernel evaluation
  → technical result, explanation, or semantic diagram
```

`Yuho.Surface` owns parsing, resolution, legal declaration kinds, modules, temporal interval selection, scenarios and cases. `Yuho.CoreYuho` contains normalized finite semantic types and pure operations. `Yuho.Kernel` and the seven specialized protocol namespaces evaluate eight closed variants. `Yuho.Diagram` derives a semantic graph from checked normalized data. `Yuho.Corpus` validates and queries the canonical Singapore coverage artifact. `Yuho.Release` provides repository discovery, doctor, starter initialization and manifest verification.

## Modules and composition

A module declares a stable name and exact authored version, explicitly exports named declarations, and keeps other declarations private. A host imports with an alias and explicitly uses or attaches qualified declarations. Import alone neither executes a rule nor attaches an exception. Resolution is deterministic, bounded to a safe local root and rejects cycles, collisions, private access, wrong kinds and inconsistent legal identities.

Module versions identify authored content; they do not select law by conduct date. Temporal selection is a separate frontend operation over explicit non-overlapping half-open intervals and a supplied conduct date. Neither module nor temporal metadata leaks into equivalent KernelInput bytes.

## Kernel boundary

The eight variants are `ClosedBooleanBranches-v1`, `AcyclicGuardedExceptions-v1`, `TypedBooleanFacts-v1`, `GuardedPenaltySelection-v1`, `PenaltyTerms-v1`, `SuppliedProofStatus-v1`, `RegisteredPresumptionDerivations-v1`, and `TypedFiniteRules-v1`. They share KernelInput v1 framing but retain closed request/result shapes. Cases contain ordered independent requests rather than a merged case verdict.

Candidate sanctions are presentations, not sentences. Normative positions and responsibility routes elaborate into typed finite rules. Presumption derivation remains separate from evidence assessment. No layer constructs guilt, liability, conviction, acquittal, sentence or criminal-procedure disposition.

## Repository layout

- `app/`, `src/`, `test/`, `schema/`: Haskell product, tests and schemas.
- `examples/`: current language examples and retained semantic fixtures.
- `mechanisation/`: Lean semantics, theorem registries and conformance evidence.
- `research/singapore/`: executable models, cases, coverage, saved sources and scoped review records.
- `library/penal_code/`: saved structural Penal Code export used by the coverage inventory.
- `docs/`: current product documentation and retained native diagram/protocol artifacts.
- `release/`: capability, diagnostic, schema and release manifests.

Test-only Python scripts orchestrate schema validation, frozen protocol replays and independent Haskell–Lean comparisons. They do not parse or execute `.yh` in the supported product path.
