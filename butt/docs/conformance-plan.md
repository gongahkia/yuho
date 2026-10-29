# Conformance Test Plan and Implementation Tranches — Phase 0.1

This plan defines (1) how conformance to the normative sections of
`architecture.md` (§2–§7, §12, §13) is tested, and (2) the implementation
tranches, each independently verifiable.

No tests or code are created in Phase 0.1.

---

## 1. Principles

1. **Tests come from normative text.** Every test cites the section it
   checks. Private details (§8) get unit tests, which are not part of
   conformance.
2. **Stage dumps.** `tokens`, `trees`, `parse`, `expand`, `core`, `check`, and
   `run`. Dump formats are a versioned tool contract.
3. **Negative tests are first-class.** They use stable diagnostic codes and
   primary spans. Message wording is covered only by separate golden tests.
4. **Determinism.** Every test is run twice, and its dumps and interfaces
   must be byte-identical (U-P6).
5. **The trusted base gets property tests:** core progress/preservation
   sampling and primitive agreement.
6. **Frozen sections** (§0.4) have complete suites before their tranche is
   accepted.

### 1.1 Test file format

```
-- test: syn/conflict/prefix-overlap-001
-- section: §6.1 §6.2
-- stage: parse
-- files: lib_a, lib_b, main
-- expect-error: E-SYN-CONFLICT at main:2:1
-- expect-note: origin lib_a.Repeat ; origin lib_b.RepeatN
<source>
```

Other directives: `expect-dump: <stage>`, `expect-run-stdout:`,
`expect-panic:`, `capabilities:`, `limits:` (any §13.3 counter).

---

## 2. Conformance suites

### 2.1 LEX — lexer (§2.1, §12) — frozen

- LEX-01 UTF-8 validity, byte-accurate spans, CRLF.
- LEX-02 Maximal operator runs: `a<-b`, `a+-b`, `x|>f`, `a<=>b`, `a.b`, `1..2`.
- LEX-03 **Stability:** token dumps are identical with and without any
  declaration or import (operators `<|>`, `+-`).
- LEX-04 Jointness flags: `f(x)`, `f (x)`, `f\n(x)`.
- LEX-05 Literals and suffixes: `3.0m`, `10ms`, `1e5`, `3em`, `0x1Fu8`, `3 m`, `1.`, `.5` (errors where specified). Strings: LF and CRLF are `E-LEX-STRING`; a lone CR is a string byte (R-48).
- LEX-06 Raw regions: brace balancing; long-bracket levels; `#t[i]` is not raw; unterminated region.
- LEX-07 Raw identifiers; never match literal atoms.
- LEX-08 `E-LEX-UNBALANCED` with both spans.
- LEX-09 Line and long comments.
- LEX-10 Comment priority: `x--y`, `a+--b`; the `W-LEX-COMMENT-AFTER-OPERAND` lint.
- LEX-11 Raw region containing a string with `}` closes early; the long-bracket form does not.
- LEX-12 Non-ASCII outside strings, comments and raw regions → `E-LEX-CHAR`. Control characters, including NUL, are accepted inside those bodies (R-47).
- LEX-13 Property: lexing then concatenating token texts and trivia reproduces the source exactly.

### 2.2 CORE — core checker and interpreter (§4.4, §4.6, §13.4–13.6) — frozen

- CORE-01 Each core form: positive and negative cases.
- CORE-02 `case` exhaustiveness, duplicate arms, `Bool` arms, `_`.
- CORE-03 Labels do not cross `fun` (`break` inside a closure → error).
- CORE-04 Value restriction: polymorphic def with a non-`fun` body rejected.
- CORE-05 Opaque types: construct/project/`case` outside the owner module rejected; inside accepted; transparent types accepted everywhere.
- CORE-06 Phase discipline: a phase-0 reference from a phase-1 def rejected, and vice versa; a primitive used at a disallowed phase rejected.
- CORE-07 **Property tests:** generated well-typed terms never get stuck, and results have the predicted type (U-P2 sampling). Mutated ill-typed terms are rejected without crashing the checker.
- CORE-08 Serialization round-trip and re-check.
- CORE-09 Phase-1 value rule: `meta def counter = ref(0)` rejected.
- CORE-10 Call-depth limit → panic `stack overflow`, never a host crash (per platform).
- CORE-11 Annotation consistency: `break[T]`, `loop[T]`, `panic[T]`, `x[T̄]` arity and kind errors.
- CORE-12 Left-to-right evaluation order is observable via `print` / `Ref`.

### 2.3 PRIM — primitive agreement (§13.6) — frozen

