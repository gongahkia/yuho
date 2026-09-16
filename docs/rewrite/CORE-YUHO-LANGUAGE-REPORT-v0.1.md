# Core Yuho Language Report v0.1

Status: normative for the bounded Haskell research language at the repository revision that contains this report. Core Yuho is formally specified here and implemented with tested conformance. This does not establish a whole-language implementation proof or legal-corpus correctness proof.

## 1. Scope and language layers

Core Yuho is the normalized semantic language between the checked Haskell `.yh` surface and the existing KernelInput v1 fragments. It is distinct from the legacy Python Canonical IR v1.2. The latter remains a compatibility boundary; neither representation is silently translated into the other.

The authoritative pipeline is:

```text
UTF-8 .yh
  -> lexer and source-located surface AST
  -> exact-version module/name resolution
  -> static checker
  -> normalized Core Yuho
  -> frontend selection/expansion
  -> existing KernelInput v1 variant(s)
  -> in-process Haskell kernel
  -> technical result
  -> explanation and semantic diagram
```

Parsing preserves tokens and locations. Resolution assigns one declaration to each reference. Checking rejects malformed or unsupported programs before normalization. Core normalization erases surface spelling that has no executable meaning but retains typed identities, citations, actors, contexts, attachments, selected module identities, temporal-selection reasons and supplied classifications. Lowering emits exactly the established protocol. Kernel evaluation supplies technical statuses. Explanations and diagrams consume checked/Core structures plus kernel results; they do not infer facts.

Executable information comprises primitive classifications, requirement trees, definition dependencies, rule targets, exception guards, participation/attempt branches, presumption registrations and candidate-penalty guards. Contextual metadata comprises authored burden/standard descriptions, limitations, purpose and explanatory text. Source identities, citations, quotes and spans are traceability information. Unsupported constructors, unbound or private names, wrong declaration kinds, cycles, incomplete inputs and incompatible actor/context bindings are rejected; they do not receive a default legal meaning.

Module resolution, temporal selection, scenario expansion and case expansion are frontend relations. Module versions and conduct dates are not kernel facts. A module version identifies authored bytes; it does not select legally applicable law. A temporal interval selects among authored assumptions; it does not determine legal currency.

## 2. Semantic domains

Let the following sets be finite UTF-8 strings accepted by the checker:

- `Id`, partitioned by typed prefixes such as facts, groups, rules, offences, exceptions, actors, roles, allegations and penalties;
- `Actor`, `Role`, `ActContext`, `Citation`, `SourceId`, `ModuleName`, `Version` and `Date`;
- `Kind = {offence, exception, participation, attempt}`;
- `Class = {proved, not_proved, unresolved(reason)}`;
- `Truth = {T, F, U}`;
- `TechnicalStatus = {satisfied, not_satisfied, unresolved, defeated, not_evaluated, rejected}`.

The classification projection is `[[proved]]=T`, `[[not_proved]]=F`, and `[[unresolved(r)]]=U`. Reasons are retained for explanation but do not add a fourth truth value.

## 3. Normalized abstract syntax

The executable Haskell types are in `Yuho.CoreYuho.Types`. The following grammar abstracts those types; brackets denote finite ordered lists and maps have unique keys.

```text
Req ::= input Id Citation Truth?
      | all Id [Req]
      | any Id [Req]

Element ::= element Id Category Citation
Definition ::= definition Id DefinitionKind [Citation] [Req] [DefinitionId] [OutputId]
Rule ::= rule Id TechnicalRuleId Kind [Citation] [Element] [Req]

Attachment ::= attachment InstanceId ExceptionId TargetId Actor? Role? ActContext?
ActorBinding ::= actor Actor Role
Relation ::= relation Id Endpoint Endpoint TargetOffence

PenaltyTerm ::= imprisonment Id Endpoint Endpoint Unit
              | fine Id Currency Endpoint Endpoint
              | all_terms Id [PenaltyTerm]
              | exactly_one Id [PenaltyTerm]
              | one_or_more Id [PenaltyTerm]
Penalty ::= penalty Id TargetRule SourceId Provision PenaltyTerm

Module ::= module ModuleName Version Alias [ExportedId]
Temporal ::= selected ExpressionId SelectionReason

Program ::= program ModelId Jurisdiction
            [Rule] [Definition] [Attachment] [Penalty]
            [ActorBinding] [Relation] [Req] (Id -> Truth)
            [Module] Temporal? [Limitation]

Presumption ::= presumption Id TargetInput SourceId TriggerInput RebuttalInput State
PresumptionProgram ::= presumption_program Id Bearer Standard Context
                       [Presumption] TechnicalStatus

Allegation ::= allegation Id Kind TargetId Role TechnicalStatus
SharedFact ::= shared_fact Id FactKind Subject Class [(AllegationId, InputId)]
Case ::= case Id Program [ActorBinding] [Allegation] [SharedFact]
```

