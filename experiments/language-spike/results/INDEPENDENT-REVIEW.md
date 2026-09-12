# Yuho Language Spike — Independent Review

**Review status:** Complete  
**Review date:** 12 September 2026  
**Role:** Separate non-implementing runtime reviewer  
**Recommendation:** Select **Haskell** as Yuho's production implementation language  
**Confidence:** **0.68** (moderate; sufficient for an ADR, with explicit architectural guardrails)

## Executive conclusion

Both candidates satisfy every scored technical gate. OCaml is materially faster and smaller in relative runtime terms, but both implementations are so far below the product's limits that the absolute difference is not decision-dominant. Haskell is the clearer implementation in this spike, is substantially shorter, has the narrower exposed module boundary, and better matches the maintainer's long-term preference.

Select Haskell. Preserve the OCaml prototype and evidence bundle, but replace the provisional OCaml ADR with an accepted Haskell ADR. This is a product-engineering decision, not a claim that Haskell is intrinsically superior or formally verified.

The decision is conditional on keeping the Haskell architecture intentionally conservative: ordinary algebraic data types and modules first, explicit effects at the boundary, strictness informed by profiling, and no pervasive type-level or effect-framework machinery.

## Review scope and reproduction

The complete 81-path inventory and extracted source/evidence were reviewed. The OCaml executable was replayed locally against all 15 frozen fixtures and produced 15/15 byte-identical responses. The review environment did not contain GHC/Cabal, and the archive intentionally excluded Haskell build artefacts, so the Haskell executable was not independently rebuilt or executed. Its complete source, build transcript, hashes, proof vectors, and raw originating-host measurements were inspected.

Additional malformed-input probes were run against OCaml and traced to equivalent Haskell source paths. These exposed shared hardening gaps outside the scored fixtures. They do not invalidate the comparative spike, but they must be resolved before promoting either prototype into production.

## Independent scores

| Review dimension | Haskell | OCaml | Assessment |
|---|---:|---:|---|
| Semantic-rule traceability | 4.5/5 | 4.2/5 | Both map the branch rules directly; Haskell is more compact without obscuring evaluation order. |
| Type and failure-flow clarity | 4.4/5 | 4.2/5 | Both use closed variants/ADTs and explicit results. Haskell's `Either`/`traverse` path is slightly more concise. |
| Module/API discipline | 4.3/5 | 3.8/5 | Haskell exposes only `run` and `decodeFailure` from `Kernel`; OCaml has no `.mli` boundaries and suppresses the missing-interface warning. |
| Unsafe/partial-operation control | 4.1/5 | 4.1/5 | Both disclose bounded array access and avoid unchecked semantic lookup; both decode recursively before applying the node limit. |
| Reproducibility/failure walkthrough | 4.3/5 | 4.3/5 | The common fixtures, correction record, hashes, and commands are strong. |
| Proof-boundary ergonomics | 4.4/5 | 4.3/5 | Both map directly to a finite inductive model. Haskell's pure recursive evaluator has a small readability advantage; neither implements proof glue. |
| **Independent clarity mean** | **4.33/5** | **4.15/5** | **Both pass the required 4/5 threshold; Haskell leads modestly.** |

These scores cover the reviewed fragment, not future parsers, LSPs, solvers, or jurisdiction modules.

## Why Haskell wins the clarity review

The Haskell candidate uses Haskell 2010, no language extensions, no warning suppressions, and no advanced effect or type-level framework. It is 512 logical lines versus OCaml's 780. Some of the difference comes from Haskell using Parsec while OCaml implements JSON manually, so raw total LOC is not decisive. The central kernel is still smaller: 315 versus 398 logical lines.

The semantic path is direct:

- `leafBranches` expresses inherited conjunction and alternative descendant branches;
- `evaluateRequirement` evaluates every `All`/`Any` child in order and retains full trace evidence;
- `evaluateBranch` performs conjunction over inherited requirements;
- `run` performs validation before evaluation and makes definition-only failure explicit.

`Map` and `Set` make fact lookup and ID validation explicit and scalable. `Kernel` exposes a narrow public surface. The prototype demonstrates that Yuho does not need sophisticated GHC extensions to obtain a clear semantic core.

Haskell's main clarity debts are the 354-line `Kernel.hs`, use of `String` where `Text`/bytes should become explicit, the custom SHA implementation, and the protocol decoder being mixed with semantic types and evaluation. These are straightforward module-boundary problems rather than reasons to reject the language.

## OCaml's strengths

OCaml's variants and result pipeline are also clear. Strict evaluation makes its runtime behaviour easy to inspect, and the standard-library-only executable has fewer shared-library dependencies. OCaml handles parser stack overflow at its local JSON boundary, whereas the Haskell prototype does not establish an equivalent deep-input guard.

The operational results favour OCaml:

| Measure | Haskell | OCaml | OCaml reduction |
|---|---:|---:|---:|
| Cold median | 4.713 ms | 2.060 ms | 56.3% |
| Cold median peak RSS | 8,130 KiB | 3,822 KiB | 53.0% |
| 1,000-request elapsed | 887.6 ms | 417.1 ms | 53.0% |
| Steady peak RSS | 9,704 KiB | 6,736 KiB | 30.6% |
| Clean offline build | 3.001 s | 0.436 s | 85.5% |
| Executable size | 2,998,272 B | 3,094,112 B | Haskell is 3.1% smaller |