- PRIM-01 For every table entry, generated arguments of the declared types produce a result satisfying `value_has_type`, or a declared trap.
- PRIM-02 Enumerated edge cases: `i64` min/max overflow, division by zero, `rem` signs, NaN/∞ conversions, array bounds 0/len/−1, empty strings.
- PRIM-03 Exact trap message prefixes.
- PRIM-04 Capability tags: a phase-1 call of `print` rejected.

### 2.4 PARSE — core grammar (§2.3)

- PARSE-01 Blocks, nesting, `end` mismatches.
- PARSE-02 No trailing call or index after a newline.
- PARSE-03 Built-in operators via prelude arrays (from T6).
- PARSE-04 `name!(…)` in all three positions.
- PARSE-05 Statement continuations: `a.b = c`, `x := 1`.
- PARSE-06 Reserved vs. contextual words.

### 2.5 SYN — declarations, dispatch, scoping (§2.4, §2.7)

- SYN-01 Declarative pattern dispatch; dispatch pattern derived from the leading atom run.
- SYN-02 Procedural parser; body consumes less than its pattern → `E-SYN-PATTERN-UNCONSUMED`.
- SYN-03 Committed choice; local `try` restores the cursor only within the production.
- SYN-04 Sequential activation.
- SYN-05 Block scoping (Example B).
- SYN-06 Exports and imports; value imports do not import syntax.
- SYN-07 Keyword claiming and raw-identifier escape; `W-SYN-CLAIM-SHADOWS`.
- SYN-08 Reserved words cannot be claimed → `E-SYN-CORE`.
- SYN-09 User categories.
- SYN-10 Keyed tables: suffix and sublanguage dispatch.
- SYN-11 Longer patterns: `["for", ident, "="]` and `["for", ident, "in"]` coexist.
- SYN-12 Unrestricted bodies: optional and repeated parts, nested categories, groups.
- SYN-13 Declarative LL(1) body rejection → `E-SYN-PATTERN-AMBIGUOUS`.

### 2.6 AMB — conflicts (§6)

- AMB-01 Identical patterns from two origins.
- AMB-02 Strict-prefix overlap.
- AMB-03 Disjoint at position *k*.
- AMB-04 Literal vs. class; `raw(t)`; groups.
- AMB-05 Diamond import.
- AMB-06 **Order independence** under permutation.
- AMB-07 `shadowing` across scopes.
- AMB-08 Rule-key conflicts.
- AMB-09 Lemma check: for random non-overlapping pattern sets and random token streams, at most one entry matches.
- AMB-10 Cross-table: a `stmt` continuation key that is also an `expr` trailing key → conflict.

### 2.7 PREC — precedence (§2.5)

- PREC-01 Same level: `left`, `right`, `none`.
- PREC-02 Same array, different levels.
- PREC-03 Unrelated → `E-PREC-UNRELATED` with a fix-it.
- PREC-04 Bridging array in a nested scope; inactive outside it.
- PREC-05 Transitivity through a bridge.
- PREC-06 Cycle via imports → `E-PREC-CYCLE` with the edge path.
- PREC-07 Duplicate level in an array → `E-PREC-DUPLICATE`.
- PREC-08 Override by operator shadowing; the outer meaning is restored after the block.
- PREC-09 Structured macro output is unaffected by use-site arrays.
- PREC-10 **Reference check (U-P1):** for random partial orders and random operator sequences, the Pratt result equals the unique well-related tree found by brute-force enumeration, or both report an error.
- PREC-11 Prefix, postfix and mixfix comparisons (§2.5.2).
- PREC-12 Infix vs. postfix with the same token → conflict; prefix vs. infix → allowed.

### 2.8 HYG — hygiene and grammar environments (§2.6, §13.1–13.2)

- HYG-01..08 As in Phase 0: `swap`, helper references, binder invisibility, `ident_at`/`$!`, use-site scopes, nested expansions, ambiguity, interpolation scope.
- HYG-09a `tokens{}` parsed with the definition-site environment.
- HYG-09b A macro's token-tree argument parsed with the use-site environment.
- HYG-09c A foreign tree spliced as a whole group keeps its stamp.
- HYG-09d Loose mixed-stamp tokens → `E-SYN-MIXED-ENV`.
- HYG-09e `restamp` changes the environment explicitly.
- HYG-10 Hygienic type names.
- HYG-11 Scope IDs are deterministic across runs.

### 2.9 META — phases, capabilities, limits (§3, §13.3, §13.8)

- META-01 Phase separation.
- META-02 Same-module `meta def` ordering.
- META-03 `E-META-FUEL` at a deterministic step.
- META-04 Capabilities: declared ∩ granted; `read_file` prefix.
- META-05 Reproducibility.
- META-06 Import cycles at any phase → `E-IMPORT-CYCLE`.
- META-07 Memory, depth, expansion depth, count and size limits; each error code.
- META-08 No partial effects: an aborted invocation leaves the registry unchanged.
- META-09 Expansion backtrace contents and deterministic truncation.

