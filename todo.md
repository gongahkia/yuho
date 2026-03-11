# Yuho Improvement Roadmap

## Overview

17 workstreams. Phases 0-8 are implementation infrastructure. Phases 9-16 are language rigour -- making Yuho a legally sound DSL, not just a syntactically valid one.

Priority: formal methods & execution > module resolution > defeasible reasoning > **type system & deontic logic** > library depth > tooling > interop.

## Dependency Graph

```
Phase 0 (doc-comments)  ──┐
Phase 7 (wizard)         ──┤── parallel, no deps
Phase 1 (module res)     ──┤
                           ▼
Phase 2 (interpreter)    ──── foundational
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
Phase 3 (defeasible)  Phase 4 (formal sem)  Phase 8 (E2E tests)
              │
              ▼
Phase 5 (Z3/Alloy harden)
              │
              ▼
Phase 6 (deepen library)

── language rigour (phases 9-16) ──────────────────────────

Phase 9 (type system)   ──── no deps, can start anytime
              │
              ├──▶ Phase 10 (deontic logic) ──▶ Phase 12 (causation & burden)
              │
              └──▶ Phase 11 (temporal logic)

Phase 13 (hierarchy)    ──── depends on Phase 1 (module res)
              │
              ▼
Phase 14 (penalty)      ──── depends on Phase 9 (refinement types)

Phase 15 (sem hardening) ── depends on Phases 9, 13

Phase 16 (interop)      ──── independent, can start anytime
```

---

## Phase 0: Doc-comment Preservation [S]

- [ ] Move `doc_comment` out of grammar `extras` into named children of declarations
- [ ] Add `doc_comment: Optional[str]` to `StructDefNode`, `FunctionDefNode`, `StatuteNode`, `ElementNode`, `FieldDef`
- [ ] Update `builder.py` to extract `///` text from preceding doc_comment nodes
- [x] Regenerate tree-sitter parser

**Files**: `grammar.js`, `nodes.py`, `builder.py`

---

## Phase 1: Module Resolution [L]

- [ ] Create `src/yuho/resolver/module_resolver.py` with `ModuleResolver` class
  - [ ] Module cache to avoid re-parsing
  - [ ] Path resolution: relative imports + library `referencing` paths
  - [ ] Cycle detection
- [ ] Wire `scope_analysis.py` to resolve imports and inject exported symbols
- [ ] Wire `type_check.py` for cross-module `NamedType` resolution
- [ ] Wire `test.py` to resolve `referencing` before running tests

**Files**: new `resolver/`, modify `scope_analysis.py`, `type_check.py`, `test.py`

---

## Phase 2: Interpreter/Evaluator [XL]

### 2A: Core Evaluator
- [ ] Create `src/yuho/eval/interpreter.py`
  - [ ] `Environment` class (chained scopes, struct/function/statute defs)
  - [ ] `Value` class (tagged union of runtime values)
  - [ ] `StructInstance` (type_name + field values)
  - [ ] `Interpreter(Visitor)` with visit methods for all expression types
  - [ ] Full operator semantics (+,-,*,/,%,==,!=,<,>,<=,>=,&&,||)
  - [ ] Pattern matching (wildcard, literal, binding, struct destructure)
  - [ ] Match-case evaluation with guards and consequences
  - [ ] Function calls with scoped environments

### 2B: Statement Execution
- [ ] `VariableDecl` -- declare + init in scope
- [ ] `ReturnStmt` -- exception-based control flow
- [ ] `AssertStmt` -- evaluate condition, raise with source location
- [ ] `Block` -- sequential execution

### 2C: Statute Evaluator
- [ ] Create `src/yuho/eval/statute_evaluator.py`
  - [ ] `StatuteEvaluator.evaluate(statute, facts, env)` -> `EvaluationResult`
  - [ ] Per-element satisfaction checking
  - [ ] `all_of`/`any_of` group evaluation
  - [ ] Penalty range output