`Req` is a tree after name resolution. A statutory definition has typed inputs, dependencies and outputs; its executable dependency rules are lowered through the checked definition graph. A mental-state target is a typed element whose target and definition kind were checked before Core construction.

The three bounded Penal Code s 107 routes are alternatives inside a participation rule: instigation, conspiracy plus pursuant conduct, and intentional aid. The s 109 consequence inquiry remains a distinct requirement. An attempt contains a target-directed mental-state input, supplied conduct-stage classification and target-completion scope annotation. Neither participation nor attempt inherits the completed target offence result.

An actor-scoped attachment names exactly one exception instance, subject role and act context. Candidate penalties are declarations about possible provision terms; `Penalty` never denotes an imposed sentence. Presumption standards and burden bearers are authored annotations, while trigger and rebuttal classifications drive only the registered technical derivation.

## 4. Static semantics

Judgments use `Γ` for visible declarations, `Μ` for resolved modules, `Α` for actor/role bindings, `Φ` for shared facts and `Δ` for definition dependencies.

### 4.1 Names and declarations

`Γ |- q => d : k` means qualified or compatible legacy-unqualified reference `q` uniquely resolves to declaration `d` of kind `k`. The rule requires one visible declaration, matching typed prefix and expected kind. Zero matches reject as unresolved/private; multiple matches reject as ambiguous. Resolution never silently renames a legal identity.

`Γ |- members(g) ok` holds when each member ID of group `g` resolves to one input or group, the group ID is unique and every referenced group is within the same checked graph. Empty groups are permitted by the low-level truth algebra but public rule shapes are constrained by their checker.

`Δ |- acyclic` holds when depth-first traversal of definition and rule dependencies has no back edge. It is a precondition to normalization and kernel evaluation.

### 4.2 Rules and targets

`Γ |- offence o ok` requires an offence-kind rule with checked elements/groups and unique technical IDs. `Γ |- participation p -> o ok` requires a participation declaration, compatible actors/endpoints and an existing offence target. `Γ |- attempt a -> o ok` analogously requires an attempt kind, target-directed intention, one supplied conduct-stage route and a compatible target offence.

`Γ; Α |- attach x to t for r at c as i ok` requires: `x` is an exception; `t` is an offence, participation or attempt of the declared target kind; role `r` is permitted by `t`; `c` has the corresponding principal, aid or attempt context kind; `i` is unique; and any scenario classification for `i` names the same actor and context. A simple attachment is the actor-free special case for a compatible offence graph.

### 4.3 Modules

`Μ |- import n@v as a => m` holds when `v` is exact `major.minor.patch`, the bounded local path derived from `n@v` is safe and regular, the declaration identity equals `n@v`, alias `a` is unique and the dependency graph is acyclic. Only explicitly exported `(kind,id)` pairs enter the importing namespace.

`Μ; Γ |- compose [d1..dn] => Γ'` requires compatible protocol, policy and burden metadata; unique legal identities; structurally identical repeated sources/quotes; resolved cross-module definition references; and at least one selected offence plus the bounded exception shape required by the current composed host. Composition order is the authored `use` order. Inconsistent duplicate identities reject.

### 4.4 Facts, cases and isolation

`Γ; Α |- fact f -> (a,i) ok` requires a primitive destination, matching fact kind, actor/relationship endpoints, target offence and, for exception inputs, instance and act context. Derived or final outputs are never bindable.

`Γ; Α; Φ |- allegation q ok` requires a member of the closed target sum `{offence, participation, attempt}`, a bound compatible role, complete allegation-local primitive classifications and at most 32 ordered allegations. IDs are unique. A case requires at least one allegation.

The allegation environment is copied, not shared by evaluation: `Env(q)=Local(q) union ExplicitBindings(q)`. No derived result from allegation `q1` appears in `Env(q2)`. Authored order affects output order only.

### 4.5 Presumptions, time and penalties

`Γ |- presumption p(t,tr,rb) ok` requires unique typed `p`, a primitive target `t`, primitive effective trigger/rebuttal inputs `tr` and `rb`, an existing source and an acyclic registered dependency graph. Evidence is not assessed.

`|- [from,to) interval` requires `from < to`; an open end has no later interval. Intervals are non-overlapping and gap-free within the authored sequence. `Intervals; conduct_date |- select e` holds only for the unique expression with `from <= date < to`; missing dates, zero matches and multiple matches reject.