### 2.10 GEN — grammar-generating macros (§3.3)

- GEN-01 Example D at module level.
- GEN-02 Missing `declare_syntax` → `E-META-CAP`.
- GEN-03 Use-site placement.
- GEN-04 Inside a block: active for the next statement, inactive after the block.
- GEN-05 Type-directed macro attempting to declare syntax → `E-META-CAP`.
- GEN-06 Generated entries are conflict-checked.
- GEN-07 A failed grammar-generating macro abandons the rest of its sequence (`N-SEQ-ABANDONED`); other failures do not.
- GEN-08 [v0.1] A block-generated `meta def`, `import` or `export` → error.

### 2.11 ELAB — elaboration (§4.2)

- ELAB-01 Bidirectional checking.
- ELAB-02 `+` via rules (Example E).
- ELAB-03 `E-TYPE-NO-RULE`.
- ELAB-04 `Elaborated` handles are not re-elaborated.
- ELAB-05 Duplicate-splice lint.
- ELAB-06 `E-TYPE-UNKNOWN-YET`.
- ELAB-07 A deliberately buggy test rule producing ill-typed core is rejected by the core.
- ELAB-08 Nested patterns → flat `case`.
- ELAB-09 A macro from `M` constructing `M`'s opaque type directly in `N` → core rejection. Via an exported helper → accepted.
- ELAB-10 `Elaborated` exposes `.type` but no term structure (API surface test).

### 2.12 CHK — module checkers (§4.3)

- CHK-01 The core interface is readable by default-checker modules.
- CHK-02 Extended facts require both `trust X` and format support.
- CHK-03 `boundary checked` guard panics (Example F).
- CHK-04 Ill-typed checker output is rejected.
- CHK-05 `E-CHK-BOUNDARY-REQUIRED` when the mode is missing.
- CHK-06 `W-CHK-ASSUMED` at use sites of `assumed` exports.
- CHK-07 [v0.1] `boundary checked` on a higher-order export → error.
- CHK-08 A checker delegating to `default_elab` gives the same core as no checker.

### 2.13 RUN — dynamic semantics (§4.6)

- RUN-01 Evaluation order.
- RUN-02 `label`/`break`, `return` via macro.
- RUN-03 Numeric traps.
- RUN-04 `panic` exit status and message.
- RUN-05 Closures over `Ref`.

---

## 3. Implementation tranches

### 3.1 Rules for every tranche

- **Output:** an independently testable artefact. Each tranche's own suites
  pass without later tranches.
- **Acceptance:** the listed suites pass, plus the double-run determinism
  check.
- **Regression:** **all** previously accepted suites still pass. Golden or
  dump changes need an explicit, reviewed update with a reason.
- **No premature features:** each tranche lists what it explicitly
  excludes.
- **TCB discipline:** any change to `core`, `prims` or `interp` needs
  CORE/PRIM tests for the change, in the same tranche. No tranche may add
  trusted behaviour that is not covered by a test.

### 3.2 Tranche table