### 2D: CLI Wiring
- [ ] Replace `test.py` ad-hoc `_evaluate_expr` with real `Interpreter`
- [x] Add `:eval` to REPL with persistent `Environment`
- [x] Add `yuho eval <file>` CLI command

**Files**: new `eval/`, modify `test.py`, `repl.py`, `main.py`

---

## Phase 3: Defeasible Reasoning [L]

- [ ] Grammar change: add `when <guard>` to `exception_block`
- [ ] Add `guard: Optional[ASTNode]` to `ExceptionNode`
- [ ] Update `builder.py` to extract exception guards
- [ ] Create `src/yuho/eval/defeasible.py`
  - [ ] `DefeasibleReasoner.evaluate_with_exceptions(statute, facts, env)`
  - [ ] Base element evaluation -> exception guard checking -> defeat logic
  - [ ] `DefeasibleResult` with reasoning chain (exportable trace)
- [ ] Integrate into `StatuteEvaluator` so exceptions auto-apply
- [ ] Update s300 (murder) exceptions with structured `when` guards

**Files**: `grammar.js`, `nodes.py`, `builder.py`, new `defeasible.py`, `statute_evaluator.py`

---

## Phase 4: Formal Semantics Document [L]

- [x] Create `doc/FORMAL_SEMANTICS.md`
  - [x] Abstract syntax (BNF at AST level)
  - [x] Type system judgment rules
  - [x] Big-step operational semantics (expressions, match-case, function calls, structs)
  - [x] Defeasible semantics (exception defeat relation, partial order)
  - [x] Module semantics (import resolution, scoping)
  - [x] Type soundness sketch (progress + preservation)
- [x] Create `tests/test_semantics.py` -- test cases validating interpreter matches formal rules

**Files**: new `doc/FORMAL_SEMANTICS.md`, new `tests/test_semantics.py`

---

## Phase 5: Z3/Alloy Verification Hardening [L]

### Z3 (`z3_solver.py`)
- [ ] Rewrite `Z3Generator._generate_sorts` to walk actual `ast.type_defs`
- [ ] AST-driven constraint generation from element descriptions and match arms
- [ ] Exception encoding as Z3 implications (`guard => NOT(conviction)`)
- [ ] Cross-statute consistency checks (e.g., s300 => s299)
- [ ] Source-mapped diagnostics (counterexamples -> source locations)

### Alloy (`alloy.py`)
- [ ] Real `fact` blocks from element groups
- [ ] Real `assert` blocks encoding statute properties
- [ ] Exception modeling as Alloy `pred` blocks

**Files**: `z3_solver.py`, `alloy.py`, `combined.py`

---

## Phase 6: Deepen Library [L]

For each of 12 statutes (`library/penal_code/s{NNN}_{name}/`):

- [ ] Add cross-references via `import` to related statutes
- [ ] Add structured `when` guards to exceptions
- [ ] Add more illustrations from actual Penal Code text
- [ ] Add more case law references
- [ ] Add doc-comments to elements
- [ ] Replace stub `test_statute.yh` with real tests:
  - [ ] Per-element satisfaction/non-satisfaction
  - [ ] Exception application
  - [ ] Illustration-as-test-case scenarios

**Priority**: s299+s300 > s378 > s415+s420 > s319 > s383+s390 > s403+s503 > s463 > s499

---

## Phase 7: Wizard Completeness [M]

- [x] Add `ExceptionData` and `CaseLawData` dataclasses
- [x] Add `collect_exceptions()` interactive prompt
- [x] Add `collect_caselaw()` interactive prompt
- [x] Modify `collect_elements()` for `all_of`/`any_of` grouping (recursive prompts)
- [x] Add case struct generation prompt
- [x] Update `generate_yuho_code()` for exceptions, caselaw, nested groups

**Files**: `wizard.py`

---

## Phase 8: E2E Tests [M]

