# Yuho Improvement Roadmap

## Overview

28 workstreams. Phases 0-8 are implementation infrastructure. Phases 9-16 are language rigour -- making Yuho a legally sound DSL, not just a syntactically valid one. Phases 17-27 are **developer integration** -- making Yuho adoptable as infrastructure for legal tech products.

Priority: formal methods & execution > module resolution > defeasible reasoning > **type system & deontic logic** > library depth > tooling > interop > **containerization & API hardening > CI/CD & observability > SDKs & ecosystem > DX**.

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

── developer integration (phases 17-27) ─────────────────

Phase 17 (containers)   ──┐
Phase 18 (API harden)   ──┤── parallel, no deps
Phase 19 (CI/CD)        ──┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
Phase 20 (observability) Phase 22 (SDKs) Phase 27 (docs/DX)
  depends on 18          depends on 18   depends on 17, 18
              │
              ▼
Phase 21 (streaming)  ──── depends on Phase 18
Phase 23 (registry)   ──── depends on Phase 17
              │
              ▼
Phase 24 (webhooks)   ──── depends on Phase 23
Phase 25 (WASM/embed) ──── independent, can start anytime
Phase 26 (multi-tenant) ── depends on Phases 18, 20
```

---

## Phase 0: Doc-comment Preservation [S]

- [x] Move `doc_comment` out of grammar `extras` into named children of declarations
- [x] Add `doc_comment: Optional[str]` to `StructDefNode`, `FunctionDefNode`, `StatuteNode`, `ElementNode`, `FieldDef`
- [x] Update `builder.py` to extract `///` text from preceding doc_comment nodes
- [x] Regenerate tree-sitter parser

**Files**: `grammar.js`, `nodes.py`, `builder.py`

---

## Phase 1: Module Resolution [L]

- [x] Create `src/yuho/resolver/module_resolver.py` with `ModuleResolver` class
  - [x] Module cache to avoid re-parsing
  - [x] Path resolution: relative imports + library `referencing` paths
  - [x] Cycle detection
- [x] Wire `scope_analysis.py` to resolve imports and inject exported symbols
- [x] Wire `type_check.py` for cross-module `NamedType` resolution
- [ ] Wire `test.py` to resolve `referencing` before running tests

**Files**: new `resolver/`, modify `scope_analysis.py`, `type_check.py`, `test.py`

---

## Phase 2: Interpreter/Evaluator [XL]

### 2A: Core Evaluator
- [x] Create `src/yuho/eval/interpreter.py`
  - [x] `Environment` class (chained scopes, struct/function/statute defs)
  - [x] `Value` class (tagged union of runtime values)
  - [x] `StructInstance` (type_name + field values)
  - [x] `Interpreter(Visitor)` with visit methods for all expression types
  - [x] Full operator semantics (+,-,*,/,%,==,!=,<,>,<=,>=,&&,||)
  - [x] Pattern matching (wildcard, literal, binding, struct destructure)
  - [x] Match-case evaluation with guards and consequences
  - [x] Function calls with scoped environments

### 2B: Statement Execution
- [x] `VariableDecl` -- declare + init in scope
- [x] `ReturnStmt` -- exception-based control flow
- [x] `AssertStmt` -- evaluate condition, raise with source location
- [x] `Block` -- sequential execution

### 2C: Statute Evaluator
- [x] Create `src/yuho/eval/statute_evaluator.py`
  - [x] `StatuteEvaluator.evaluate(statute, facts, env)` -> `EvaluationResult`
  - [x] Per-element satisfaction checking
  - [x] `all_of`/`any_of` group evaluation
  - [x] Penalty range output

### 2D: CLI Wiring
- [ ] Replace `test.py` ad-hoc `_evaluate_expr` with real `Interpreter`
- [x] Add `:eval` to REPL with persistent `Environment`
- [x] Add `yuho eval <file>` CLI command

**Files**: new `eval/`, modify `test.py`, `repl.py`, `main.py`

---

## Phase 3: Defeasible Reasoning [L]

