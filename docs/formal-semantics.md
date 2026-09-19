# Core Yuho formal semantics

This is the cumulative specification for the finite Core used by Yuho Haskell Research Language v1.0. Internal schema labels `v0.1`, `v0.2`, and `v0.3` identify additive proof and conformance boundaries; they are not separate user-facing languages.

## 1. Layers and semantic boundary

```text
authored norm / responsibility-route / candidate sanction
  -> source-located Haskell parser and static checker
  -> normalized v0.3 metadata plus existing Core rule or sanction node
  -> TypedFiniteRules-v1 or PenaltyTerms-v1 KernelInput
  -> in-process Haskell evaluation
  -> technical status, explanation and native semantic graph
```

A norm or route carries reviewable source identity, actor and kind metadata. Its executable condition is an existing finite requirement. The checker elaborates the construct into an explicitly named finite rule; the original metadata is retained for explanation and diagrams but does not change the kernel schema. Candidate sanctions use the penalty-term Core and kernel forms. Module names, citations and limitations remain contextual metadata.

No construct assesses evidence, infers a norm from silence, transfers responsibility between actors, determines guilt or liability, or imposes a sentence.

## 2. Semantic domains and normalized syntax

The three-valued domain is `Truth = {T,F,U}`, written `satisfied`, `not_satisfied`, and `unresolved`. Proposition states are `{established, defeated, conflict, unresolved, not_established}`. Identifiers, module names, actors, roles, contexts, citations, source spans, entity types, entities, predicate signatures, scalar names and rule IDs are finite checked atoms.

```text
Expr ::= input InputId
       | all [Expr]
       | any [Expr]
       | not Expr
       | predicate PredicateId [Term]
       | compare Comparator Scalar Scalar
       | forall Variable EntityType Expr
       | exists Variable EntityType Expr
       | cardinality Bound Nat [Expr]

Declaration ::= definition DefinitionId Expr
              | offence OffenceId Expr
              | exception ExceptionId Expr
              | participation ParticipationId Expr
              | attempt AttemptId Expr ConductStage
              | presumption PresumptionId Trigger Rebuttal
              | penalty PenaltyId Guard Sanction
              | proposition PropositionId
              | rule RuleId Polarity PropositionId Expr

Case ::= ordered finite list of AllegationId × Target × scoped environment
```

Primitive proof assignments are external `proved`, `not_proved`, or `unresolved` classifications mapped to `T`, `F`, or `U`. Known scalar values are exact integers, ISO dates, finite enum members, or currency-tagged integer minor units. Explicitly unresolved scalars make dependent comparisons `U`; missing required values are a static/input error, never false.

Modules have a stable name and exact `major.minor.patch` authored version, explicit exports, exact-version imports with aliases, and qualified references. Module and source metadata guide frontend resolution but are not evaluated by the kernel. Temporal expressions are complete rule expressions paired with half-open intervals `[from,to)`; a scenario-supplied conduct date selects exactly one checked interval.

## 3. Static judgments

The principal judgments are:

```text
M; Γ ⊢ ref ⇓ declaration-kind       name and export resolution
Γ ⊢ expr : proposition              expression typing
Γ ⊢ declaration ok                  declaration well-formedness
Γ ⊢ attachment : target×actor×context
Γ ⊢ fact-binding : destination-type
Γ ⊢ case isolated
Γ ⊢ intervals unique
Γ ⊢ priorities acyclic
```

Resolution is deterministic over a bounded local module root. Unsafe paths, missing or mismatched versions, import cycles, duplicate aliases, private access, wrong declaration kinds, and structurally inconsistent exported legal identities are rejected. Requirement and definition dependencies must be acyclic. Predicate arity and every argument’s nominal type must match its signature; scalar comparators require compatible types and money currencies.

Exception attachments must identify a compatible technical target, actor or role, instance and act context. Shared facts may bind only to compatible primitive destinations; derived outputs cannot be transferred between allegations. Offence, participation and attempt targets form a closed typed sum. Every case has 1–32 uniquely identified allegations and evaluates each with its own scoped environment.

Quantifier variables have lexical scope, cannot shadow, and range only over the finite declared domain of their nominal entity type. Priority edges name known conflicting rules, are explicit rather than source-order-derived, and form an acyclic graph. Candidate sanctions have valid closed term shapes and ordered bounds. Resource limits are checked before lowering.

## 4. Dynamic semantics

For finite lists, the complete base truth tables are:

| `all` | T | F | U |
|---|---|---|---|
| **T** | T | F | U |
| **F** | F | F | F |
| **U** | U | F | U |

| `any` | T | F | U |
|---|---|---|---|
| **T** | T | T | T |
| **F** | T | F | U |
| **U** | T | U | U |

`all [] = T`, `any [] = F`, and strong negation maps `T↦F`, `F↦T`, `U↦U`. A definition evaluates its acyclic expression under the supplied environment. Finite `forall` is the `all` of each capture-avoiding typed substitution; finite `exists` is the corresponding `any`.

For a collection with `s` satisfied members and `u` unresolved members:

- `at-least k` is T if `s ≥ k`, F if `s+u < k`, otherwise U;
- `at-most k` is T if `s+u ≤ k`, F if `s > k`, otherwise U;
- `exactly k` is T if `s=k ∧ u=0`, F if `s>k ∨ s+u<k`, otherwise U.

An ordinary satisfied branch is defeated only by a satisfied attached exception guard. A not-satisfied exception does not defeat it; an unresolved applicable guard makes the technical result unresolved. The lookup key includes actor, instance and act context, so another actor or inactive instance cannot affect the selected branch.

Participation and attempt reuse finite requirements but remain separate targets. The three bounded participation routes are instigation, conspiracy and intentional aid. Attempt conduct stage is supplied as preparation only, act towards commission, or unresolved; target-offence completion is not inferred. A registered presumption evaluates to exactly inactive, active, rebutted, or unresolved from its supplied trigger and rebuttal classifications, separately from offence status and evidence assessment.

A rule whose body is T contributes its authored establish/defeat polarity; F is inactive and U remains blocking where a higher conflicting rule could apply. Explicit acyclic priority can defeat a lower conflicting satisfied rule. Incomparable satisfied opposite polarities produce conflict; source order never chooses a winner. Rules unrelated to a proposition are irrelevant.

Each allegation evaluates independently under its compatible inputs. A case result is an ordered mapping from allegation ID to technical result and constructs no aggregate status. Reordering allegations may reorder presentation but does not change that mapping.

## 5. Normative positions, responsibility and sanctions

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

### Static semantics

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

### Dynamic semantics

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

## 6. Frontend relations and lowering

Norms and routes lower as rules and priorities to `TypedFiniteRules-v1`. Their review metadata is frontend-owned. Rich sanction terms lower to `PenaltyTerms-v1`. Exact-version module resolution, temporal selection, scenario expansion and case orchestration are frontend relations; they do not become hidden kernel semantics.

Specialised participation and attempt retain their stable lowering and frozen bytes. The shared route representation is additive and does not alter existing requests.

## 7. Properties and evidence

The cumulative theorem registry contains 79 declarations covering three-valued algebra, finite evaluation, exceptions and isolation, presumptions, cases, temporal selection, typed comparisons, quantification, substitution, cardinality, priority, normative applicability, sanctions and actor routes. The retained conformance corpora contain 95, 2,518 and 33 vectors evaluated independently by Haskell and Lean.

This establishes the finite mathematical definitions named by those theorems. Parser correctness, full surface-to-Core preservation, Core-to-kernel refinement, diagram layout, legal interpretation, source currency and corpus correctness remain tested or unverified—not mechanically proved.