| Tranche | Output | Acceptance | Excludes | TCB change |
|---|---|---|---|---|
| **T0 / T0.1** | Specification documents | Review sign-off (§4) | all code | — |
| **T1** | Lexer + reader library and a `tokens`/`trees` dump CLI | LEX-01..13 | parsing, registry, raw-region interpretation | none |
| **T2a** | Core AST, private S-expression core reader, **core checker** (incl. opaque authorisation, value restriction, phase-1 value rule, phase discipline), serializer | CORE-01..06, 08, 09, 11 | evaluation | **introduces** the checker |
| **T2b** | **Interpreter** (call-depth limit, counters, capability gate hooks), **primitive table** + agreement harness | CORE-07, 10, 12; PRIM-01..04; RUN-01, 03, 04 | phase-1 syntax primitives | **introduces** interpreter and primitives |
| **T5a** (parallel) | Pure library: pattern overlap, conflict rule, scoped activation over abstract entries | AMB-01..07, 09, 10 as unit-level conformance | any parser | none |
| **T6a** (parallel) | Pure library: level graph, bridging, cycle check, Pratt comparison over abstract operator sequences | PREC-01..07, 10, 11, 12 (abstract) | any parser | none |
| **T3** | Fixed surface parser (sequences, Pratt with hardwired operators, statement continuations, hardwired `if`/`while`/`return`) + minimal monomorphic elaborator → core | PARSE-01, 02, 04 (syntax only), 05, 06; RUN-01..05 end-to-end | macros, registry, polymorphic inference | none |
| **T4** | Syntax objects, scope sets, expander, quotation; **phase-1 syntax primitives**; **minimal source-based multi-module driver** (no serialized interfaces); eager head-expansion in item position; macros only from imported modules | HYG-01..08, 10, 11; PARSE-04; META-01, 03, 05, 06, 09 | custom grammar, same-module macros, serialized interfaces | **adds** syntax primitives (PRIM-01..03 extended) |
| **T5** | Registry + declarative `syntax` + dispatch + claims + scoping + imports + conflicts (integrates T5a) | SYN-01, 04..13; AMB-* on real source | procedural parsers, precedence | none |
| **T6** | Precedence in the real parser (integrates T6a); prelude operators become declared | PREC-* on source; PARSE-03 | — | none |
| **T7** | Procedural parsers, Parser API, capability gate enforced, resource counters enforced, grammar-environment stamps | SYN-02, 03; META-04, 07, 08; HYG-09a–e | same-module meta, grammar-generating macros | none (hooks existed since T2b) |
| **T8** | Same-module `meta def`; serialized interfaces with re-check on load; `declare_syntax` grammar generation (module level and blocks); recovery policy | META-02; GEN-01..04, 06..08; CORE-08 on interfaces; interface byte-identity | type-directed features | none |
| **T9** | Full elaborator: bidirectional checking, unification, rank-1 polymorphism, Elab API, type-directed macros, `var` | ELAB-01, 03..08, 10; GEN-05; CORE-04 regression | rules, custom types | none |
| **T10** | `new` types, rule tables, literal-suffix typing; Examples D and E end-to-end | ELAB-02, 09; AMB-08; HYG-10 | checkers | none (opaque checking existed since T2a) |
| **T11** | Sublanguages (raw-region parsers, host interpolation) | SYN-10; HYG-08; LEX-06/11 end-to-end | — | none |
| **T12** | Module checkers, extended interfaces, `trust`, boundary modes | CHK-01..08 | gradual typing | none |
| **T13** | Prelude completion; **remove hardwired** `if`/`while`/`return`/operators from T3 | Full suite with hardwired forms deleted; Examples A–G | — | none |
| **T14** | Diagnostics polish, per-item caching, LSP groundwork, optional bytecode for core | Golden diagnostics; caching on/off equivalence; bytecode/interpreter differential tests | — | bytecode, if added, is a new TCB component with differential tests |

Changes from the Phase 0 roadmap:

- T2 is split into a checker tranche and an interpreter tranche.
- Opaque-type checking moved from T10 into T2a, because it is TCB behaviour.
- The minimal multi-module driver moved into T4. Phase 0's T4 needed
  imported macros without a driver.
- Phase-1 syntax primitives are explicitly a TCB addition in T4.
- Resource counters are hooked in T2b and enforced in T7.
- T5a and T6a are formal parallel tranches.

### 3.3 Earliest tranche after Phase 0.1 acceptance

**T1**, together with **T2a**, **T5a** and **T6a** in parallel. All are
**gated only on U-03** (the implementation-language decision). Their
specifications are frozen (T1, T2a) or self-contained (T5a, T6a).

Status: U-03 was resolved as OCaml at the start of T1. T1 (lexer, reader and
`lexdump` CLI) is implemented, and its audit findings were addressed in
T1.1. The LEX-01..13 test mapping is in `design-decisions.md` §6.4. Two
LEX properties can only be fully tested later:

- LEX-03 with actually activated declarations (T5/T6);
- LEX-07 literal-atom matching (T5).

### 3.4 Exit criteria for full functionality (C16)

- All suites pass with hardwired forms removed (T13).
- Examples A–G pass end-to-end.
- Determinism tests pass.
- Every DEFERRED item is resolved; every OPTIONAL item is documented as
  excluded.
- Every unproven claim in §11.2 is either proven, or supported by its stated
  test with no known counterexample. Test support is not a proof, and the
  documentation must say which applies.

---

## 4. Verification of Phase 0.1

Phase 0.1 is verified by document review:

- [ ] The five corrections are integrated into normative text (§1.3, §2.1, §2.5, §3.3, §4.3, §5).
- [ ] The three overstatements are corrected (§2.4.2–2.4.3, §2.5.7, §4.3.2, §9.3).
- [ ] Each of the eight safety contracts has before / deferred / test parts (§13.1–13.8).
- [ ] Every parser edge case listed in the brief appears in §12.
- [ ] The complexity review is recorded (§8.4).
- [ ] All U-items are classified (`design-decisions.md` §3).
- [ ] Every tranche has output, acceptance, regression, exclusions and TCB status (§3.2).
- [ ] Every diagnostic code and test ID cited in `architecture.md` exists in this plan, or is defined in `architecture.md` itself.
- [ ] No production code, dependencies, VM or prototype exists in the repository.