- [x] Grammar change: add `when <guard>` to `exception_block`
- [x] Add `guard: Optional[ASTNode]` to `ExceptionNode`
- [x] Update `builder.py` to extract exception guards
- [x] Create `src/yuho/eval/defeasible.py`
  - [x] `DefeasibleReasoner.evaluate_with_exceptions(statute, facts, env)`
  - [x] Base element evaluation -> exception guard checking -> defeat logic
  - [x] `DefeasibleResult` with reasoning chain (exportable trace)
- [x] Integrate into `StatuteEvaluator` so exceptions auto-apply
- [x] Update s300 (murder) exceptions with structured `when` guards

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
- [x] `fact movedProperty := TRUE` vs. `conclusion guiltyOfTheft := evaluateTheft(...)`
- [ ] Semantic analysis: conclusions must derive from facts, never the reverse
- [x] Transpile: clearly separate factual predicates from legal conclusions in English output
- **Why:** "The accused took the wallet" (fact) and "the accused committed theft" (conclusion) are epistemically different. Conflating them hides the inferential leap that legal reasoning requires.

**Files:** `grammar.js`, `nodes.py`, `builder.py`, `type_inference.py`, `type_check.py`

---

## Phase 10: Deontic Logic [XL]

Criminal statutes are inherently deontic -- they define what is prohibited, obligatory, or permitted. Yuho currently has no way to express these modalities; everything is descriptive.

### 10A: Deontic Operators
- [x] Add keywords `obligation`, `prohibition`, `permission` as element qualifiers
- [x] Syntax: `obligation duty_to_report := "Must report knowledge of felony";`
- [x] These are distinct from `actus_reus`/`mens_rea` -- they encode what the law *requires*, not what constitutes an offense
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
- [x] Syntax: `statute 300 "Murder" effective 1872-01-01 { ... }`
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
- [x] Syntax: `actus_reus death := "Death of the victim" caused_by act;`
- [ ] Distinguish factual causation ("but for") from legal causation ("proximate cause")
- [ ] Model novus actus interveniens (intervening acts breaking the chain)
- **Why:** s299 (culpable homicide) *requires* a causal link: the act must *cause* death. Currently this is just a string description. Making it structural lets verification check that every homicide offense actually specifies a causal chain.

### 12B: Burden of Proof Constructs
- [x] `burden` qualifier on elements: `burden prosecution` (default) vs. `burden defence`
- [x] `presumed` modifier: `presumed TRUE` means the fact is assumed unless rebutted
- [x] `standard` qualifier: `beyond_reasonable_doubt`, `balance_of_probabilities`, `prima_facie`
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
- [x] Syntax: `statute 300 "Murder" subsumes 299 { ... }`
- [ ] Semantic: if s300 is satisfied, s299 is necessarily satisfied
- [x] Verification: Z3 checks that subsumption claims are consistent with element definitions
- **Why:** Murder (s300) is a special case of culpable homicide (s299). Dacoity (s395) subsumes robbery (s390) which subsumes theft (s378). These hierarchies are legally significant -- charging the subsuming offense includes the subsumed one.

### 13B: First-class Cross-references
- [ ] `ref s24.dishonestly` as an expression that resolves to the definition from s24
- [ ] Reference validation at parse time: warn if target doesn't exist
- [ ] Transpile: hyperlink references in HTML/LaTeX output
- [x] Dependency graph: `yuho deps <file>` shows which statutes depend on which
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

## Phase 17: Containerization & Cloud-Ready Deployment [M]

The archived v4 Dockerfile targets the old structure. v5 uses `pyproject.toml` with hatchling and a tree-sitter native lib that must be compiled. Without a Dockerfile, evaluation stops at `pip install`.

