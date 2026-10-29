# Technical Risks — Phase 0.1

Severity: **High** (could invalidate a decision or the safety claim),
**Medium** (significant redesign or effort), **Low** (local fix). Each entry
gives the problem, its status after Phase 0.1, and **what remains difficult**.

Section references (§) point to `architecture.md`. Decision IDs point to
`design-decisions.md`.

---

## 1. Contradictions in the brief

All of these are resolved in the normative text as of Phase 0.1.

| ID | Contradiction | Resolution (Phase 0.1) | Residual difficulty |
|---|---|---|---|
| C-01 | "Arbitrary token grammars" vs. a fixed lexer | **Resolved** (correction 1). Fixed vocabulary; raw regions only (§2.1). | Brace-form raw regions close on unbalanced braces in strings; users must choose the long-bracket form (§12). |
| C-02 | Separate stages vs. grammar-generating and type-directed macros | **Resolved** (correction 2). Per-item pipeline; type-directed macros never declare syntax (§5). | Compilation of a module is sequential. Incremental rebuilds must invalidate every item after a changed syntax declaration. |
| C-03 | Global precedence arrays vs. independent imports | **Resolved** (correction 3). Transitive order from scoped arrays; unrelated ⇒ parenthesise (§2.5). | A bridging array can relate more operator pairs than its author intended. Diagnostics must show edge paths. |
| C-04 | Replaceable checkers vs. soundness | **Resolved** (correction 4). Checkers are frontends; guarantee split G1–G6 (§4.3.2). | Users may mistake checker claims for guarantees (S-10). |
| C-05 | Hygiene vs. macro-generated grammar | **Resolved.** Generated declarations land in the use-site scope, gated by `declare_syntax`. | Macro authors must choose contexts for generated names deliberately (`ident_at`). |
| C-06 | Block-level activation vs. late expansion | **Resolved** (correction 5). Every item-position macro is head-expanded eagerly (R-32). | Eager expansion means item-position macros cannot depend on types. |
| C-07 | "Lua-like" vs. static typing | **Resolved** by rewording (R-01). | Less flexible than Lua. |
| C-08 | "Invent type rules" vs. a fixed core | **Resolved** by wording (§4.1, §4.3.1). | Subtyping, higher-kinded types, and *guaranteed* linearity or effects are not expressible. |
| C-09 | Full vision vs. one developer | Scheduling (P-01). | Unproven (U-P8). |
| C-10 | *(new)* Phase 0 text implied literal prefixes restrict the whole grammar | **Resolved.** Dispatch pattern vs. body (§2.4.2). | — |
| C-11 | *(new)* Phase 0 overstated what generalized parsers cannot do | **Resolved** (§9.3). | — |

---

## 2. Circular compilation dependencies

| ID | Cycle | Break | Status |
|---|---|---|---|
| D-01 | Macros written in L; conveniences are macros | Layered prelude (R-20) | Accepted |
| D-02 | Types → macro → grammar → parsing | Type-directed macros cannot declare syntax | Accepted |
| D-03 | Parser at *i+1* calls a `meta def` at *i* still in progress | Phase-1 items complete P1–P7 before the next item is read | Accepted |
| D-04 | Cyclic module syntax dependencies | Import cycles forbidden at all phases (R-39) | Accepted, **stricter** than Phase 0 |
| D-05 | Rules need operators; operators need rules | Rules declared with core forms; prelude layering | Accepted |
| D-06 | Core must check `Syntax[K]` for user `K` | Builtin opaque nominal types; no special checker rules | Accepted |
| D-07 | Phase-1 code mentioning own-module phase-0 types | Forbidden by phase separation | Accepted |
| D-08 | *(new)* Block items need P1–P3 before the enclosing item's elaboration | Block syntax uses only phase-1 code, which cannot see phase-0 locals | Accepted (§5.2) |
| D-09 | *(new)* Macro-generated imports would make the dependency graph depend on expansion | Forbidden (R-40) | Accepted |

**Residual.** D-04, D-07 and D-09 forbid some natural library layouts.
Users will need to split modules.

---

## 3. Soundness risks

### S-01 Trusted base larger than intended — **High → mitigated**

The TCB is the core checker, the primitive table, the interpreter, the
interface loader, and the driver's module-identity assignment (§7.1).
**Mitigation:** fully annotated core (R-44); one primitive table with
agreement tests (R-36); re-check on load.
**Residual:** the interpreter is tested, not verified. No progress or
preservation proof exists (U-P2).

### S-02 Elaboration silently changes meaning — **Medium, inherent**

Not solvable in general (§7.3).
**Mitigation:** dumps, traces, differential tests.

### S-03 Checker bypass — **Resolved**

Forbidden. A checker is a frontend (§4.3).

### S-04 Private types leaking through macros — **High → resolved conservatively**

Phase 0 proposed authorisation annotations, which a buggy elaborator could
forge. Phase 0.1 replaces this with **authorisation by module membership
only**. Macros from `M` must call `M`'s exported functions (§13.4).
**Residual:** an extra call per privileged operation, recoverable by
post-check inlining. Some macro styles (direct field access to a library's
opaque types) are impossible in v0.1.

### S-05 Phase-1 code escaping capabilities — **Medium → mitigated**

Capability-tagged primitives; deterministic memory and step counters
(§13.3).
**Residual:** the gate is trusted code.

### S-06 Leftover metavariables — **Resolved**

The core has no metavariables (R-44).

### S-07 Polymorphism + `Ref` — **Resolved**

Core value restriction (§13.5).
**Residual:** polymorphic constants must be written as functions.

