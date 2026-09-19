# Core Yuho Language Report v0.3 — Release Extensions

Status: normative for the three additive release constructs implemented by the Haskell frontend. This report extends [Core Yuho v0.1](formal-semantics.md) and [Core Yuho v0.2](formal-semantics.md); it does not replace their syntax, semantics or limitations.

## 1. Layers and semantic boundary

```text
authored norm / responsibility-route / candidate sanction
  -> source-located Haskell parser and static checker
  -> normalized v0.3 metadata plus existing Core rule or sanction node
  -> TypedFiniteRules-v1 or PenaltyTerms-v1 KernelInput
  -> in-process Haskell evaluation
  -> technical status, explanation and native semantic graph
```

A norm or route carries reviewable source identity, actor and kind metadata. Its executable condition is an existing finite requirement. The checker elaborates the construct into an explicitly named Core v0.2 rule; the original metadata is retained for explanation and diagrams but does not change the existing kernel schema. Candidate sanctions use the existing penalty-term Core and kernel forms. Module names, citations and limitations remain contextual metadata.

No construct assesses evidence, infers a norm from silence, transfers responsibility between actors, determines guilt or liability, or imposes a sentence.

## 2. Semantic domains and normalized syntax

The v0.1 three-valued domain is `Truth = {T,F,U}` and the v0.2 proposition states are `{established, defeated, conflict, unresolved, not_established}`.

```text
Modality ::= required | prohibited | permitted
ResponsibilityKind ::= principal-conduct | joint-conduct | instigation
                     | conspiracy | intentional-aid | attempt
                     | other:Identifier

Norm ::= NormId SubjectEntity Modality PropositionId RequirementId Citation?
Route ::= RouteId SubjectEntity ResponsibilityKind PropositionId
          RequirementId Citation?

Sanction ::= death | life-imprisonment
           | imprisonment LowerBound UpperBound Unit
           | fine Currency LowerBound UpperBound
           | caning LowerBound UpperBound strokes
           | all-of [Sanction]
           | exactly-one-of [Sanction]
           | one-or-more-of [Sanction]

Bound ::= not-stated | unbounded | specified Nat
```

`required` and `permitted` elaborate to `establish`; `prohibited` elaborates to `defeat`. Synthetic rule IDs are deterministic: `r:norm:<norm-id>` and `r:route:<route-id>`. An authored priority naming a norm or route is normalized to its synthetic rule ID before v0.2 acyclicity and conflict resolution.

Candidate sanctions are presentation trees. Alternative and cumulative constructors preserve authored structure. They do not select an actual sentence.

## 3. Static semantics

Let `E`, `P`, `Q` and `R` be the checked entity, proposition, requirement and rule environments.

```text
E(s)=person-like entity   P(a)=proposition   Q(q)=Truth
modality in Modality
------------------------------------------------------ NORM
E,P,Q |- norm n subject s modality action a when q

E(s)=entity  P(t)=proposition  Q(q)=Truth
kind in ResponsibilityKind  s occurs in q
------------------------------------------------------ ROUTE
E,P,Q |- route r subject s kind target t when q
```

IDs are unique at their declaration kind. Norm IDs use the `n:` prefix and routes use `route:`. Subjects must resolve to declared typed entities; actions and targets must resolve to named technical propositions. A route body must mention its subject, preventing a route whose attributed actor is absent from its finite requirements. These checks do not infer that the authored route is legally sufficient.

Norms and routes count against separate limits of 64 each and the existing 128-rule, 64-priority-edge and 2,048-node limits after elaboration. Priorities must name known rules, norms or routes, may not self-reference, and must form a finite acyclic graph.

Module exports and uses add declaration kinds `norm` and `responsibility-route`. Import alone has no semantic effect. Visibility, exact-version identity, final-name collision and deterministic source-order rules are those of v0.2.

Candidate term IDs are unique inside a candidate. Specified lower bounds must not exceed specified upper bounds; caning uses non-negative integer strokes. Death and life imprisonment accept no numeric bounds. Unsupported sanction kinds fail parsing or checking; forfeiture and disqualification are not silently represented as fines or imprisonment.

## 4. Dynamic semantics

For norm `n` with condition `q`:

```text
evalNorm(n) = eval(q)
rule(n) = (r:norm:n, action(n), polarity(modality(n)), eval(q))
polarity(prohibited)=defeat
polarity(required)=polarity(permitted)=establish
```

Normative applicability is therefore total and deterministic for a well-typed finite program. Absence of a norm yields no rule and no inferred obligation or permission. Opposite active polarities use the exact v0.2 conflict and explicit-priority semantics. Permission does not inherently override prohibition. An unresolved higher opposite-polarity norm blocks a lower rule rather than allowing an arbitrary result.

For route `r`:

```text
evalRoute(r) = eval(requirement(r))
rule(r) = (r:route:r, target(r), establish, eval(requirement(r)))
```

Only the explicitly named subject and the facts referenced by that route body are read. No fact, relationship or result creates another actor's route. The route kinds are descriptive typed tags; the language gives none of them hidden doctrine.

Candidate-sanction evaluation preserves the authored tree and bound values. Existing guarded penalty selection may select a candidate technical branch, but this never becomes an imposed sentence. The forms do not model discretion, mitigation, aggravation, totality, consecutive/concurrent terms or procedure.

## 5. Lowering and compatibility

Norms and routes lower as v0.2 rules and priorities to `TypedFiniteRules-v1`. Their review metadata is frontend-owned. Rich sanction terms lower to `PenaltyTerms-v1`. No KernelInput version, Canonical IR version or historical variant changes.

Legacy participation and attempt keep their historical lowering and frozen bytes. The shared route representation is additive; it does not rewrite historical requests. Existing sources that do not use v0.3 retain their v0.1 or v0.2 explanation labels and byte output.

## 6. Properties and evidence

Eleven registered Lean theorems cover applicability determinism/totality, explicit-conflict symmetry, no inference from absent norms, ordered sanction bounds, sanction shape, actor-route isolation, irrelevant-actor extension, explicit routes and legacy participation/attempt elaboration. Thirty-three retained vectors are independently evaluated by Haskell and Lean.

This establishes the finite mathematical definitions named by those theorems. Parser correctness, full surface-to-Core preservation, Core-to-kernel refinement, diagram layout, legal interpretation, source currency and corpus correctness remain tested or unverified—not mechanically proved.