- [ ] Multi-stage `Dockerfile` for v5 (builder stage compiles tree-sitter `.so`, prod stage is `python:3.12-slim` + venv copy)
- [ ] `docker-compose.yml` with `yuho-api` and `yuho-mcp` services, shared volume for `library/`, health checks on `/health`
- [ ] `.dockerignore` excluding `archive/`, `.git/`, `tests/`, `doc/`
- [ ] `ENTRYPOINT ["yuho"]` with `CMD ["api"]` default; document `docker run yuho serve --stdio` for MCP
- [ ] Helm chart scaffold (`deploy/helm/yuho/`) with configmap for `config.toml`, secret for auth tokens, liveness/readiness probes
- [ ] ARM64 + AMD64 multi-arch CI build
- [ ] `doc/DEPLOYMENT.md` covering Docker, Compose, K8s, Cloud Run patterns
- **Why:** Compliance SaaS runs K8s. Without containers, Yuho can't be deployed behind a load balancer, can't autoscale, can't be included in IaC.

**Files**: new `Dockerfile`, `docker-compose.yml`, `deploy/helm/yuho/`, `doc/DEPLOYMENT.md`

---

## Phase 18: API Hardening [L]

REST server uses `http.server.ThreadingHTTPServer` with no auth, no versioning, no pagination. MCP already has token-bucket rate limiting and `auth_token` config, but REST has none of this. CORS is hardcoded `*`.

- [ ] Bearer-token auth middleware on `YuhoAPIHandler` (reuse `mcp.auth_token` from config, check `Authorization` header, skip `/health`)
- [ ] Extract `RateLimiter`/`TokenBucket` from `mcp/server.py` to shared `src/yuho/middleware/rate_limit.py`; wire into REST handler
- [ ] API versioning: prefix routes with `/v1/`, add `X-API-Version` response header, keep unversioned as v1 aliases
- [ ] Pagination for list endpoints: `/v1/rules?offset=0&limit=50`
- [ ] Structured error codes: `{"error": {"code": "PARSE_ERROR", "message": "...", "details": [...]}}` matching `AnalysisError.error_code`
- [ ] `X-Request-ID` propagation (consistent across REST and MCP)
- [ ] CORS configurability via config instead of hardcoded `*`
- [ ] OpenAPI spec update: auth scheme, versioned paths, error schemas, pagination params
- **Why:** A contract analysis platform exposing Yuho as a microservice needs auth, rate limiting, and structured error codes for programmatic error handling.

**Files**: modify `api.py`, new `src/yuho/middleware/{rate_limit,auth}.py`, modify `config/schema.py`, modify `doc/openapi.yaml`

---

## Phase 19: Machine-Readable CLI Output & CI/CD Integration [M]

Legal tech devs integrate Yuho into CI/CD the same way ESLint runs in CI. No standardized exit-code contract, no SARIF output, no pre-commit hook config.

- [ ] Standardize exit codes: 0=success, 1=error, 2=warnings-only (for `check`, `lint`, `test`); document in `doc/CLI_EXIT_CODES.md`
- [ ] SARIF output for `yuho check` and `yuho lint`: `--format sarif` (GitHub Code Scanning compatible, annotations on PR diffs)
- [ ] JUnit XML output for `yuho test`: `--format junit` for CI test result ingestion
- [ ] GitHub Action: `.github/actions/yuho-check/action.yml` wrapping `pip install yuho && yuho batch check . --json`
- [ ] Pre-commit hook config: `.pre-commit-hooks.yaml` at repo root
- [ ] GitLab CI template: `doc/ci-templates/gitlab-ci.yml`
- [ ] `yuho ci-report` command: runs check+lint+test, produces unified JSON/SARIF report
- **Why:** A legislative drafting platform with 200+ `.yh` files needs statute validation in CI. SARIF = annotations on GitHub PRs. Pre-commit hooks catch errors before CI.

**Files**: modify `main.py`, new `src/yuho/output/{sarif,junit}.py`, new `ci_report.py`, new `.github/actions/yuho-check/`, new `.pre-commit-hooks.yaml`

---

## Phase 20: Observability [M]

Structured JSON logging exists. MCP tracks `_stats` with per-tool counts and latency histograms. But no Prometheus endpoint, no OTel traces, no way for ops teams to monitor Yuho in production.

