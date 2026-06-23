# Yuho DSL Hardening TODO

Generated: 2026-06-23

Scope: strengthen Yuho as a serious computational-law DSL. This is not a feature wishlist; every item below maps to an audit gap found locally and cross-checked against external rules-as-code/legal-DSL references.

## External Baselines Checked

- Catala: statutory-law DSL with one-to-one statute mapping and prioritized default logic.
  - https://github.com/CatalaLang/catala
  - https://arxiv.org/pdf/2103.03198
- L4: legal DSL/CNL tooling with compiler, IDE, LSP, REPL, web editor, decision service, and priority/meta-rule focus.
  - https://github.com/smucclaw/l4-ide
  - https://l4-documentation.readthedocs.io/en/latest/docs/returning-L4-and-law.html
- OpenFisca: rules-as-code platform for computable legislation and open APIs.
  - https://openfisca.org/en/
  - https://openfisca.org/doc/openfisca-web-api/index.html
- Blawx: web-based declarative logic rules-as-code tool with testing/explanation focus.
  - https://github.com/Lexpedite/blawx
  - https://law.mit.edu/pub/blawxrulesascodedemonstration
- Akoma Ntoso: OASIS legal document/interchange standard.
  - https://www.oasis-open.org/standard/akn-v1-0/
- LegalRuleML: OASIS standard for legal normative rules.
  - https://www.oasis-open.org/standard/legalruleml-core-specification-version-1-0-oasis-standard/
- Z3: SMT solver used in verification/program analysis.
  - https://www.microsoft.com/en-us/research/publication/z3-an-efficient-smt-solver/
  - https://microsoft.github.io/z3guide/docs/logic/intro/
- Alloy: relational modeling language/analyzer using bounded analysis.
  - https://alloytools.org/alloy6.html
  - https://groups.csail.mit.edu/sdg/pubs/2015/icse15-alloystar.pdf

## Audit Validation

- Shallow executable facts: valid.
  - Local evidence: `src/yuho/eval/statute_evaluator.py` says each element is satisfied by a matching fact field whose value is truthy.
  - External pressure: OpenFisca and Blawx expose computable rule/fact models and APIs, not only boolean smoke fixtures.
- Legal meaning left in strings: valid.
  - Local evidence: element descriptions, definitions, holdings, and many case-law details are string payloads in AST/transpilers.
  - External pressure: Catala emphasizes close executable correspondence to legal paragraphs; LegalRuleML exists specifically to model legal normative rule particularities.
- Case-law semantics shallow: valid.
  - Local evidence: `visit_caselaw()` returns `Value(None, "none")`; case law is mostly parsed/transpiled/diffed.
  - Local confirmation: `mechanisation/README.md` lists richer doctrine, precedent-sensitive interpretation, and procedural burdens as outside the current proof.
- Formal semantics/implementation gap: valid.
  - Local evidence: `docs/researcher/formal-semantics.md` explicitly lists approximate money/duration arithmetic, erased generics, explicit null checks, and a post-type-checking defeasible layer.
- Backend drift risk: valid.
  - Local evidence: multiple independent emitters/backends exist: runtime evaluator, JSON, English, LaTeX, Mermaid, Mindmap, Alloy, LegalRuleML, Akoma Ntoso, Z3, Lean fixtures.
  - External pressure: Z3/Alloy are serious but the encoder is the trust boundary.
- Alloy weaker than Z3/Lean: valid enough to track.
  - Local evidence: E2E tests skip when `AlloyGenerator` does not handle a case; Z3 has deeper element/group/exception/apply_scope tests.
  - Marking: [Inference] Treat Alloy as secondary until nested groups, exceptions, priority, penalties, and cross-section refs have parity tests.
- Cross-section reasoning incomplete: valid.
  - Local evidence: embedded `apply_scope`/`is_infringed` now execute in runtime and explain traces, but section input/output typing and Lean parity remain incomplete.
- Syntax conventional: valid, but low priority.
  - Local evidence: grammar is conventional statically typed DSL syntax with legal blocks.
  - Marking: [Inference] Esolang experts may not care; PL/DSL experts will care more about semantics, tooling, and conformance.

## P0: Canonical Semantics

- Make runtime, Z3, Alloy, and Lean agree on shared fixtures.
  - Current support: `make verify-core` includes a backend-parity summary with feature-category rows and explicit unsupported-feature boundaries; runtime/Z3 differential fixtures cover nested `all_of`/`any_of`, `apply_scope`, and scoped fact overrides.
  - Expand fixture categories: flat elements, nested `all_of`, nested `any_of`, mixed groups, exceptions, `defeats`, `is_infringed`, `apply_scope`, penalties, money/duration, optional values.
  - Add differential tests: runtime verdict == Z3 model verdict == Lean expected verdict where available.
  - Acceptance: runtime, Z3, and Lean fixture parity reports covered and unsupported feature categories explicitly; Alloy remains explicit-unsupported until it has parity coverage.

## P0: Machine-Readable Legal Meaning

