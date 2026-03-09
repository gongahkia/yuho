# Yuho Improvement Roadmap

## Overview

9 workstreams organized by dependency order. Priority: formal methods & execution > module resolution > defeasible reasoning > library depth > tooling.

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
```

---

## Phase 0: Doc-comment Preservation [S]

- [ ] Move `doc_comment` out of grammar `extras` into named children of declarations
- [ ] Add `doc_comment: Optional[str]` to `StructDefNode`, `FunctionDefNode`, `StatuteNode`, `ElementNode`, `FieldDef`
- [ ] Update `builder.py` to extract `///` text from preceding doc_comment nodes
- [ ] Regenerate tree-sitter parser

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
- [ ] Add `:eval` to REPL with persistent `Environment`
- [ ] Add `yuho eval <file>` CLI command

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

- [ ] Create `doc/FORMAL_SEMANTICS.md`
  - [ ] Abstract syntax (BNF at AST level)
  - [ ] Type system judgment rules
  - [ ] Big-step operational semantics (expressions, match-case, function calls, structs)
  - [ ] Defeasible semantics (exception defeat relation, partial order)
  - [ ] Module semantics (import resolution, scoping)
  - [ ] Type soundness sketch (progress + preservation)
- [ ] Create `tests/test_semantics.py` -- test cases validating interpreter matches formal rules

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

- [ ] Add `ExceptionData` and `CaseLawData` dataclasses
- [ ] Add `collect_exceptions()` interactive prompt
- [ ] Add `collect_caselaw()` interactive prompt
- [ ] Modify `collect_elements()` for `all_of`/`any_of` grouping (recursive prompts)
- [ ] Add case struct generation prompt
- [ ] Update `generate_yuho_code()` for exceptions, caselaw, nested groups

**Files**: `wizard.py`

---

## Phase 8: E2E Tests [M]

- [ ] `tests/e2e/test_parse_to_eval.py` -- parse -> AST -> analyze -> evaluate (all 12 statutes)
- [ ] `tests/e2e/test_transpile_roundtrip.py` -- parse -> transpile -> verify output
- [ ] `tests/e2e/test_verify_pipeline.py` -- parse -> Z3/Alloy -> check results
- [ ] `tests/e2e/test_module_resolution.py` -- cross-file imports, cycles, type checking
- [ ] `tests/e2e/test_defeasible.py` -- exception defeat, guards, multiple exceptions
- [ ] `tests/e2e/conftest.py` -- shared fixtures

**Files**: new `tests/e2e/`

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