- [x] `tests/e2e/test_parse_to_eval.py` -- parse -> AST -> analyze -> evaluate (all 12 statutes)
- [x] `tests/e2e/test_transpile_roundtrip.py` -- parse -> transpile -> verify output
- [x] `tests/e2e/test_verify_pipeline.py` -- parse -> Z3/Alloy -> check results
- [x] `tests/e2e/test_module_resolution.py` -- cross-file imports, cycles, type checking
- [x] `tests/e2e/test_defeasible.py` -- exception defeat, guards, multiple exceptions
- [x] `tests/e2e/conftest.py` -- shared fixtures

**Files**: new `tests/e2e/`

---

---

## Phase 9: Type System for Legal Modeling [XL]

Yuho's type system mirrors general-purpose languages. Legal reasoning requires domain-specific type distinctions that the current system cannot express.

### 9A: Sum Types / Enums
- [x] Add `enum` declaration to grammar: `enum Verdict { guilty, notGuilty, mistrial }`
- [x] `EnumDefNode` in AST with named variants (optionally carrying data)
- [ ] Exhaustiveness checking: match arms over enums must cover all variants
- [x] Transpile enums to JSON (string union), GraphQL (enum), Alloy (abstract sig)
- **Why:** Verdicts, offense categories, and element types are finite closed sets, not structs with bool flags. `struct Verdict { bool guilty, bool notGuilty }` allows the impossible state `{ guilty: TRUE, notGuilty: TRUE }`.

### 9B: Type Aliases
- [x] Add `type` declaration: `type MensRea = string`
- [x] Aliases are transparent for type checking but improve readability
- [ ] Show alias names in error messages and transpiler output
- **Why:** Repeating `string` for every definition obscures intent. `type StatuteRef = string` documents that a value is a cross-reference, not arbitrary text.

### 9C: Refinement Types
- [x] Integer/money/percent ranges: `int{0..99}`, `money{$0.00..$10000.00}`
- [ ] Checked at assignment, function boundaries, and struct construction
- [ ] Encode as Z3 range constraints for verification
- **Why:** `imprisonment := 1 year .. 7 years` is a range but the type system can't prevent assigning `99 years` to it. Refinements make penalty constraints machine-checkable.

### 9D: Fact vs. Conclusion Distinction
- [x] Add `fact` and `conclusion` type qualifiers (or marker types)
- [ ] `fact movedProperty := TRUE` vs. `conclusion guiltyOfTheft := evaluateTheft(...)`
- [ ] Semantic analysis: conclusions must derive from facts, never the reverse
- [ ] Transpile: clearly separate factual predicates from legal conclusions in English output
- **Why:** "The accused took the wallet" (fact) and "the accused committed theft" (conclusion) are epistemically different. Conflating them hides the inferential leap that legal reasoning requires.

**Files:** `grammar.js`, `nodes.py`, `builder.py`, `type_inference.py`, `type_check.py`

---

## Phase 10: Deontic Logic [XL]

Criminal statutes are inherently deontic -- they define what is prohibited, obligatory, or permitted. Yuho currently has no way to express these modalities; everything is descriptive.

### 10A: Deontic Operators
- [x] Add keywords `obligation`, `prohibition`, `permission` as element qualifiers
- [ ] Syntax: `obligation duty_to_report := "Must report knowledge of felony";`
- [ ] These are distinct from `actus_reus`/`mens_rea` -- they encode what the law *requires*, not what constitutes an offense
- **Why:** s202 (intentional omission to give information of offence) creates an *obligation*. Encoding it as `actus_reus` loses the normative force -- it's not an act, it's a failure to act.

### 10B: Conditional Duties
- [ ] `obligation X when Y` -- duty arises only when condition holds
- [ ] `prohibition X unless Y` -- default prohibition with exception
- [ ] Defeasible reasoning integration: permissions can defeat prohibitions
- **Why:** "A public servant *shall* report" is conditional on being a public servant. The duty doesn't exist in the abstract.