`Γ |- penalty p -> r ok` requires a unique penalty ID, existing target rule/source, supported unit/currency endpoints and one of the closed term constructors. Unsupported sentence labels or term combinations reject.

## 5. Dynamic semantics

Evaluation is a deterministic function over a finite checked graph. Let `Eρ(e)` evaluate requirement `e` under total supplied map `ρ`.

### 5.1 Three-valued truth tables

`all` is conjunction and `any`/branch aggregation is disjunction in the following strong-Kleene tables:

| `all` | T | F | U |
|---|---:|---:|---:|
| **T** | T | F | U |
| **F** | F | F | F |
| **U** | U | F | U |

| `any` | T | F | U |
|---|---:|---:|---:|
| **T** | T | T | T |
| **F** | T | F | U |
| **U** | T | U | U |

Empty `all` is `T`; empty `any` is `F`. For lists, `all` returns `F` if any member is `F`, otherwise `U` if any is `U`, otherwise `T`. `any` returns `T` if any member is `T`, otherwise `U` if any is `U`, otherwise `F`.

```text
Eρ(input i) = ρ(i)
Eρ(all i es) = ALL(map Eρ es)
Eρ(any i es) = ANY(map Eρ es)
```

A missing `ρ(i)` is a validation/internal inconsistency, never `F`.

### 5.2 Definitions and rules

Definitions are evaluated in checked dependency order. A definition output receives the result of its normalized requirement tree; dependent inputs read that output. A rule branch conjoins inherited and direct requirements. Rule status is `ANY` over its branch statuses. A definition-only rule is reported separately and is not manufactured into an offence branch.

### 5.3 Exceptions

Guards are evaluated only after ordinary branch requirements are `T` in the existing proof fragment. For guard statuses `gs`:

| condition | guarded branch | reason |
|---|---|---|
| any `T` in `gs` | F | defeated |
| no `T`, any `U` | U | exception_unresolved |
| all `F` or no guards | T | satisfied |

If ordinary requirements are `F`, the branch is `F` without guard evaluation. If they are `U`, the branch is `U` without guard evaluation. An actor-scoped instance uses namespaced inputs and one `(actor, role, context, instance)` tuple; no other actor or act context can satisfy it.

### 5.4 Participation and attempt

Each s 107 route is a requirement branch. Participation route status is `ANY(instigation, conspiracy, intentional_aid)` after its route-specific requirements. The supplied s 109 consequence inquiry is a separate requirement and result label.

Attempt status conjoins the target-directed intention projection with the supplied `act_towards_commission` projection and required bounded scope. `preparation_only` maps the latter projection to `F`; an unresolved stage maps it to `U`. Target completion remains a separate scope classification. Attempt status does not imply target-offence completion.

### 5.5 Registered presumptions

For trigger `tr` and rebuttal `rb`:

| trigger | rebuttal | state |
|---|---|---|
| F | T/F/U | inactive |
| T or U | T | rebutted |
| T | F | active |
| otherwise | otherwise | unresolved |

For direct target `d` and route states `rs`, effective target is `T` if `d=T` or any route is active; otherwise it is `U` if `d=U` or any route is unresolved; otherwise `F`. Inactive and rebutted routes make no negative inference. This is a technical derivation from supplied classifications, not an evidence or burden finding.

### 5.6 Penalties and cases

A candidate penalty is selected only by its existing fragment's validated guard/support relation. Its term remains a candidate provision term. It is never an imposed sentence.

Case evaluation is pointwise:

```text
EvalCase([q1..qn]) = [Kernel(Lower(Expand(q1))), ..., Kernel(Lower(Expand(qn)))]
```

There is no fold into an aggregate case status. Results retain allegation order and independent request IDs.

## 6. Frontend relations and seven kernel variants

The current seven variants remain unchanged:

| Variant | Core/language relation |
|---|---|
| `ClosedBooleanBranches-v1` | Low-level compatibility boundary; Boolean predecessor of the authored proof surface. |
| `AcyclicGuardedExceptions-v1` | Low-level guarded-rule boundary; higher-level exceptions normally lower through supplied proof. |
| `TypedBooleanFacts-v1` | Low-level typed-fact boundary; generated internally by earlier compatibility paths. |
| `GuardedPenaltySelection-v1` | Low-level penalty-selection boundary; higher-level candidate penalties use its semantics through proof selection. |
| `PenaltyTerms-v1` | Candidate term algebra exposed by Haskell penalty syntax. |
| `SuppliedProofStatus-v1` | Primary lowering target for models, definitions, offences, exceptions, participation, attempts and allegation requests. |
| `RegisteredPresumptionDerivations-v1` | Directly authorable presumption technical subprogram. |