- [ ] Prometheus metrics endpoint: `GET /metrics` exposing `yuho_requests_total{endpoint,status}`, `yuho_request_duration_seconds{endpoint}` (histogram), `yuho_parse_errors_total`, `yuho_active_connections`
- [ ] Export MCP server `_stats` as Prometheus metrics
- [ ] OpenTelemetry tracing: optional `yuho[observability]` extra; auto-instrument parse->AST->transpile pipeline with spans; propagate `traceparent` header
- [ ] Health endpoint enrichment: `{"status":"healthy","uptime_seconds":N,"requests_served":N,"parser_cache_size":N}`
- [ ] Configurable log level via `YUHO_LOG_LEVEL` env var
- **Why:** A compliance SaaS needs to know when parse times spike, which endpoints are hot, whether rate limiting is firing. Without observability, debugging = reading raw container logs.

**Files**: modify `api.py`, new `src/yuho/middleware/metrics.py`, modify `mcp/server.py`, modify `logging_utils.py`, modify `pyproject.toml`

**Dependencies**: Phase 18 (uses middleware pattern)

---

## Phase 21: Streaming & Real-time [L]

Z3/Alloy verification takes 5-30s. REST API is sync request-response only. Legal tech devs building real-time editors or verification dashboards need streaming progress.

- [ ] WebSocket endpoint: `ws://host:port/ws` accepting JSON-RPC messages (reuse MCP tool signatures)
- [ ] SSE for long-running ops: `POST /v1/verify` returns `202 Accepted` + `Location: /v1/jobs/{id}`; `GET /v1/jobs/{id}/events` streams SSE progress (`parsing`, `z3_encoding`, `z3_solving`, `complete`)
- [ ] Async job queue: in-memory for single-instance, clean interface for Redis-backed queue in multi-instance
- [ ] WebSocket live validation: client sends partial source on keystroke, server debounces and pushes diagnostics
- [ ] Batch transpile streaming: `POST /v1/batch/transpile` streams results as NDJSON
- **Why:** A browser-based legislative drafting tool wants live validation (WS). A compliance dashboard wants verification progress for 50 statutes (SSE). Without streaming, UI freezes or client must poll.

**Files**: new `src/yuho/api/{websocket,sse,jobs}.py`, modify `api.py`, modify `pyproject.toml`

**Dependencies**: Phase 18 (auth and rate limiting cover WS connections)

---

## Phase 22: Multi-Language SDKs [L]

Yuho is Python-only. Legal tech is built in TypeScript (frontend), Java (enterprise), Go (microservices). The OpenAPI spec is the natural starting point but needs completion first.

- [ ] Complete OpenAPI spec: all endpoints, request/response schemas, auth, pagination
- [ ] TypeScript/JavaScript SDK: generated or hand-written thin wrapper; publish to npm as `@yuho/sdk`; typed responses, async/await, streaming
- [ ] Go SDK: generated via `oapi-codegen`; publish as `github.com/gongahkia/yuho-go`; context-based cancellation
- [ ] Java SDK: generated via `openapi-generator`; Maven Central publish
- [ ] All SDKs: retry logic, configurable base URL, auth token injection, timeout config
- [ ] Integration tests: each SDK starts `yuho api`, runs parse/validate/transpile/lint, verifies results
- [ ] `doc/SDK_QUICKSTART.md` with examples in Python, TypeScript, Go, Java
- **Why:** An enterprise contract management system in Java can't call a Python SDK. A Next.js legal AI assistant needs a TS client. Without multi-lang SDKs, every non-Python consumer hand-rolls HTTP calls.

**Files**: new `sdks/{typescript,go,java}/`, modify `doc/openapi.yaml`, new `doc/SDK_QUICKSTART.md`

**Dependencies**: Phase 18 (versioned, authenticated API with proper error schemas)

---

## Phase 23: Registry & Package Ecosystem [L]

