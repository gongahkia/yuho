# Core Yuho Language Report v0.2 — Typed Finite Rules

Status: normative for the additive typed-finite-rules fragment implemented by the authoritative Haskell frontend. Core Yuho v0.1 remains normative for the criminal-law constructs and seven historical kernel variants described in the [v0.1 report](CORE-YUHO-LANGUAGE-REPORT-v0.1.md). This report adds a finite rule calculus; it does not replace those constructs or prove the complete compiler.

## 1. Layers and claim boundary

The v0.2 path is:

```text
typed-rules-model / typed-rules-module / typed-rules-case
  -> Haskell lexer and source locations
  -> exact-version local module selection
  -> nominal name, scope and type checking
  -> TypedFiniteProgram (normalized finite Core)
  -> TypedFiniteRules-v1 KernelInput
  -> in-process Haskell evaluation
  -> technical proposition states, explanation and native semantic graph
```

Facts and scalar values are supplied. Predicate, comparison, quantifier, cardinality and rule resolution are deterministic computations over those supplied values. Citations, reasons and limitations are explanatory metadata. Missing required inputs, private or wrong-kind module references, type errors, cycles and resource excess are rejected. Yuho does not extract facts from prose, assess evidence, infer legal authority, determine applicable law, decide guilt or liability, convict, acquit, sentence or enter a court disposition.

Finite quantifiers could be expanded into v0.1 `all` and `any`, but scalar operands, exact cardinality intervals, binding witnesses and explicit rule-conflict states cannot be preserved by any of the seven historical variants. v0.2 therefore adds one versioned variant, `TypedFiniteRules-v1`. It leaves KernelInput v1, Canonical IR v1.2 and all historical variants unchanged.

## 2. Semantic domains

All accepted collections are finite and ordered. Let:

```text
Id, TypeId, EntityId, PredicateId, ScalarId, PropositionId, RuleId, ModuleId
  = source identifiers of at most 128 Unicode code points

Truth = {T, F, U}
Class = {proved, not_proved, unresolved(reason)}
Polarity = {establish, defeat}
PredicateKind = {conduct, circumstance, mental-state, relationship}
CardinalityKind = {at-least, at-most, exactly}
PropositionState = {established, defeated, conflict, unresolved, not_established}
```

`proved`, `not_proved` and `unresolved` project to `T`, `F` and `U`. Reasons do not create another truth value.

Nominal types are equal only when their `TypeId`s are equal. There are no structural subtypes or implicit casts. A finite entity environment `E : EntityId -> TypeId` defines the domain `D(t) = [e | E(e)=t]` in declaration order.

Scalar types and values are:

```text
ScalarType ::= integer | date | enum EnumId [Member] | money Currency
ScalarValue ::= integer Z | date ISODate | enum EnumId Member
              | money Currency MinorUnits | unresolved(reason, ScalarType)
```

Money uses non-negative integer minor units and a three-uppercase-letter authored currency code. It never uses binary floating point or currency conversion. Dates are parsed ISO `YYYY-MM-DD` calendar days; the language does not infer a legal timezone or commencement rule.

## 3. Normalized syntax

The executable representation is `Yuho.CoreYuho.TypedFinite.TypedFiniteProgram`:

```text
Term ::= entity EntityId | variable VariableId

Expr ::= predicate PredicateId [Term]
       | compare Comparison ScalarId ScalarId ScalarId?
       | all [Expr] | any [Expr] | not Expr
       | forall VariableId TypeId Expr
       | exists VariableId TypeId Expr
       | cardinality CardinalityKind Nat [Expr]
       | reference RequirementId

Rule ::= RuleId [VariableId : TypeId] Polarity PropositionId Expr Citation?
Priority ::= higher RuleId lower RuleId
GroundFact ::= PredicateId [EntityId] Truth Reason

Program ::= ModelId [EntityType] [Entity] [PredicateSignature]
            [ScalarDeclaration] [PropositionId] [(RequirementId, Expr)]
            [Rule] [Priority] [GroundFact] (ScalarId -> ScalarValue)
            [ModuleRecord] [Limitation]
```

A typed-rules case is an ordered list of 1–32 allegation IDs, each containing an independently checked `Program`, plus explicitly named ground facts copied only into listed allegations. It has no aggregate status.

The module record retains exact name, `major.minor.patch` version, alias and explicit typed exports for explanation and diagrams. Module metadata is not evaluated by the kernel.

## 4. Static semantics

Judgments use `Γ` for declaration namespaces, `Δ` for entity types and entities, `Σ` for scalar declarations, `Π` for predicates, `Q` for requirements, `R` for rules and `V` for bound variables.