- Expose computable definition source syntax and import semantics.
  - Runtime/explain can evaluate source-level computable definitions and reuse them across elements.
  - Current support: `definition_entry` accepts either prose strings or executable expressions.
  - Current support: direct named/wildcard imports expose statute `definitions` as computable terms, and local statute definitions override imported terms during evaluation.
  - Remaining work: alias syntax, transitive imported-definition dependencies, and diagnostics for duplicate imported definition terms.
  - Acceptance: a source `.yh` definition can be referenced by multiple elements and tested independently.

## P0: Case Law And Doctrine

- Promote case law from explanation annotations to executable semantics.
  - Current support: `yuho explain` annotates targeted elements with active case-law holdings and marks same-statute overruled authorities inactive.
  - Current support: `yuho explain` also marks same-statute distinguished, reversed, and disapproved authorities inactive for the current explanation.
  - Current support: `yuho refs --treatment` exposes case-to-case treatment edges.
  - Current support: case-law treatment syntax accepts follows/followed, distinguishes/distinguished, overrules/overruled, reverses/reversed, approves/approved, disapproves/disapproved, and applies/applied.
  - Model holding, ratio/obiter marker, jurisdiction/court level, date, treatment, element target, and interpretive effect.
  - Add priority rules over cases and statutes where jurisdiction permits.
  - Acceptance: case-law blocks can alter, narrow, or expand element predicates in a testable way.
  - Acceptance: one fixture demonstrates overruled/distinguished case law changing the outcome.

## P1: Cross-Section Scope Composition

- Harden embedded `apply_scope` and `is_infringed` runtime semantics.
  - Current support: predicate elements can resolve `apply_scope` and `is_infringed` through a registered statute environment in runtime and explain traces, nested section calls carry cycle and depth-limit diagnostics, and `apply_scope` struct args support ordered fact substitution.
  - Acceptance: runtime evaluator, Z3, and Lean smoke fixtures agree on nested cross-section references.

- Add section-call typing.
  - Current support: lint checks unresolved section calls, empty apply_scope targets, missing fields on struct-literal fact bases, unknown fields on struct-literal overrides, and obvious non-bool literal values for target element fields.
  - Current support: semantic analysis rejects structurally invalid `apply_scope` literal fact bases before runtime.
  - Remaining work: define named section input/output types beyond the current element-name bool schema.
  - Remaining work: infer identifier fact shapes across imports and reject incompatible substituted fact schemas that are not literal structs.
  - Acceptance: semantic analysis catches invalid literal `apply_scope` calls before runtime.

## P1: Formal Mechanisation

- Close the known Lean proof gaps incrementally.
  - Add binder infrastructure for scoped names.
  - Add richer doctrine/case-law semantics once runtime semantics exists.

- Expand beyond smoke fixtures.
  - Current support: `make verify-core` reports Lean mechanisation feature coverage and explicit out-of-scope areas.
  - Generate representative Lean fixtures from corpus strata: simple, nested, exception-heavy, cross-ref-heavy, penalty-heavy.
  - Acceptance: mechanisation CI reports coverage by feature, not only by named sections.

## P1: Type System And Numeric Semantics

- Add interval endpoint semantics and verifier calendar parity.
  - `..` range syntax is now documented and serialized as a closed interval with inclusive endpoints.
  - Money now uses Decimal, retained currency, and supported currency minor-unit validation.
  - Fixed day/hour/minute/second durations now compare exactly via `datetime.timedelta`.
  - Runtime calendar durations now compare exactly when a reference date is supplied, with month-end clamping.
  - Z3 verifier calendar-duration day counts are exact when `--reference-date YYYY-MM-DD` is supplied and explicitly labeled as 365-day/year and 30-day/month approximations otherwise.
  - Remaining work: exact calendar parity for non-Z3 verifier surfaces that still model duration as raw integer days.
  - Acceptance: no backend uses 30-day/month or 365-day/year approximation except explicitly labeled verifier summaries or no-reference-date Z3 mode.

- Align docs with implementation.
  - Current support: docs contract checks command coverage, advanced constructs, generic-support boundaries, and boolean literal spelling against parser behavior.
  - Audit `docs/researcher/syntax.md` and `docs/researcher/formal-semantics.md` against parser/type-checker/evaluator.
  - Acceptance: every documented feature has a smoke parse test and at least one semantic/lint/transpile test where applicable.

## P1: Lawyer-Facing And Researcher UX

- Expand literate statute mapping.
  - Current support: `yuho literate` emits Markdown/HTML reports with legal text, Yuho code, source anchors, executable element source spans, and optional result trace.
  - Remaining work: align statutory paragraphs to executable elements automatically when explicit anchors are absent.
  - Acceptance: report highlights each statutory paragraph next to its executable element and result trace.

- Expand controlled-authoring mode.
  - Current support: `yuho init` templates cover basic statute-only, statute-literate, statute-with-exceptions, and statute-with-cross-reference workflows.
  - Current support: `yuho init --guided` prompts for starter template, primary statute title, and smoke-check execution.
  - Remaining work: stricter authoring flows that validate each prompted legal element before writing files.

## Non-Goals For Now

- Do not optimize syntax novelty for esolang appeal.
- Do not add more export formats before backend parity improves.
- Do not claim end-to-end legal correctness; claim parsed, checked, transpiled, evaluated, or verified only for the covered fragment.