### 10C: Hohfeldian Relations (stretch)
- [ ] Model claim-right / duty / privilege / no-right / power / liability / immunity / disability
- [ ] Express correlative pairs: X's right implies Y's duty
- **Why:** Full legal relations require Hohfeldian analysis. s96 (right of private defence) creates a *privilege* that defeats what would otherwise be a *prohibition*.

**Files:** `grammar.js`, `nodes.py`, `builder.py`, `defeasible.py`, `statute_evaluator.py`

---

## Phase 11: Temporal Logic [L]

Statutes are not timeless -- they are enacted, amended, repealed, and have transition provisions. Yuho has `date` and `duration` literals but no temporal semantics.

### 11A: Statute Validity Windows
- [x] Add `effective` and `repealed` metadata to statute blocks
- [ ] Syntax: `statute 300 "Murder" effective 1872-01-01 { ... }`
- [x] Semantic check: warn if evaluating a repealed statute
- [x] Support `amended_by` references with dates
- **Why:** The Penal Code 1871 has been amended dozens of times. s377A (repealing s377) changed the law on a specific date. Without temporal scoping, Yuho can't model which version of a statute applies to facts occurring on a given date.

### 11B: Temporal Operators for Facts
- [ ] `before(date)`, `after(date)`, `during(date, date)` as boolean expressions
- [ ] `within(duration)` -- "within 7 days of the act"
- [ ] Date arithmetic: `date + duration`, `date - date`
- **Why:** s300 exception 1 (provocation) requires the act to occur while "deprived of the power of self-control" -- a temporal condition. Limitation periods require date arithmetic.

### 11C: Amendment Chains
- [x] `amends` keyword to reference prior versions
- [ ] Diff-aware transpilation: show what changed between versions
- [ ] Library support: maintain amendment history per statute
- **Why:** Tracing how a statute evolved is essential for statutory interpretation. Courts apply the version in force at the time of the offense.

**Files:** `grammar.js`, `nodes.py`, `builder.py`, `interpreter.py`, transpilers

---

## Phase 12: Causation & Burden of Proof [L]

These are foundational to criminal law but entirely absent from Yuho.

### 12A: Causal Operators
- [x] Add `caused_by` as a first-class relation between elements
- [ ] Syntax: `actus_reus death := "Death of the victim" caused_by act;`
- [ ] Distinguish factual causation ("but for") from legal causation ("proximate cause")
- [ ] Model novus actus interveniens (intervening acts breaking the chain)
- **Why:** s299 (culpable homicide) *requires* a causal link: the act must *cause* death. Currently this is just a string description. Making it structural lets verification check that every homicide offense actually specifies a causal chain.

### 12B: Burden of Proof Constructs
- [x] `burden` qualifier on elements: `burden prosecution` (default) vs. `burden defence`
- [x] `presumed` modifier: `presumed TRUE` means the fact is assumed unless rebutted
- [ ] `standard` qualifier: `beyond_reasonable_doubt`, `balance_of_probabilities`, `prima_facie`
- **Why:** s300 requires prosecution to prove intent *beyond reasonable doubt*. Exceptions shift the burden: provocation must be raised by the defence on a *balance of probabilities*. Without this, the evaluator treats all elements identically regardless of who must prove them.

### 12C: Presumption & Rebuttal
- [ ] `presumption X := Y unless Z` -- X is presumed to equal Y unless Z is established
- [ ] Integrate with defeasible reasoning: presumptions are default rules
- [ ] Track presumption status in evaluation trace
- **Why:** s114 of the Evidence Act creates presumptions (e.g., possession of recently stolen goods implies theft). These are critical inference rules that the evaluator should model, not ignore.

**Files:** `grammar.js`, `nodes.py`, `defeasible.py`, `statute_evaluator.py`

---

## Phase 13: Statute Hierarchy & Cross-references [L]

Statutes don't exist in isolation. They form hierarchies, reference each other, and sometimes conflict.