Library system has `PackageMetadata`, `.yhpkg` format, `lockfile.py`, `signature.py`, registry client. Registry URL points to `registry.yuho.dev` but the server likely doesn't exist yet. Local package ops work; remote registry is the gap.

- [ ] Registry server: minimal HTTP API (static JSON index on GitHub Pages as v1, or FastAPI); endpoints: `GET /v1/packages`, `GET /v1/packages/{name}/{version}`, `POST /v1/packages`, `GET /v1/search?q=`
- [ ] Real package signature verification: Ed25519 (current `_verify_signature` only checks length==64)
- [ ] Transitive dependency resolution with conflict detection (version ranges `>=1.0.0 <2.0.0`)
- [ ] `yuho library init` -- create `metadata.toml` interactively
- [ ] Package namespace: `{jurisdiction}/{section}` (e.g., `singapore/s300`) for multi-jurisdiction
- [ ] Mirror support: organizations host private registries via `library.registry_url`
- **Why:** A legal tech company encoding Indonesian statutes needs to publish packages their team can share. Without a real registry, consumers manually copy `.yh` files.

**Files**: new `src/yuho/registry/server.py`, modify `library/{resolver,signature,package}.py`, modify `commands_registry.py`

**Dependencies**: Phase 17 (registry server needs containerization)

---

## Phase 24: Webhook & Event System [M]

Statutes change. When Singapore amends s300, every downstream system consuming that statute needs to know. No notification mechanism exists.

- [ ] Event model: `statute.updated`, `statute.deprecated`, `statute.created`, `package.published`, `verification.failed` as typed dataclasses
- [ ] Webhook registration: `POST /v1/webhooks` with `{url, events, secret}`; stored in config
- [ ] Webhook delivery: HTTP POST with HMAC-SHA256 in `X-Yuho-Signature`, retry with exponential backoff (3 attempts)
- [ ] CLI: `yuho webhook add <url> --events statute.updated`, `yuho webhook list`, `yuho webhook test <id>`
- [ ] File-watch mode: `yuho watch <dir>` monitors `.yh` files, re-validates, fires events
- [ ] Config section: `[webhooks]` in `config.toml`
- **Why:** A compliance SaaS needs to re-run validation when a statute changes. A legal AI assistant needs to invalidate cache when `s300` gets a new exception. Without webhooks, consumers must poll.

**Files**: new `src/yuho/events/{model,webhook}.py`, new `src/yuho/cli/commands/{watch,webhook}.py`, modify `config/schema.py`

**Dependencies**: Phase 23 (registry events trigger webhooks)

---

## Phase 25: Embedding & WASM [XL]

The playground is a local server with HTML served from Python. True browser embedding = tree-sitter parser as WASM, parsing client-side with zero server round-trips.

- [ ] Tree-sitter WASM build: `tree-sitter build --wasm` for `tree-sitter-yuho`; publish to npm
- [ ] JavaScript binding: thin JS wrapper over WASM parser providing `parse(source) -> AST JSON`
- [ ] Pyodide bundle: package Yuho's Python code (minus native tree-sitter) for Pyodide; `validate()` and `transpile()` in-browser
- [ ] Standalone playground: static HTML/JS site using WASM parser + client-side transpilation to JSON/English/Mermaid
- [ ] Embeddable widget: `<script src="cdn.yuho.dev/embed.js">` renders code editor with live validation
- [ ] Monaco/CodeMirror integration: syntax highlighting, error squiggles, completions from WASM parser
- **Why:** A legal AI assistant wants to validate Yuho in-browser without a server call. A law school e-learning platform wants an embedded editor. Without WASM, every client-side use case requires network latency.

**Files**: modify `src/tree-sitter-yuho/`, new `packages/{wasm,playground,embed}/`

---

## Phase 26: Multi-Tenancy & Workspace Isolation [L]

When Yuho serves multiple organizations as a hosted service, each tenant needs isolated library packages, config, and usage tracking. Current server is single-tenant.