### 4.1 Names and nominal types

```text
Γ(TypeId) = entity-type                    Γ |- TypeId type
Γ(EntityId) = entity(TypeId)               Γ |- EntityId : TypeId
Π(PredicateId) = (t1,...,tn), 1 <= n <= 4  Γ |- PredicateId : t1*...*tn
```

Namespaces must be unique at their declaration kind. An entity argument checks only against the identical nominal type. A variable occurrence is valid only under the closest quantifier or rule parameter binding with the required type. Free variables and shadowing are errors.

### 4.2 Expressions

```text
Π(p)=(t1,...,tn)  Γ,V |- ai:ti for every i
------------------------------------------------ PRED
Γ,V |- p(a1,...,an) : Truth

Σ(x)=τ  Σ(y)=τ  comparison defined for τ
------------------------------------------------ CMP
Γ |- compare(x,op,y) : Truth

Γ,V[x:t] |- body : Truth
----------------------------------------------- FORALL / EXISTS
Γ,V |- forall x:t body : Truth
Γ,V |- exists x:t body : Truth

Γ,V |- ei : Truth for every i  k >= 0  members nonempty
------------------------------------------------ CARD
Γ,V |- cardinality(kind,k,[ei]) : Truth
```

`all` and `any` use the v0.1 three-valued operations. Their empty identities are `all([])=T` and `any([])=F`. Quantifiers inherit those identities, so `forall` over an empty nominal domain is `T` and `exists` is `F`. Cardinality source forms require at least one member.

`eq` and `neq` accept equal scalar types. Ordered comparisons accept integer, date or one money currency; enums support only equality and inequality. `in-half-open(value,lower,upper)` requires three dates. Unknown scalar IDs, mismatched enum types or currencies, missing assignments and malformed dates are rejected. An explicitly unresolved compatible operand evaluates to `U`.

Requirement references must resolve and be acyclic. Rule parameters are finite nominal domains. Conclusions must name declared technical propositions. Priority endpoints must name rules, priorities are explicit, and the priority graph must be acyclic. Source order never creates priority.

### 4.3 Modules and cases

A module identity is `(ModuleId, exact SemVer)`. A host import binds it to one unique alias. `use kind alias::id` succeeds only if the imported file explicitly exports `id` at `kind`. Non-exports are private; wrong-kind uses, duplicate identities/aliases and final declaration collisions are errors. Selection is deterministic in authored import/use order and never silently renames a legal ID.

Typed-finite v0.2 supports a single explicit host composition layer. Imported typed-rules modules may independently declare mutually referential fragments that become well typed in the composed host; nested imports inside such a module are rejected. Ordinary Core Yuho v0.1 statutory modules retain their separately documented recursive resolver. Entities are declared in models/modules in v0.2; scenarios supply ground classifications and scalar values, not new domain members.

Each case allegation is checked against the same named model and its own scenario. A shared fact is copied only into allegations that explicitly `use` its ID and is checked again at each destination. Results are keyed and presented in authored order, but no result becomes an input to another allegation.

## 5. Dynamic semantics

### 5.1 Three-valued operations and negation

| `all` | T | F | U |
|---|---:|---:|---:|
| T | T | F | U |
| F | F | F | F |
| U | U | F | U |

| `any` | T | F | U |
|---|---:|---:|---:|
| T | T | T | T |
| F | T | F | U |
| U | T | U | U |

`not(T)=F`, `not(F)=T`, and `not(U)=U`. This is explicit technical negation, never negation-as-failure.

### 5.2 Predicates, values and quantifiers

For ground key `p(e1,...,en)`, evaluation reads its supplied classification. Absence is an error, not `F`. A known compatible scalar comparison returns `T` or `F`; an explicitly unresolved operand returns `U`. Half-open membership is `value >= lower AND value < upper`.

```text
eval(forall x:t body, b) = all [eval(body,b[x:=e]) | e in D(t)]
eval(exists x:t body, b) = any [eval(body,b[x:=e]) | e in D(t)]
```

Substitution is lexical, nominally typed and capture avoiding because the checker forbids shadowing. Explanations retain satisfying entities and counterexample entities; unresolved bindings remain visible through the expression status.

### 5.3 Cardinality

Let `s` be the number of `T` members and `u` the number of `U` members. The possible final count is `[s,s+u]`.

```text
at-least k = T if s >= k; F if s+u < k; U otherwise
at-most  k = T if s+u <= k; F if s > k; U otherwise
exactly  k = T if s=k and u=0;
             F if s>k or s+u<k; U otherwise
```

### 5.4 Rules and explicit priority

