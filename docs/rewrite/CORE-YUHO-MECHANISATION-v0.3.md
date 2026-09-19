# Core Yuho v0.3 Mechanisation Report

Core Yuho v0.3 adds a small Lean 4 model for normative applicability, candidate-sanction shapes and actor-attributed responsibility routes. It imports the v0.2 finite status and priority calculus rather than defining a competing evaluator.

## Sources and theorem inventory

- Semantics: `mechanisation/Yuho/CoreYuho/ReleaseV03.lean`.
- Registry checks: `ReleaseV03TheoremRegistry.lean` and `core-yuho-theorems-v0.3.json`.
- Axiom audit: `ReleaseV03Audit.lean`.
- Independent vectors: `ReleaseV03Conformance.lean` and `conformance/core-yuho-v0.3.json`.

The eleven registered theorems are:

1. `normative_applicability_deterministic`;
2. `normative_applicability_total`;
3. `explicit_normative_conflict_symmetric`;
4. `no_norm_inference_from_missing_declarations`;
5. `specified_bounds_valid_when_ordered`;
6. `candidate_sanction_structure_preserved`;
7. `actor_route_isolation`;
8. `irrelevant_actor_environment_extension`;
9. `explicit_route_required_for_cross_actor_effect`;
10. `legacy_participation_elaboration_compatible`; and
11. `legacy_attempt_elaboration_compatible`.

They contain no `sorry`, `admit` or project axiom. The axiom audit reports the standard Lean kernel assumptions, if any, for the selected theorem declarations; it is not a proof of the Haskell compiler.

## Conformance boundary

The retained `yuho.core-conformance-v0.3` corpus has 33 semantic input vectors. Haskell evaluates them through `Yuho.CoreYuho.Conformance`; Lean evaluates the same inputs through an independently generated checked module. The orchestration compares canonical result bytes. Expected results are not generated once and supplied to both evaluators.

Run:

```sh
make verify-core-yuho-v03-conformance
python3 scripts/verify_core_yuho_theorems.py
```

The trusted boundary includes the Lean kernel/toolchain, GHC and Haskell runtime, each implementation's vector decoder, the deterministic vector-to-Lean generator, the canonical JSON comparison script and the checked source files. The generator performs schema translation but not legal reasoning.

## Claim boundary

Machine checking covers the named finite definitions and theorems. Bounded cross-implementation conformance covers the retained inputs. Parsing, module filesystem resolution, source-location diagnostics, all elaboration paths, SVG layout, Singapore legal interpretation, factual truth and legal currency remain outside the proof. The justified claim is: Core Yuho v0.3 has machine-checked finite semantics for its documented release fragment with independent bounded Haskell–Lean conformance.

