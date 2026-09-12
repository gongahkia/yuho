# Yuho repository handoff

This is a self-contained technical and product summary of
[`gongahkia/yuho`](https://github.com/gongahkia/yuho), intended to be uploaded
to a ChatGPT web conversation. It describes the project’s intended purpose,
what the checked-in implementation currently does, its evidence boundaries,
the state of `main`, and every GitHub issue visible on 2026-09-12.

## Snapshot and evidence basis

- Repository: `gongahkia/yuho`, public, MIT-licensed.
- Branch/commit inspected: `main` at `b5f37d9e92ff11348836a273896c63185fc1b328`
  (`addedgoodideas`), matching `origin/main`. The worktree was clean before
  this document was added.
- Package version: `5.1.0`; Python requirement: `>=3.10`.
- Latest visible GitHub release: tag `v5.1.0`, published 2026-03-29.
- Scale: 2,087 tracked files. The largest areas are `library/` (1,661 files),
  `src/` (145), `tests/` (127), `docs/` (45), `scripts/` (40), and
  `mechanisation/` (22). There are 1,113 `.yh` files and 264 Python files.
- GitHub issues: 32 in the visible history—27 open and 5 closed. The issue
  bodies and comments were inspected, not only their titles.
- Evidence inspected includes manifests, task scripts, documentation, grammar,
  AST/canonical-IR/runtime/verifier code, representative encodings, corpus
  ledgers, tests, CI workflows, current Actions runs, branch protection, commit
  history, and issue discussions.
- Heavy local verification was intentionally not rerun after a verification
  attempt caused memory pressure on the workstation. Current GitHub Actions
  results and checked-in evidence are reported instead; skipped local checks
  are not treated as passes.

When sources disagree, use this reliability order:

1. Current source, generated artifacts, tests, and GitHub Actions results.
2. `docs/release/capability-claims.json` and `docs/release/evidence.md`.
3. `docs/positioning/status-matrix.md` and architecture/researcher docs.
4. README and older retrospective/archive prose.

## Executive assessment

Yuho is a serious research-oriented legal DSL toolchain, not merely a grammar
or statute dataset. It aims to turn legal provisions—currently centered on
Singapore criminal law—into typed, inspectable, partly executable programs.
Its strongest assets are the breadth of its compiler/tooling surface, the full
524-section Singapore Penal Code encoding, retained consistency checks,
explicit backend capability diagnostics, and a substantial Lean formalisation
of a bounded abstract fragment.

Its present limitation is semantic depth rather than surface breadth. The
parser and AST can represent many legal-looking constructs, but important
criminal-law concepts still reduce to unscoped Boolean fact names or inert
metadata. Causation, time, fault, voluntary conduct and omissions, participants,
attempts, context-specific consent, evidential burdens and presumptions,
territorial applicability, cross-Act packages, and precedent-sensitive case
rules are tracked as open semantic work. Consequently, “parses,” “exports,” or
“has a Lean theorem” must not be read as “legally faithful” or “fully
executable.”

The current `main` branch is not release-ready. Its latest CI run is red, the
generated Tree-sitter parser is behind `grammar.js`, Canonical IR source is at
v1.2 while core docs still say v1.1, newly added typed-outcome work is not
integrated into the conformance matrix or corpus, and no branch protection or
repository ruleset protects `main`.

The clearest product description is:

> Yuho is a local Python/CLI compiler and corpus toolkit for encoding statutes
> in a Tree-sitter-based DSL, analyzing their structure, evaluating a bounded
> Boolean/typed-fact rule fragment, exporting legal and visualization formats,
> and comparing selected runtime behavior with Z3 and Lean-side models. It is a
> research and review tool, not legal advice, a hosted decision service, or an
> end-to-end proof of legal correctness.

## What Yuho sets out to do

Yuho’s long-term thesis is that statutes can be represented as source code with
enough structure to support all of the following from one source:

- human review of definitions, elements, subsections, exceptions, authorities,
  and penalties;
- parser, type, semantic, lint, and source-location diagnostics;
- evaluation of fact patterns against statutory rules;
- explainable traces showing satisfied and failed elements;
- machine-checkable verification through solver/formal backends;
- exports for developers, lawyers, documents, diagrams, and legal interchange;
- a versioned, provenance-aware statute corpus rather than isolated demos;
- cross-section and eventually cross-Act composition;
- comparative encoding across related common-law criminal codes.

The project focuses on criminal statutes because they stress conjunction and
disjunction of offence elements, fault and physical elements, exceptions and
defences, burdens, participation, causation, and structured sentencing. The
syntax is intended to be jurisdiction-agnostic, but the mature corpus and most
semantics are Singapore Penal Code-oriented.

The project positions itself as narrower than L4, less mature in literate
one-to-one legislative methodology than Catala, not a benefits engine like
OpenFisca, not a non-programmer authoring environment like Blawx, and not an
interchange standard like Akoma Ntoso or LegalRuleML. Those last two are export
targets; emitting them is not proof of semantic equivalence.

## What the repository currently contains

### End-to-end data flow

The intended and partially implemented compiler path is:

```text
.yh source
  -> Tree-sitter concrete syntax tree (CST)
  -> immutable Python AST (`ModuleNode` and descendants)
  -> versioned Canonical IR with deterministic serialization/hash
  -> semantic/type/lint analysis
  -> runtime evaluation and/or verifier adapters
  -> JSON, English, LaTeX, Mermaid, Alloy, DOCX, Akoma Ntoso, LegalRuleML
```

The canonical boundary is important: parser acceptance is not supposed to
imply executable or backend support. Each consumer classifies a feature as
`modeled`, `ast_adapter`, or `unsupported`; unsupported combinations should
produce structured `YIR...` diagnostics rather than silently approximating
meaning.

In practice, the transition is incomplete. Canonical IR models statutes,
provision paths, recursive requirement trees, subsection branches, burden
metadata, penalties, dependency edges, and newly added outcome transitions.
Expression execution, exceptions, most exports, and parts of verifier lowering
still use named AST adapters.

### Main subsystems

| Area | Current implementation | Honest status |
|---|---|---|
| Parser | Tree-sitter grammar, checked-in generated C parser, Python binding | Partial; all 524 SG sources have historical parse evidence, but #39 is a known semantic defect and generated artifacts currently lag grammar source |
| AST | Immutable nodes, `ASTBuilder`, visitors, transforms | Broad and generally stable |
| Analysis | Shared parsing, AST, canonical lowering, type/scope, lint, metrics, caching | Broad, but cache tests fail in current CI |
| Type system | Nominal primitives/named types, structs, enums, aliases, optionals, arrays, refinements, some inference | Partial; generics are preserved but not substituted or enforced end-to-end |
| Canonical IR | Deterministic JSON plus semantic/artifact hashes, rule branches, consumer capabilities | Partial; source says v1.2, core docs say v1.1, and not every layer consumes it directly |
| Runtime | Groups, definitions, subsection branches, exceptions, limited case-law effects, penalties, cross-section guards, explanations | Partial; much legal meaning still comes from Boolean keys |
| Z3 | Constraint generation, differential checks, penalty bounds, exception priority, selected cross-section dependencies | Partial with explicit rejection of unsupported features |
| Alloy | Generated bounded structural model and optional analyzer execution | Secondary bounded-shape smoke backend, not parity evidence |
| Lean | 19 Lean files with abstract semantics/theorems under Lean 4.10.0 | Substantial bounded mechanisation, but disconnected from production Canonical IR |
| Transpilers | JSON, English, LaTeX, Mermaid/mindmap, Alloy, DOCX, AKN, LegalRuleML | Mixed: most are snapshot/XSD tested; DOCX is partial; PDF/SVG/PNG need external tools |
| Corpus tools | Scrapers/builders, coverage/provenance, source maps, reference/semantic graphs, cross-jurisdiction diff | Strong tooling; legal-source and review evidence remains partial |
| LSP/editor | `pygls` server and VS Code extension | Partial but usable |
| Hosted API | OpenAPI document only | No hosted decision service implementation |

### Language surface

The `.yh` language includes:

- primitive literals/types: `int`, `float`, `bool`, `string`, `money`,
  `percent`, `date`, `duration`, and `void`;
- structs and inheritance, struct literals, enums, aliases, optional/array/
  refinement/generic syntax;
- declarations, assignments, functions, expressions, operators, lists,
  indexing, field access, assertions, and `match`/`case` expressions;
- statute jurisdiction, dates, amendments, hierarchy, and annotations;
- definitions, `actus_reus`, `mens_rea`, `circumstance`, nested `all_of` and
  `any_of`, subsections, illustrations, exceptions, and case law;
- burden labels and standards, presently metadata-aware but not a complete
  proof-state system;
- imprisonment, fines, caning, death, minimums, concurrent/consecutive modes,
  `cumulative`/`alternative`/`or_both`, sibling penalties, and guards;
- exception priority and defeat/rebut/undercut relations;
- imports, references, `is_infringed`, and `apply_scope`;
- limited executable case-law effects with treatment/precedence selection;
- experimental civil primitives, legal tests, conflict checks, parties,
  fact-event structures, timeline syntax, and newly added outcome syntax.

There are intentionally no loops. The model favors declarative rule trees and
pattern matching.

### Runtime semantics actually present

- Statutes lower to recursive canonical rule branches.
- Nested element-bearing leaves are alternatives and inherit ancestor
  requirements; local `all_of`/`any_of` structure is retained.
- Provisions without an executable element-bearing branch are
  `definition_only` and fail closed instead of succeeding by vacuous truth.
- Results retain subsection citation paths and per-element traces.
- Primitive and typed facts are accepted. Typed facts preserve source/date/
  jurisdiction/evidential/burden metadata. Supplied burden metadata must match
  an element declaration, but primitive Booleans retain compatibility behavior.
- Registered, acyclic `is_infringed` dependencies use the caller’s statute
  registry and fact context. Missing targets, cycles, or unsupported overrides
  become unresolved diagnostics rather than silently false guards.
- Guarded sibling penalties are selected from satisfied branches. Unguarded
  and same-guard blocks are cumulative. Distinct simultaneously true guards
  are retained with `YRTP001` rather than resolved by declaration order.
- Limited case-law annotations can alter targeted fact-level elements. This is
  not a general precedent engine.
- Money uses `Decimal` with currency-aware rounding checks. Exact month/year
  duration ordering needs a reference date.

### Newly added but incomplete typed outcomes

Commit `b5f37d9e` added outcome kinds (`not_proved`, `acquitted`, `reduced_to`,
`convicted`, `special_disposition`, `unresolved`), source/target/diagnostic
types, Canonical IR v1.2 transitions, runtime reduction/disposition resolution,
and grammar source forms such as `outcome acquit`, `outcome reduce_to s304`,
and guarded dispositions.

Treat this work as incomplete:

- issue #51 remains open and has no completion comment;
- no checked-in `.yh` corpus file uses an `outcome` declaration;
- generated `src/parser.c` and `src/node-types.json` contain no
  `outcome_block`, so production parser artifacts are behind `grammar.js`;
- the conformance matrix lacks the two new outcome grammar rules and CI fails;
- no dedicated outcome tests were found;
- Z3, Alloy, and Lean mark criminal outcomes unsupported;
- core architecture/status/evidence docs still identify Canonical IR as v1.1.

This is a partially landed design, not a completed user-facing feature.

## User-facing workflows

The installed entry points are `yuho` and `yuho-lsp`. The recommended checkout
installer requires exact `uv 0.11.14`, synchronizes the committed `uv.lock`,
and defaults to Python 3.13 in `.venv`.

The CLI exposes:

| Command | Purpose |
|---|---|
| `doctor` | Check parser/package/tool readiness |
| `init` | Create starter projects from four templates |
| `check` | Parse/validate, optionally syntax-only, watch, JSON/SARIF, or experimental civil feature |
| `lint` | Statute-core/fidelity rules, transcription or executable posture, optional fixes |
| `fmt` | Format or check formatting |
| `ast` | Display AST and statistics |
| `test` | Execute embedded Yuho assertions with optional coverage/JUnit |
| `explain` | Evaluate and explain a section against facts |
| `debug` | Element-level evaluation debugging |
| `irac` | Emit Issue/Rule/Application/Conclusion-style English |
| `literate` | Align legal text and encoded elements into Markdown/HTML |
| `refs` | Query statute/case-treatment graphs, cycles, SCCs, and transitive edges |
| `diff` | Compare files or selected sections across jurisdictions |
| `transpile` | Emit registered exports and optional provenance sidecars |
| `schema` | Emit the JSON output schema |
| `verify` | Use `combined`, `z3`, or `alloy`, or display capabilities |
| `ci-report` | Validate a tree and emit one JSON/SARIF report |
| `upgrade` | Rewrite/check grammar-version migrations |
| `completion` | Generate Bash, Zsh, or Fish completion |

Documentation drift exists: `library/README.md` shows a nonexistent
`yuho library search` command, and some examples use older `explain` argument
forms. The generated `docs/user/cli-reference.md` is the stronger reference.

The LSP publishes parse/AST/semantic/lint diagnostics on open/change/save and
supports hover, same/imported/corpus section definitions, keyword completion,
references, semantic tokens, and a check code action. The VS Code extension
launches `yuho-lsp`, registers `.yh`, and includes TextMate fallback syntax
highlighting.

## Corpora and legal-data evidence

### Corpus inventory

| Corpus | Raw sections | Encoded `statute.yh` | Nature and limitation |
|---|---:|---:|---|
| Singapore Penal Code 1871 | 524, scraped 2026-04-24 | 524 | Principal structural corpus; metadata, 141 `test_statute.yh` files, ledgers, review history |
| Bharatiya Nyaya Sanhita 2023 | 358 | 358 | Generated skeletons preserving raw text in definitions; doctrinal elements await manual encoding |
| Indian Penal Code 1860 | 493 | 8 | Representative subset: ss300, 302, 375, 376, 378, 420, 497, 509 |
| Malaysia Penal Code Act 574 | 541 | 20 | IPC-lineage proof-of-concept/skeleton using a 2023-07-04 official PDF snapshot |
| Pakistan Penal Code 1860 | 617 | 20 | Proof-of-concept/skeleton; a UNODC 2017 snapshot was used after the official PDF was unreachable |
| Contracts (Rights of Third Parties) | n/a | 1 | Experimental civil-feature example |
| Problem questions | n/a | 10 exercise files | Fact/application exercises, not an Act corpus |

`library/_index/` also has a 500-record Singapore Statutes Online Act index and
a 358-row IPC/BNS mapping.

### Singapore Penal Code claim boundary

The coverage ledger says 524/524 sections have L1 parse, L2 build/lint, and a
legacy L3 stamp. “L3” is historical metadata, not proof of legal correctness or
universal human review. The authoritative capability registry breaks the 524
records down as:

- 377 automated-triage records;
- 123 explicitly labelled human-review records;
- 24 unattributed team records.

The archived L3 triage file separately contains 126 flagged records: 124
`INVESTIGATE` and 2 `FIX_NEEDED`. It records historical concerns and must not
be confused with the 524-record attribution breakdown.

The current provenance ledger verifies checked-in raw-section and `.yh` hashes.
It does **not** establish that the snapshot is current official text, that an
encoding preserves the intended law, or that a qualified independent reviewer
approved it. The target evidence schema calls for digest-addressed authoritative
raw bytes, deterministic normalization, source-span/IR links, compiler/grammar/
IR hashes, named review decisions, and invalidation after input changes. Issues
#46 and #47 track this missing chain.

### Quantitative signs of semantic gaps

A scan of the 524 Singapore statute files found:

- 123 files containing subsections;
- 81 files containing guarded penalties;
- 147 files using `is_infringed(...)`;
- 32 files using `caused_by`;
- 11 files declaring burden metadata;
- 3 files containing case-law blocks;
- 0 files containing executable `temporal` constraints;
- 0 files containing the new `outcome` declarations.

These counts explain why parsing coverage is much stronger than full legal
execution coverage. Known substantive corpus defects include an incorrect
conjunctive model and invented penalty in s299, flattened/incorrect sentencing
branches in ss302/304, inert causal labels, and a private-defence family that
cannot express its connected temporal and cross-section doctrine.

## Verification, formal methods, and trust boundary

### Retained checks

The `Makefile` and scripts define gates for:

- all-524 parse/lint coverage;
- Akoma Ntoso round-trip against vendored OASIS XSDs;
- runtime sweeps and runtime/Z3 differential comparisons;
- penalty verdict/bound comparisons and source-map coverage;
- DSL/conformance and backend-capability matrices;
- action SHA pins, corpus provenance, and capability-claim consistency;
- literate alignment;
- Lean/Python structural diff, expected verdicts, penalty footprints, and Lean
  builds where the toolchain is available;
- reproducible Python artifacts and release audit;
- Mermaid rendering and full-corpus variants on demand.

These checks provide consistency evidence, not proof that encoded rules are
legally correct.

### Lean

`mechanisation/` pins Lean 4.10.0 and documents a v9 abstract artefact with no
`sorry`s. It includes element and nested element-graph evaluation, exceptions,
cross-section/`apply_scope` models with acyclicity conditions, penalty
footprints/combinators, canonical abstract SMT constructors, typed burden
metadata, a bounded executable case-law fragment, and extensive smoke theorems.

Its trusted base includes Lean’s kernel/stdlib assumptions, the Python AST/Z3
encoder, fixture generation, and corpus selection. Production Canonical IR is
marked unsupported by the Lean capability matrix. There is no end-to-end
refinement proof from parsed production source through the Python runtime to
Lean semantics; #45 tracks a bounded version of that work.

### Backend boundaries

- Z3 is a conformance-tested primary solver for a bounded fragment. It rejects
  subsection branches, conditional/multiple penalties, case-law semantics,
  typed burdens, criminal outcomes, unresolved/cyclic dependencies, and
  fact-override dependency calls where unsupported.
- Alloy is explicitly only a secondary bounded-shape smoke backend. It is not
  semantic parity evidence.
- Legal interchange/export schemas validate shape, not truth or meaning.

### Claims the repository itself prohibits

Do not claim end-to-end legal correctness, formal verification of the entire
language/corpus, universal human review, semantic equivalence merely because an
export validates, legal advice, or a hosted decision service.

The root README currently violates that caution by opening with “Yuho is a
formally verified ... domain-specific language.” Issue #43 exists to align that
wording with the capability registry.

## Current `main` health and material drift

The latest `Yuho CI/CD on push` run for `b5f37d9e` failed. Current evidence is
more informative than older passing comments on closed issues:

- Python 3.11/3.12/3.13: 11,978 passed, 2,634 skipped, 5 failed. Failures were
  three disk-cache tests, the README backend-parity wording contract, and two
  outcome grammar rules missing from the construct conformance matrix.
- Python 3.10: collection stopped with two errors because corpus scripts import
  stdlib `tomllib`, introduced in Python 3.11, despite declared Python 3.10
  support and installed `tomli`.
- Black failed on many source files; mypy and generated CLI-doc checks were
  consequently skipped.
- The Akoma Ntoso 524/524 XSD round-trip job passed.
- The generated-grammar job was cancelled during verification. Static
  inspection confirms `grammar.js` has outcome rules while checked-in
  `parser.c`/`node-types.json` do not.
- The clean release gate failed while setting up Lean, so its audit did not run.
- The latest security workflow failed because locked `lxml 5.4.0` was reported
  under `PYSEC-2026-87` with fix version 6.1.0. OpenSSF Scorecard separately
  failed while pulling its GCR image due an upstream billing-denied response.
  CodeQL passed.
- GitHub reports `main` as unprotected and the repository has no rulesets,
  directly confirming #42.

Other important drift:

- Package/release version is 5.1.0 while the Tree-sitter package is 0.1.0;
  these are separate artifacts but easy to confuse.
- Source Canonical IR is v1.2; four core docs still say v1.1.
- README advertises the project more strongly than the evidence registry allows.
- No current successful full release-gate run exists after the latest changes.
- The Dockerfile pins uv/Python image digests and records inputs, but #41
  correctly says this is not proof that isolated builds match or the image
  currently builds.

## GitHub issue inventory

### Closed issues

1. [#1 — LSP support for Yuho](https://github.com/gongahkia/yuho/issues/1)
   (closed 2024-09-06). Originally requested more checks and VS Code support.
   It was explicitly shelved because scope mattered more at the time, not
   closed with an implementation report. The repository later acquired a
   Python LSP and VS Code extension, so present code exceeds the historical
   issue state.

2. [#44 — Implement the versioned canonical IR pipeline and explicit capability diagnostics](https://github.com/gongahkia/yuho/issues/44)
   (closed 2026-09-04). Added deterministic Canonical IR v1.0, hashes,
   provision/requirement/penalty IR, canonical entry points, and consumer
   capability boundaries. The completion comment reported 45 focused tests,
   all 524 statutes lowering, and a full run with one unrelated README failure.
   Later commits advanced source IR to v1.2; docs/current CI no longer fully
   align with that closed snapshot.

3. [#48 — P0: evaluate nested subsection elements in the runtime](https://github.com/gongahkia/yuho/issues/48)
   (closed 2026-09-04). Fixed the soundness bug where 104 statutes with only
   nested elements could appear satisfied on empty facts. Runtime now evaluates
   recursive branches, preserves paths, and classifies empty provisions as
   definition-only. Z3 rejects nested branches instead of flattening them.

4. [#49 — Correct runtime selection of conditional and sibling penalty blocks](https://github.com/gongahkia/yuho/issues/49)
   (closed 2026-09-04). Runtime now selects all applicable branch-governed
   penalties, fixes s304A rash/negligent selection, preserves source/combinator
   shape, and diagnoses conflicting sibling guards with `YRTP001`. Z3 rejects
   unsupported multi/conditional-penalty input.

5. [#50 — Resolve cross-section exception guards in the registered rule environment](https://github.com/gongahkia/yuho/issues/50)
   (closed 2026-09-04). Added canonical dependency edges and same-fact-context
   runtime resolution for `is_infringed`; missing references, cycles, and
   unsupported calls are explicit. Supported acyclic same-fact dependencies
   have Z3 coverage; Alloy and Lean production-IR support remains rejected.

### Open release, governance, and trust issues

1. [#39 — P0: fix and prove comment-before-typed-struct-literal parsing](https://github.com/gongahkia/yuho/issues/39).
   A non-doc comment before `Foo value := Foo { ... }` can make the generated
   parser split the initializer and silently change meaning. Diagnostic `Y0103`
   is a temporary fail-safe. The fix requires controlled Tree-sitter 0.22.6
   regeneration, artifact validation, CST/AST/runtime regressions, and only
   then narrowing the mitigation.

2. [#40 — Run the full release gate in a resource-safe environment](https://github.com/gongahkia/yuho/issues/40).
   The post-hardening suite and `release_audit.py --full` have not completed.
   It calls for serial, logged corpus, Lean, source-map, AKN, runtime, security,
   and generated-grammar checks after memory pressure is controlled.

3. [#41 — Prove Docker and isolated double-build reproducibility](https://github.com/gongahkia/yuho/issues/41).
   Locked inputs/digest reporting exist, but a clean two-build comparison and
   real Docker build/container smoke have not been run for current changes.

4. [#42 — Enforce the release gate with a protected main ruleset](https://github.com/gongahkia/yuho/issues/42).
   Requires PRs, approval, resolved conversations, current branches, force-push
   and deletion blocking, and documented required checks. The GitHub API
   currently confirms no protection and no rulesets.

5. [#43 — Align README assurance and product wording with the capability registry](https://github.com/gongahkia/yuho/issues/43).
   Requires a maintainer-approved minimal README change removing blanket
   formal-verification/review/legal-correctness implications and accurately
   describing parser, review, and formal-method limits. This also causes a
   current test failure.

6. [#45 — Prove runtime refinement for a bounded canonical-IR fragment](https://github.com/gongahkia/yuho/issues/45).
   Depends on #44. It seeks a named subset, Lean reference interpreter,
   exclusions, runtime/refinement checks, and backend translation obligations;
   it explicitly cannot establish legal correctness.

7. [#46 — Materialize immutable corpus source and provenance evidence records](https://github.com/gongahkia/yuho/issues/46).
   Depends on #44. It requires authoritative raw-byte snapshots, normalization
   hashes, source-span/IR links, compiler/grammar hashes, schema validation,
   and review invalidation after changes.

8. [#47 — Establish named human and independent corpus-review approvals](https://github.com/gongahkia/yuho/issues/47).
   Requires reviewer qualifications, a rubric, named/timestamped hash-bound
   decisions, conflict/independence policy, and independent approval for
   high-risk material. Automated/unattributed history must not be upgraded.

### Open core legal-semantics issues

9. [#51 — Represent criminal outcomes and dispositions instead of Boolean exception effects](https://github.com/gongahkia/yuho/issues/51).
   Results must distinguish `not_proved`, `acquitted`, `reduced_to`, `convicted`,
   and `special_disposition`, preserve whether the act was found, route special
   murder exceptions to s304, and support the s84/CPC path. Source contains an
   incomplete partial implementation described earlier.

10. [#52 — Repair the executable model of Penal Code section 299 culpable homicide](https://github.com/gongahkia/yuho/issues/52).
    Current s299 incorrectly requires all three mental-state limbs and includes
    an invented standalone penalty. It should require act/result plus one of
    three fault alternatives, defer causal execution to #54, remove the
    penalty, and route charging/sentencing through #51.

11. [#53 — Correct limb-specific sentences for Penal Code sections 302 and 304](https://github.com/gongahkia/yuho/issues/53).
    Current generic numeric ranges erase distinct statutory branches and
    mandatory/optional/alternative/cumulative consequences. Depends on #49
    penalty execution and #51 outcome routing.

12. [#54 — Make causal links executable rather than `caused_by` metadata](https://github.com/gongahkia/yuho/issues/54).
    Calls for typed source/result events, a named causal test, proof status,
    unresolved/disproved traces, migration diagnostics, and initial coverage
    of s299, s304A, and an injury provision.

13. [#55 — Make temporal relationships and concurrence executable](https://github.com/gongahkia/yuho/issues/55).
    Temporal syntax is ignored by runtime and Z3 ordering variables are not
    bound to evidence events. It needs named timepoints/intervals and shared
    `precedes`/`during`/`after` semantics for concurrence and defence timing.

14. [#56 — Add structured criminal fault-state primitives](https://github.com/gongahkia/yuho/issues/56).
    Replace Boolean `mens_rea` labels with actor/target/mode/standard values for
    intent, knowledge, wilful blindness, rashness, negligence, strict liability,
    and reasonable-care qualifications. Coordinate proof status with #62 and
    an MDA fixture from #64.

15. [#57 — Model voluntary conduct, duty-based omissions, and automatism](https://github.com/gongahkia/yuho/issues/57).
    Add actor-bound positive conduct and omissions with legal duty,
    opportunity/capacity, omitted act, and involuntariness rather than generic
    physical-element labels.

16. [#58 — Add agents, roles, relationships, and cardinality for participation liability](https://github.com/gongahkia/yuho/issues/58).
    Add named actors/victims/events, participation relationships, shared
    intention/object, and bounded counts for ss34, 107, 120A, 141/149, and 391.
    A person must not inherit another person’s Boolean fact.

17. [#59 — Model attempts as target-offence relations rather than Boolean labels](https://github.com/gongahkia/yuho/issues/59).
    Bind actor, target offence, qualifying conduct, threshold authority, and
    non-completion. Tests should distinguish preparation, attempt, and completed
    offence for s511 and a specific attempt offence.

18. [#60 — Add context-sensitive consent, capacity, and vitiating-factor semantics](https://github.com/gongahkia/yuho/issues/60).
    Consent must be person-, act-, and context-specific and separately trace
    capacity/age, fear, misconception, and statutory overrides. General-
    exception and sexual-offence consent cannot be one global Boolean.

19. [#61 — Encode the private-defence rule family as connected executable rules](https://github.com/gongahkia/yuho/issues/61).
    Rebuild ss96–106A as a source-cited dependency/temporal/participant/outcome
    graph. It must distinguish body/property branches, commencement/cessation,
    and limiting conditions rather than accept an umbrella fact.

20. [#62 — Add proof-status, burden, and rebuttable-presumption semantics](https://github.com/gongahkia/yuho/issues/62).
    Add `proved`, `not_proved`, `presumed`, `rebutted`, and `unresolved` states,
    party/standard/source attribution, and trigger/rebuttal transitions. The
    project explicitly rejects invented probability thresholds for reasonable
    doubt. Runtime and Z3 must agree on a subset or reject it explicitly.

### Open package, corpus-expansion, case-law, and jurisdiction issues

21. [#63 — Add versioned multi-Act packages and qualified cross-Act references](https://github.com/gongahkia/yuho/issues/63).
    Add Act/package manifests with jurisdiction, source URL, effective version/
    date, hashes, deterministic version selection, qualified references, and
    package/version provenance in traces. This is the foundation for Evidence
    Act, MDA, CPC, and Road Traffic Act work.

22. [#64 — Add a reviewed Misuse of Drugs Act core corpus](https://github.com/gongahkia/yuho/issues/64).
    Create a versioned, reviewed `MDA1973` subset for ss5, 12, 17–18, and 33B.
    Section 18’s possession and knowledge presumptions must have distinct
    triggers/rebuttals, and s33B must expose cited eligibility/disposition
    branches. Depends on #63, #62, #56, and #51.

23. [#65 — Add an Evidence Act burden and presumption corpus slice](https://github.com/gongahkia/yuho/issues/65).
    Create a reviewed `EA1893` subset for ss103–108 and directly needed
    presumptions. It must connect s107 to Penal Code exceptions without
    overwriting the prosecution’s offence-element burden. Depends on #63/#62.

24. [#66 — Add the CPC ss247–252 unsoundness-of-mind disposition slice](https://github.com/gongahkia/yuho/issues/66).
    Create `CPC2010` rules for competency/unsoundness inquiry, required findings,
    and post-s84 safe-custody disposition. Results must distinguish acquittal,
    act-found status, and procedural order from an ordinary penalty. Depends on
    #63/#51.

25. [#67 — Add a current Road Traffic Act dangerous-driving/death corpus slice](https://github.com/gongahkia/yuho/issues/67).
    First resolve current official section numbering/version because an audited
    note may confuse ss64 and 66. Then model dangerous driving and causing death
    separately with causation and supported alternative outcomes. Depends on
    #63, #54, #56, #49, and #51.

26. [#68 — Make cited case-law propositions executable, scoped, and reviewable](https://github.com/gongahkia/yuho/issues/68).
    Add versioned reviewed case rules with court, citation, date, source,
    proposition/test, statutory/factual scope, and treatment. Parser/IR/runtime
    need a defined subset; unsupported backends must reject it. This must not
    convert every note citation into a universal binding Boolean. Coordinate
    provenance/review with #46/#47.

27. [#69 — Make territorial and extraterritorial applicability executable](https://github.com/gongahkia/yuho/issues/69).
    Add event location, actor status, statutory nexus, and hypothetical
    equivalent-offence relationships for Penal Code ss2–4B and provisions such
    as s376C/s377BO. Package jurisdiction metadata alone cannot establish
    applicability. Depends on #55, #58, and #63.

## How the open work fits together

The issues form a dependency program, not 27 independent enhancements:

```text
restore a trustworthy build/release boundary
  #39 generated parser -> #40 full gate -> #41 reproducibility -> #42 protection
                       \-> #43 honest public wording

stabilize the semantic result and evidence model
  #44 canonical IR (closed) -> #45 refinement proof
                            -> #46 provenance -> #47 review governance
                            -> #51 typed outcomes

add missing criminal-law primitives
  #54 causation + #55 time + #56 fault + #57 conduct
  + #58 participants + #60 consent + #62 proof state
       -> #52/#53 homicide repairs
       -> #59 attempts
       -> #61 private defence
       -> #69 jurisdiction

add versioned legal packages
  #63 packages + core primitives
       -> #64 MDA
       -> #65 Evidence Act
       -> #66 CPC
       -> #67 Road Traffic Act
       -> #68 reviewed case-law modules
```

A coherent priority order is:

1. Restore build truth: finish/integrate or revert the partial #51 landing,
   resolve #39, repair CI/conformance/docs/Python 3.10/security failures, then
   run #40 serially.
2. Correct public trust: #43, #41, and #42 before treating another tag as a
   reliable promotion boundary.
3. Complete the semantic foundations: #51, #54–#58, #60, #62, and #63.
4. Repair high-risk existing doctrine: #52, #53, and #61.
5. Add external Act slices and jurisdiction/case-law work: #64–#69.
6. Build the stronger evidence story: #45–#47 alongside the semantics they
   are meant to attest.

The key architectural rule should remain: define the Canonical IR semantics and
unsupported boundaries before expanding syntax or corpora. The latest outcome
commit demonstrates what happens when grammar, generated parser, conformance
matrix, docs, tests, and corpus adoption do not land atomically.

## Practical interpretation

### What is useful today

Yuho is already useful for authoring and structurally reviewing `.yh` files,
parsing and linting the checked-in corpora, navigating statute/reference graphs,
inspecting AST and Canonical IR output, rendering several documentary and visual
formats, and experimenting with the bounded rule subset that the runtime and Z3
explicitly support. The 524-section Singapore corpus is also a meaningful
research dataset when its provenance and review qualifications are retained.

### What should not be relied on today

Do not use current Yuho output as a legal conclusion, assume every accepted
construct is executable, equate generated-schema validity with semantic
equivalence, or infer legal fidelity from parse/build coverage. Do not publish a
new release from the inspected commit until the red build and partial outcome
landing are reconciled. Treat the BNS, Malaysia, and Pakistan corpora primarily
as structural/skeleton material, not reviewed executable doctrine.

### Recommended product direction

The best near-term direction is to stabilize and deepen the existing semantic
core before adding more syntax or bulk corpora. Specifically, restore one
truthful green release boundary, make typed outcomes and proof status the shared
result vocabulary, then add participant/event/time/causation/fault primitives
through Canonical IR. After that, use a small reviewed cross-Act scenario—such
as Penal Code s84 plus the CPC disposition path—as the vertical proof that
packages, provenance, runtime traces, and assurance boundaries compose.

This recommendation is an engineering/product judgment derived from the
repository evidence, not an existing maintainer decision.

## Repository map for follow-up investigation

| Path | Why it matters |
|---|---|
| `pyproject.toml`, `uv.lock`, `Makefile` | Package contract, pinned environment, and authoritative task entry points |
| `src/tree-sitter-yuho/` | Grammar source, generated parser artifacts, queries, and language bindings |
| `src/yuho/ast.py`, `parser.py`, `analysis.py` | CST-to-AST construction and shared analysis pipeline |
| `src/yuho/ir/` | Canonical IR schema, lowering, hashes, capability matrix, and outcome model |
| `src/yuho/eval/` | Runtime rule, dependency, penalty, case-law, and outcome evaluation |
| `src/yuho/verify/` | Z3 and Alloy adapters plus explicit support boundaries |
| `src/yuho/transpile/` | Human, diagram, document, and legal-interchange exporters |
| `src/yuho/cli.py`, `lsp.py` | User-facing CLI and language-server behavior |
| `library/` | Statute corpora, raw sources, indexes, ledgers, and problem questions |
| `mechanisation/` | Lean project, abstract semantics, theorems, and fixtures |
| `tests/` | Unit, integration, snapshot, conformance, corpus, and regression evidence |
| `scripts/` | Corpus builders, provenance/release checks, generated artifacts, and audits |
| `docs/architecture/`, `docs/positioning/` | Intended design, status, and known claim boundaries |
| `docs/release/` | Capability registry and retained evidence; stronger than marketing prose |
| `.github/workflows/` | CI, release, security, CodeQL, Scorecard, and corpus jobs |
| `editors/vscode/` | VS Code language support |

## Questions worth taking into a ChatGPT discussion

1. Should Yuho present itself first as a legal-language research platform, a
   compiler/toolkit, or a reviewed corpus project? Its current breadth obscures
   which success criterion takes priority.
2. Should the incomplete outcome work on `main` be finished immediately or
   temporarily reverted to restore a clean release boundary?
3. What is the smallest Canonical IR fragment whose Python runtime semantics can
   realistically be related to Lean, without implying whole-system legal
   correctness?
4. What fact/evidence model can unify actors, events, time, causation, fault,
   burdens, presumptions, and outcomes without turning each doctrine into an
   unrelated special case?
5. Which corpus tier should be called “reviewed,” and what immutable source and
   named approval evidence is required for that label?
6. Should corpus expansion pause until one cross-Act criminal-law path works
   end to end with qualified references, traceable evidence, and explicit
   backend rejection where unsupported?
7. Which current outputs are products versus research artifacts, and which CI
   checks must protect each promise?
8. How should the README explain the Lean/Z3 work accurately while preserving
   the project’s genuinely strong formal-methods contribution?

## Suggested prompt to accompany this document

> Treat the attached Yuho handoff as the repository snapshot at commit
> `b5f37d9e` on 2026-09-12. Help me reason about product direction,
> architecture, issue prioritization, and assurance boundaries. Distinguish
> checked-in/current behavior from aspirations, do not equate parser coverage
> with legal correctness, and explicitly identify assumptions. When proposing
> work, map it to the issue dependencies and prefer one coherent vertical slice
> over disconnected feature growth.

## Investigation limitations

- This review is a source, artifact, issue, and current-CI audit; it is not an
  independent legal review of the encoded statutes.
- No local full-suite, Docker, Tree-sitter regeneration, Lean build, or full
  release audit was completed during this handoff because an earlier local
  verification attempt caused workstation memory pressure. Those checks remain
  skipped, not passed.
- GitHub state is a time-stamped snapshot. Issues, Actions results, releases,
  dependencies, and branch rules can change after 2026-09-12.
- The document deliberately preserves contradictions and incomplete features
  instead of resolving them, because its purpose is accurate handoff context.