A parameterless rule body is evaluated once. A parameterised rule enumerates the Cartesian product of its finite nominal parameter domains and combines instance statuses with `any`; its satisfying bindings are retained as witnesses.

For proposition `p`, only rules concluding `p` are relevant. A rule `r` is blocked when an opposite-polarity rule `h` is transitively higher than `r` and `h` is `T` or `U`. An active rule is `T` and unblocked.

```text
active establish and active defeat -> (U, conflict)
one or more active establish       -> (T, established)
one or more active defeat          -> (F, defeated)
no active rule, but a U rule or a blocked T rule -> (U, unresolved)
otherwise                          -> (F, not_established)
```

Thus an unresolved higher conflicting rule blocks a lower satisfied rule; incomparable satisfied opposite polarities produce an explicit conflict. A priority says only what the author declared for this finite technical program. It does not infer legal hierarchy, repeal, temporal applicability or authority.

## 6. Lowering and protocol

Checked `Program`s lower canonically to KernelInput v1 with fragment `TypedFiniteRules-v1`. The normalized program contains no filesystem path, module alias or timestamp. The variant independently re-decodes a closed object, revalidates finite limits and evaluates the same pure operations. Results contain expression, rule and proposition observations; proposition states remain separate from supplied classifications.

The seven v0.1 variants remain: `ClosedBooleanBranches-v1`, `AcyclicGuardedExceptions-v1`, `TypedBooleanFacts-v1`, `GuardedPenaltySelection-v1`, `PenaltyTerms-v1`, `SuppliedProofStatus-v1` and `RegisteredPresumptionDerivations-v1`. No historical request is migrated to the new fragment.

## 7. Bounds and diagnostics

The surface rejects before publishing a request or diagram when any bound is exceeded:

| Resource | Bound |
|---|---:|
| Source/module bytes | 65,536 |
| Exact imports | 32 |
| Entity types | 32 |
| Entities total / per type | 256 / 64 |
| Predicate declarations / arity | 128 / 1–4 |
| Scalar declarations | 256 |
| Ground applications | 1,024 |
| Quantifier nesting | 4 |
| Rules / priority edges | 128 / 256 |
| Allegations | 1–32 |
| Generated normalized nodes | authored `limit`, 1–2,048 |
| Identifier length | 128 characters |

`SFT001`–`SFT014` identify syntax, duplicates, unknown names, arity/kind errors, type errors, variable scope, priority cycles, scalar values, cardinality thresholds, limits, missing inputs, limitations, unsafe local paths and export visibility. Kernel validation failures use `KTF001`. Output publication is atomic.

## 8. Properties and evidence

| Property | Evidence |
|---|---|
| Six binary comparison operations, negation, finite quantifier and cardinality totality/determinism | Lean definitions and theorem registry v0.2; date half-open membership is the checked Haskell composition of `>=`, `<` and `all` and is fixture-tested rather than a separate Lean constructor |
| Negation involution; quantifier/cardinality permutation invariance | Mechanically proved in Lean |
| Typed substitution preservation | Mechanically proved for normalized typed applications |
| Quantifier expansion agrees with v0.1 `all`/`any` | Mechanically proved |
| Cardinality exclusivity and satisfied boundaries | Mechanically proved; all lists of size 0–4 and thresholds 0–5 independently conformance-tested |
| Priority resolution determinism | Mechanically proved for the executable finite graph function under the stated acyclicity predicate |
| Higher defeat, unresolved higher blocking and incomparable conflict | Mechanically proved for the two-rule cases; chains and diamonds independently conformance-tested |
| Actor/exception and allegation isolation | Existing v0.1 Lean theorems plus v0.2 selected-key conformance vectors |
| Haskell–Lean semantic agreement | Bounded independent conformance, not a universal refinement proof |
| Surface-to-Core preservation and Core-to-kernel preservation | Tested on fixtures; not mechanically proved |
| Parser, module filesystem lookup, source spans, explanations and diagram completeness/layout | Tested only |
| Legal correctness or factual truth | Not claimed and not mechanised |

The exact theorem inventory is `mechanisation/core-yuho-theorems-v0.2.json`; the retained input corpus uses `yuho.core-conformance-v0.2`. Neither evidence source establishes that a Singapore-law model is doctrinally correct.

## 9. Explicitly deferred features

The language has no open or infinite domains, structural subtyping, implicit casts, arbitrary recursion, higher-order predicates, general arithmetic, currency conversion, negation-as-failure, inferred priority, unrestricted defeasible logic, natural-language extraction, evidence credibility assessment, automatic legal research or legal-currency selection. Typed-finite rules do not automatically elaborate existing offence/exception declarations into generic propositions; the established criminal-law constructs remain compatible alongside the additive fragment.