### S-08 *(new)* Host stack overflow in a tree-walking interpreter — **Medium → resolved by rule**

Without an explicit depth bound, deep recursion crashes the host process.
That would violate the "never a host crash" behaviour that G1 relies on.
**Rule:** a call-depth limit turns this into a panic (R-45).
**Residual:** the limit must be enforced below the host's real stack
capacity on every platform. This needs a per-platform test.

### S-09 *(new)* Primitive typing disagrees with implementation — **High → mitigated**

This is the classic source of unsoundness in small languages.
**Mitigation:** one table read by both checker and interpreter, and an
agreement property test per primitive (§13.6).
**Residual:** property tests sample inputs. Edge cases (overflow boundaries,
NaN) must be enumerated explicitly.

### S-10 *(new)* Checker claims mistaken for guarantees — **Medium**

**Mitigation:**
- mandatory boundary modes (`E-CHK-BOUNDARY-REQUIRED`);
- `W-CHK-ASSUMED`;
- diagnostics label properties as "core-verified" or "checker-claimed".

**Residual:** a social risk, not a technical one.

### S-11 *(new)* Phase-1 global state breaking determinism — **Resolved**

Phase-1 defs must be syntactic values (R-35).

---

## 4. Grammar conflict risks

| ID | Risk | Status / mitigation | Residual |
|---|---|---|---|
| G-01 | Literal-first leading patterns are too restrictive | **Mitigated:** statement continuations (R-26); unrestricted bodies (R-24); longer patterns | Class-first leading patterns are DEFERRED (U-14). |
| G-02 | Keyword claiming breaks code on import | Explicit syntax imports; raw identifiers; `W-SYN-CLAIM-SHADOWS` | Adding an exported production is a breaking library change. |
| G-03 | Claimed keyword vs. expression statement | A claim always dispatches; `` `x` `` escapes | — |
| G-04 | Same-token prefix vs. infix | Separate tables; call syntax is core | — |
| G-05 | Committed choice gives poor errors | Parser API expectation sets; local `try` | Quality depends on extension authors. |
| G-06 | Raw-region closer collisions | Long-bracket levels | — |
| G-07 | Precedence cycles via imports | Incremental cycle check with edge paths | — |
| G-08 | Two versions of one library | The build forbids it | — |
| G-09 | *(new)* `--` comment inside apparent operators (`x--y`) | Comment priority + lint (§12) | Surprising to C-family users. |
| G-10 | *(new)* Maximal munch forces spaces (`a+-b`) | Fix-it diagnostics; never split runs | A minor usability cost, accepted for stability. |
| G-11 | *(new)* A `stmt` continuation key also used as an `expr` operator | Cross-table conflict rule (§6.1) | — |
| G-12 | *(new)* Brace raw regions close early on string content | Documented; long-bracket form | Users will hit it once. |
| G-13 | *(new)* Multi-token lookahead dispatch on long patterns | Patterns are finite; matching is bounded | Long patterns slow dispatch slightly; acceptable. |

---

## 5. Hygiene problems

| ID | Problem | Status | Residual |
|---|---|---|---|
| H-01 | Custom parsers create binders from tokens | Scope sets handle it; there is no context-free identifier constructor | — |
| H-02 | Hygienic type names in type-directed output | Types resolve through scope sets | Printing renamed types in diagnostics. |
| H-03 | Generated keywords are visible by text | Intended (text dispatch, U-08) | No "private keywords". |
| H-04 | Grammar hygiene for re-parsed token trees | **Mitigated conservatively** by R-38: root stamps, whole-group splicing, `E-SYN-MIXED-ENV` | May be too restrictive; the claim is unproven (U-P3). |
| H-05 | Use-site scopes in definition contexts | Adopt the Racket rules; port tests | Eager head-expansion multiplies definition contexts; must be tested heavily. |
| H-06 | Capture abuse | Lint | — |
| H-07 | *(new)* `restamp` misuse reintroduces grammar capture | Explicit and visible, like `ident_at`; lint on `restamp` to use site | — |

---

## 6. Project and implementation risks

| ID | Risk | Severity | Mitigation | Residual |
|---|---|---|---|---|
| P-01 | Feature set too large for one developer | **High** | Tranches with OPTIONAL items removed from the critical path; checkers last | Unproven (U-P8). |
| P-02 | Specification drift | Medium | Frozen sections need a decision entry plus a test update | Discipline. |
| P-03 | AI-generated code wrong in the TCB | **High** | Small, fully annotated core; one primitive table; hand review; property tests | Reviewer attention. |
| P-04 | Slow interpreter for compile-time code | Medium | Counters, profiling; optional bytecode | — |
| P-05 | Tooling must run user code | Medium | Sandboxed phase 1 reused by the language server | — |
| P-06 | Diagnostics across layers | Medium | Expansion backtraces; golden tests | Ongoing. |
| P-07 | Cyclic values in Rust | Medium → **closed** | Not applicable: OCaml was chosen (U-03); run-time values use the OCaml GC (U-16). Language-level memory safety remains unverified. | — |
| P-08 | Non-determinism | Medium | Deterministic IDs, counters, double-compile tests | — |
| P-09 | Observable expansion order | Medium | **Specified** (§13.8) | Programs will depend on it; it is now part of the contract. |
| P-10 | *(new)* The freeze proves premature | Medium | Frozen areas are small (lexer, core, primitives, data shapes) and chosen for stability | A core change after T2 would ripple into later tranches. |
| P-11 | *(new)* Internal consistency mistaken for implementability | Medium | Unproven claims tracked explicitly (§11.2) | — |