### 13A: Offense Subsumption
- [x] Add `subsumes` relation between statutes
- [ ] Syntax: `statute 300 "Murder" subsumes 299 { ... }`
- [ ] Semantic: if s300 is satisfied, s299 is necessarily satisfied
- [x] Verification: Z3 checks that subsumption claims are consistent with element definitions
- **Why:** Murder (s300) is a special case of culpable homicide (s299). Dacoity (s395) subsumes robbery (s390) which subsumes theft (s378). These hierarchies are legally significant -- charging the subsuming offense includes the subsumed one.

### 13B: First-class Cross-references
- [ ] `ref s24.dishonestly` as an expression that resolves to the definition from s24
- [ ] Reference validation at parse time: warn if target doesn't exist
- [ ] Transpile: hyperlink references in HTML/LaTeX output
- [ ] Dependency graph: `yuho deps <file>` shows which statutes depend on which
- **Why:** s378 (theft) requires "dishonestly" as defined in s24. Currently this must be duplicated or imported as a function. A first-class reference makes the dependency explicit and traceable.

### 13C: Conflict Resolution
- [ ] `overrides` declaration between statute provisions
- [ ] `lex specialis` / `lex posterior` / `lex superior` resolution rules
- [ ] Verification: warn when two statutes produce contradictory conclusions for the same facts
- **Why:** When the Penal Code and a special Act (e.g., Misuse of Drugs Act) both apply, conflict resolution rules determine which prevails. Yuho should model this, not leave it implicit.

### 13D: General Exceptions as Library
- [ ] Encode Penal Code Chapter IV (ss76-106) as a shared exception library
- [ ] Any statute can `referencing general_exceptions` to inherit them
- [ ] Exceptions apply universally unless a statute explicitly excludes them
- **Why:** General Exceptions (mistake of fact, necessity, duress, private defence, etc.) apply to *all* offenses in the Penal Code. Encoding them once and referencing them everywhere avoids duplication and ensures consistency.

**Files:** `grammar.js`, `nodes.py`, `resolver/`, `z3_solver.py`, library files

---

## Phase 14: Penalty Composition [M]

Real sentencing is far more complex than min/max ranges.

- [x] Add `concurrent` vs. `consecutive` sentencing modifiers
- [x] Model mandatory minimums: `minimum imprisonment := 2 years` (court cannot go below)
- [ ] Alternative penalties: `penalty either { imprisonment ... } or { fine ... }`
- [ ] Aggravating/mitigating factors as modifiers on penalty ranges
- [ ] Penalty scaling: `if repeat_offender { imprisonment := imprisonment * 2 }`
- [ ] Caning limits: statutory cap of 24 strokes (s328 CPC) -- encode as a system-wide constraint
- **Why:** s302 prescribes death *or* life imprisonment for murder. s325 prescribes up to 7 years *and* fine *and* caning. These aren't simple ranges -- they're structured compositions with legal constraints. A judge choosing between concurrent and consecutive sentences changes the total penalty dramatically.

**Files:** `grammar.js`, `nodes.py`, `statute_evaluator.py`, `penalty` transpile logic

---

## Phase 15: Semantic Analysis Hardening [M]

Static checks that catch legal modeling errors before runtime.

### 15A: Statute Completeness Linting
- [x] Warn if a statute has `elements` but no `penalty`
- [x] Warn if a statute has no `actus_reus` element (every offense needs a physical act)
- [x] Warn if a statute has no `mens_rea` element and is not marked `strict_liability`
- [ ] Warn if `illustrations` reference elements not defined in the statute
- **Why:** An offense without actus reus is legally malformed. Catching this statically is better than discovering it at evaluation time.

### 15B: Exception Coherence
- [x] Check that exception guards reference variables available in the fact pattern
- [ ] Check that exceptions defeat at least one element (an exception that defeats nothing is dead code)
- [x] Warn if multiple exceptions have identical guards (likely copy-paste error)
- **Why:** s300 has 5 exceptions. If exception 3 accidentally uses the same guard as exception 1, it's either redundant or a mistake. Static analysis should flag this.