- [ ] Workspace model: `Workspace(id, name, config_overrides, library_path, api_key)`
- [ ] Tenant routing: `X-Workspace-ID` header or subdomain routes to appropriate workspace
- [ ] Per-tenant rate limiting: extend `RateLimiter` with workspace-scoped buckets
- [ ] Usage tracking: `POST /v1/usage` returns `{requests_today, parse_count, transpile_count, verify_count}` per workspace
- [ ] Quota enforcement: configurable limits per workspace (`max_requests_per_day`, `max_source_length`, `allowed_transpile_targets`)
- [ ] CLI: `yuho workspace create <name>`, `yuho workspace switch <name>`, `yuho workspace list`
- **Why:** A hosted Yuho-as-a-service serving 10 law firms needs each firm's library isolated. A platform with free/premium tiers needs usage quotas. Without multi-tenancy, hosting for multiple customers = separate deployments.

**Files**: new `src/yuho/workspace/{model,router}.py`, modify `api.py`, `middleware/rate_limit.py`, `config/schema.py`, new `commands/workspace.py`

**Dependencies**: Phase 18 (auth), Phase 20 (metrics per workspace)

---

## Phase 27: Documentation & Developer Experience [M]

Existing docs cover SDK, config, formal semantics, OpenAPI. No interactive API explorer, no cookbook for common integration patterns, no "getting started for legal tech devs" tutorial.

- [ ] Interactive API explorer: Swagger UI served at `GET /docs` on the API server (auto-generated from OpenAPI spec)
- [ ] Cookbook: `doc/cookbook/` with practical recipes:
  - [ ] `compliance-saas.md` -- building a compliance checker with Yuho API
  - [ ] `contract-analysis.md` -- parsing contracts and mapping to statute elements
  - [ ] `legislative-drafting.md` -- CI/CD for statute version control
  - [ ] `legal-ai-assistant.md` -- MCP integration with Claude/GPT
  - [ ] `multi-jurisdiction.md` -- managing statutes across jurisdictions
- [ ] `doc/GETTING_STARTED.md` -- 5-minute quickstart (Docker -> API call -> parse result)
- [ ] Architecture diagram in `doc/ARCHITECTURE.md`
- [ ] Changelog automation: `CHANGELOG.md` from git tags + conventional commits
- [ ] Error catalog: `doc/ERROR_CODES.md` mapping every `error_code` to description, causes, fixes
- **Why:** A dev evaluating Yuho spends 10 minutes before deciding to adopt or reject. Without quickstart, cookbook, and interactive explorer, they choose a simpler tool.

**Files**: modify `api.py` (serve Swagger UI at `/docs`), new `doc/{cookbook/,GETTING_STARTED.md,ARCHITECTURE.md,ERROR_CODES.md}`

**Dependencies**: Phase 17, 18 (Docker quickstart + complete OpenAPI spec)

---

## Verification Checklist

After all phases:

### Language & Semantics (Phases 0-16)
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

### Developer Integration (Phases 17-27)
- [ ] `docker build -t yuho . && docker run -p 8080:8080 yuho` -- API server starts in <30s
- [ ] `curl -H "Authorization: Bearer <token>" localhost:8080/v1/parse` -- auth works
- [ ] `curl localhost:8080/v1/parse` without token returns 401
- [ ] `yuho check --format sarif` produces valid SARIF JSON
- [ ] `yuho test --format junit` produces valid JUnit XML
- [ ] GitHub Action validates `.yh` files on PR and annotates diffs
- [ ] `GET /metrics` returns Prometheus-format counters and histograms
- [ ] WebSocket live validation: send source, receive diagnostics within 200ms
- [ ] TypeScript SDK: `await yuho.parse(source)` returns typed AST
- [ ] `yuho library install singapore/s300` resolves from registry with transitive deps
- [ ] Webhook fires on `statute.updated` event with valid HMAC signature
- [ ] Tree-sitter WASM: `parse()` works in browser with no server
- [ ] Multi-tenant: two workspaces with separate libraries don't leak data
- [ ] `GET /docs` serves Swagger UI with tryable endpoints