The relative advantage exceeds the spike's 25% observation threshold on several measures. The absolute deltas remain small: approximately 2.65 ms and 4.2 MiB at cold start, and about 0.47 ms per request in the 1,000-request run. Both candidates are dramatically inside the accepted limits. Yuho's expected bottlenecks are more likely to be parsing, corpus work, solver calls, trace volume, and legal-model complexity than a few milliseconds of kernel-process startup.

The timing session always measured Haskell before OCaml and was not counterbalanced. That does not explain away the consistent gap, but it limits precision. The performance evidence should be retained as an OCaml advantage rather than elevated to a decisive product constraint.

## Shared hardening findings

These findings apply to both candidates by direct source comparison. They are outside the frozen fixture set.

### 1. Kernel validation does not enforce the closed protocol schema

Both decoders ignore unknown object fields. An otherwise valid B06 request with an additional top-level field evaluates as `true`. The JSON Schema rejects that request, but the kernel documentation says each candidate performs its own invariant validation. Production must either validate the full closed shape in-process or narrow the claim and make schema validation an authenticated mandatory gateway.

### 2. Leaf members are silently discarded

In Haskell `decodeRequirement` maps a `Leaf` directly to `Right []`; OCaml does the same with `Leaf -> Ok []`. A malformed leaf containing `members` is accepted and its children disappear. It should be rejected as `KINV` rather than normalised silently.

### 3. Dates are shape-checked, not calendar-checked

Both kernels read `reference_date` as an unchecked string. `2026-99-99` evaluates successfully. Production should parse an actual date type and reject invalid dates canonically.

### 4. Parser acceptance can contradict its diagnostics

A `validate` request with `accepted=true` and an error-severity diagnostic returns status `true` while retaining the error. The protocol must specify and enforce whether an error diagnostic forces rejection.

### 5. `definitions` is decoded but does not determine provision kind

Both implementations classify any zero-branch program as `definition_only`, even if `definitions=false`. Either remove the field from this fragment or specify and validate its relationship to branch construction and `provision_kind`.

### 6. Spans are not validated against source bytes

Both check nonnegative/order/line minima but not whether byte offsets fit the source, whether displayed positions agree with UTF-8 text, or whether node spans are structurally nested. The first production protocol should define the required level of span validation.

### 7. Resource limits apply after recursive decoding

The node bound is checked after the entire recursive program is decoded. Deep hostile input can exhaust stack or memory before `max_nodes` is enforced. Add byte/line/depth limits at the protocol boundary and a bounded/iterative decoder strategy.

### 8. The local JSON and SHA implementations are spike artefacts

Both implementations reject valid JSON surrogate-pair escapes and implement SHA-256 locally. Production should use maintained, audited libraries for parsing/cryptography while retaining an explicit canonical encoder and duplicate-key policy.

## Proof-boundary assessment

Neither implementation has a formal advantage established by this spike. Both export identical proof vectors and require the same three conceptual steps: decode the vector, reconstruct facts/tree by stable IDs and ordered children, then check values and trace edges against a reference relation.

Haskell receives a small score advantage because the pure recursive evaluator and ADTs visually resemble the intended inductive semantics. This is not a proof bridge. A Lean, Rocq, or F* model still needs an explicit relation to production Haskell, and example agreement remains testing until that bridge is established.

The existing Lean work should remain the first proof-spike baseline. Do not select a proof tool merely because Haskell is selected for production.

## Decision rationale

The deciding factors are:

1. Both candidates satisfy every mandatory gate.
2. Both exceed the independent clarity threshold.
3. Haskell is modestly clearer and substantially shorter in this implementation.
4. OCaml's operational advantage is real but not material at Yuho's present scale.
5. Whole-toolchain parser/LSP risk is unresolved for both; Tree-sitter/Python remains in place.
6. The maintainer prefers Haskell, which matters for a long-lived solo research project once technical suitability is established.

Accordingly, the result is not a technical tie that defaults by historical ADR wording. It is a narrow Haskell win after technical parity.

## Conditions for production Haskell

The accepted Haskell ADR should require:

- ordinary ADTs/newtypes/modules before GADTs, DataKinds, type families, free monads, lens-heavy APIs, or effect frameworks;
- explicit module dependency direction and small export lists;
- `Text`/`ByteString` ownership documented at protocol and source boundaries;
- strict fields and profiling for retained IR/trace structures;
- maintained JSON and cryptographic libraries, with an explicit canonical JSON encoder;
- property and mutation tests for validation, trace order, inheritance, and unsupported-capability behaviour;
- process isolation for legacy parsing and initially for solvers/proof tools;
- retained Tree-sitter/Python parser and LSP until their separate retirement gates pass;
- no claim that host-language purity or type safety constitutes legal or formal correctness;
- a reversal ADR if later typed outcomes, proof correspondence, parser/LSP delivery, or packaging exposes a material Haskell-specific failure.

## Next step

1. Add this review to `experiments/language-spike/results/INDEPENDENT-REVIEW.md`.
2. Have the maintainer record a short maintainability assessment; a code-expertise score is not required to restate this review.
3. Accept an ADR selecting Haskell and record OCaml's measured operational advantages.
4. Freeze the spike unchanged as historical evidence.
5. Begin a production-foundation phase that hardens KernelInput/Result v1 and promotes only `ClosedBooleanBranches-v1` into a clean Haskell module layout.
6. Do not begin `AcyclicGuardedExceptions-v1` until the shared protocol gaps above are fixed and exception ordering is explicitly decided.