### 15C: Cross-statute Consistency
- [x] If statute A `subsumes` statute B, check that A's elements are a superset of B's
- [ ] If two statutes share a definition term, check that the definitions are compatible
- [ ] Detect contradictory penalty ranges across related statutes
- **Why:** If s300 (murder, max: death) subsumes s299 (culpable homicide, max: life), the penalty for the subsuming offense should be >= the subsumed one. This is a checkable invariant.

### 15D: Illustration-as-test Validation
- [ ] Parse illustration text for named parties and fact patterns
- [ ] Auto-generate test assertions from illustrations where possible
- [ ] Warn if an illustration's described outcome contradicts the statute's element logic
- **Why:** Illustrations are the legislature's own test cases. "A shoots Z intending to kill him. Z dies. A commits murder." This should be mechanically verifiable against the statute definition.

**Files:** `scope_analysis.py`, `type_check.py`, new `statute_lint.py`

---

## Phase 16: Interoperability [L]

Yuho should not be an island. Legal tech has standards and ecosystems worth connecting to.

### 16A: Akoma Ntoso XML Export
- [x] Transpile statutes to Akoma Ntoso (the international standard for legislative XML)
- [x] Map elements to `<section>`, `<paragraph>`, `<point>` structures
- [x] Embed metadata as FRBR expressions
- **Why:** Akoma Ntoso is used by parliaments worldwide. Exporting to it makes Yuho statutes interoperable with legislative drafting systems (e.g., EU N-Lex, Kenya Law).

### 16B: Prolog / Answer Set Programming Backend
- [x] Transpile statute logic to Prolog facts and rules
- [ ] Use ASP (clingo) for defeasible reasoning with priorities
- [ ] Compare ASP results with Yuho's interpreter for soundness checking
- **Why:** Prolog is the de facto language for legal expert systems. ASP handles defeasibility natively. Using them as a backend gives Yuho access to decades of logic programming research.

### 16C: Legal API Bridges
- [ ] Singapore Statutes Online (SSO) API: fetch statute text and validate against .yh definitions
- [ ] Case law APIs: link `caselaw` blocks to real case databases
- [ ] Auto-import: `yuho import --from-sso 300` scaffolds a .yh file from the official text
- **Why:** Manually encoding statutes is error-prone. Machine-assisted import from authoritative sources (with human review) reduces encoding errors and keeps the library current.

### 16D: Catala / OpenFisca Interop (stretch)
- [ ] Study Catala's approach to legislative encoding (literate programming + default logic)
- [ ] Study OpenFisca's approach to tax/benefit rules
- [ ] Identify features worth adopting or bridging to
- **Why:** Catala (Inria) and OpenFisca are the most mature rules-as-code frameworks. Understanding their design tradeoffs avoids reinventing solved problems and opens collaboration paths.

**Files:** new transpilers in `transpile/`, new `import/` module

---

## Verification Checklist

After all phases:

- [ ] `pytest tests/` -- all unit + property + E2E tests pass
- [ ] `yuho check library/penal_code/s300_murder/statute.yh` -- parses clean
- [ ] `yuho test library/penal_code/s300_murder/test_statute.yh` -- real assertions pass
- [ ] `yuho transpile ... -t english` -- includes exception info
- [ ] `yuho verify ...` -- Z3 reports consistency
- [ ] `yuho wizard` -- generates all_of/any_of, exceptions, caselaw
- [ ] Cross-file `referencing` resolves correctly
- [ ] Defeasible: provocation exception defeats murder conviction
- [ ] Enum exhaustiveness: match over `Verdict` must cover all variants
- [ ] Subsumption: `s300 subsumes s299` verified by Z3
- [ ] Temporal: evaluating repealed statute produces a warning
- [ ] Burden: prosecution elements distinguished from defence elements in traces
- [ ] Penalty composition: concurrent/consecutive correctly modeled
- [ ] Cross-statute lint: contradictory definitions flagged