Exact module resolution and temporal selection occur before `Checked`. Scenario expansion produces a total primitive map. Case expansion produces one checked request per allegation. Core normalization records those frontend decisions for explanations and diagrams, but module identities and temporal metadata do not enter KernelInput. Equivalent modular and standalone checked graphs therefore retain byte-identical requests.

## 7. Properties and evidence status

The named obligations are:

1. **Evaluation determinism:** `Eρ(e)` and kernel evaluation are functions.
2. **Totality:** every well-typed finite Core program with a total primitive map returns a technical result.
3. **Termination:** checked dependency acyclicity, finite trees and configured node/allegation/module bounds terminate recursive evaluation.
4. **Group commutativity:** permutations of `all` or `any` members preserve truth status, though declaration order remains in traces.
5. **Actor/instance isolation:** changing a different actor/context/instance input cannot satisfy the selected instance.
6. **Allegation independence:** permuting allegation evaluation changes only output order, not individual requests/results.
7. **Resolution determinism:** one local root, exact versions, unique aliases/exports and unique interval match yield one selected graph/expression.
8. **Lowering preservation:** for supported constructs, the Core technical status equals the established kernel result after lowering.

Evidence classification:

| Property | Current evidence |
|---|---|
| Closed finite syntax, unique name/kind resolution, bounds, acyclicity | Established by checker construction and refusal tests. |
| Three-valued truth tables and presumption state table | Exhaustively tested over their finite domains. |
| `all`/`any`/branch/guard order independence | Property-tested plus exhaustive lists through length three. |
| Kernel memoized/reference agreement, actor/exception isolation, deterministic bytes | Property and regression tested. |
| Module/temporal determinism and modular/standalone equivalence | Regression tested on retained fixtures. |
| Historical protocol behavior | Golden byte comparisons. |
| Whole-Core progress/termination proof | Conjectural from checked finiteness/acyclicity; not mechanised. |
| Surface-to-Core type preservation theorem | Precisely stated below; not mechanised. |
| Core-to-kernel semantic preservation theorem | Tested on supported fixtures; not mechanically proved. |
| Legal completeness, correctness or current applicability | Intentionally not claimed. |

Proposed mechanisation statements for a later milestone are:

```text
Theorem surface_core_preservation:
  Check(surface) = checked -> Normalize(checked) = core -> WellTyped(core).

Theorem core_progress:
  WellTyped(core) /\ TotalInputs(core,rho) -> exists result, Eval(core,rho)=result.

Theorem core_termination:
  WellTyped(core) /\ Acyclic(core) -> Eval(core,rho) terminates.

Theorem lowering_preservation:
  Supported(core,v) -> Kernel_v(Lower_v(core)) = Observe_v(Eval(core)).

Theorem allegation_noninterference:
  Inputs(q1) disjoint Derived(q2) -> Eval(q1) is invariant under Eval(q2).
```

No Lean, Rocq, Agda or other proof assistant establishes these statements in this milestone. Existing Lean material is a separate bounded historical mechanisation.

## 8. Diagram semantics

`yuho diagram` accepts the same checked inputs as other Haskell commands. The semantic graph has stable IDs formed from semantic kind plus checked legal identifier. Nodes cover inputs, groups, definitions, offences, exceptions, participation, attempts, candidate penalties, presumptions, actors, allegations and shared facts. Edges cover membership, definition use, import, temporal selection, attachment, target, candidate penalty and explicit fact binding.

The SVG encoder applies a deterministic layered placement based on semantic kind and stable ID. Shape and border patterns redundantly distinguish categories; colour is not the only signal. Labels wrap, citations and statuses remain visible, edges have arrowheads, and every document includes a legend and the no-judicial-outcome notice. Semantic-graph JSON uses schema `yuho.semantic-graph/v0.1`. Neither format embeds timestamps or absolute checkout paths.

Diagrams are explanatory projections. They do not add edges missing from checked Core, aggregate allegations, decide evidence, or convert a candidate penalty into a sentence.

## 9. Limitations

Core Yuho v0.1 is bounded to the public constructs listed in the [machine-readable conformance registry](core-yuho-conformance-v0.1.json). It does not perform narrative fact extraction, evidence credibility assessment, automatic research, automatic legal-currency or transitional-law determination, unrestricted temporal reasoning, judicial guilt/liability/conviction/acquittal decisions, sentencing, CPC procedure, production package resolution, or exhaustive modelling of Singapore legislation. The authored corpus and its source assumptions remain a research proof of concept.
