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
  - Local evidence: `StatuteEvaluator.apply_scope()` says embedded `ApplyScopeNode` refs inside expression contexts are not yet semantically interpreted by the element-graph executor.
- Syntax conventional: valid, but low priority.
  - Local evidence: grammar is conventional statically typed DSL syntax with legal blocks.
  - Marking: [Inference] Esolang experts may not care; PL/DSL experts will care more about semantics, tooling, and conformance.

## P0: Canonical Semantics

- Define one canonical Yuho semantics document and make every implementation layer point to it.
  - Add `docs/researcher/canonical-semantics.md`.
  - Cover every surface construct in `src/tree-sitter-yuho/grammar.js`.
  - For each construct, specify parse node, AST node, type rule, runtime rule, Z3 rule, Alloy rule, Lean model status, transpiler obligations.
  - Add a machine-readable construct matrix under `tests/fixtures/conformance/constructs.json`.
  - Acceptance: CI fails when a construct is parsed but has no semantic/backend coverage row.

- Make runtime, Z3, Alloy, and Lean agree on shared fixtures.
  - Add fixture categories: flat elements, nested `all_of`, nested `any_of`, mixed groups, exceptions, `defeats`, `is_infringed`, `apply_scope`, penalties, money/duration, optional values.
  - Add differential tests: runtime verdict == Z3 model verdict == Lean expected verdict where available.
  - Acceptance: `make verify-core` includes a backend parity summary, with unsupported backend features explicit.

## P0: Rich Fact Model

- Replace bare truthy-fact matching with typed fact declarations.
  - Add a first-class `facts` schema DSL or documented JSON Schema.
  - Model type, source, date, jurisdiction, evidential status, burden, standard of proof, and confidence/provenance metadata.
  - Keep boolean facts as a compatibility shorthand, not the canonical model.
  - Acceptance: `yuho explain` can say why a fact satisfies an element and what evidence/proof standard it used.

- Add predicate-backed element satisfaction.
  - Permit elements to bind to computable predicates, not only matching field names.
  - Example shape to design, not final syntax: `actus_reus deception when facts.representation.falsehood && facts.accused.knows_falsehood`.
  - Acceptance: element truth can depend on structured fields, comparisons, dates, amounts, parties, and nested records.

## P0: Machine-Readable Legal Meaning

- Split human text from executable meaning.
  - Keep `description` for human-readable drafting.
  - Add required or warning-backed `condition`/`predicate`/`requires` bodies for executable elements.
  - Add lint level: string-only element is allowed for transcription mode but warned in executable mode.
  - Acceptance: `yuho lint --mode executable` reports every element/definition/case holding that is only opaque text.

- Make definitions computable when possible.
  - Support definitional predicates and term expansion.
  - Track aliases, imported definitions, and section-local overrides.
  - Acceptance: a definition can be referenced by multiple elements and tested independently.

## P0: Case Law And Doctrine

- Promote case law from metadata to semantics.
  - Model holding, ratio/obiter marker, jurisdiction/court level, date, treatment, element target, and interpretive effect.
  - Encode treatment types: follows, distinguishes, overrules, reverses, approves, disapproves, applies.
  - Add priority rules over cases and statutes where jurisdiction permits.
  - Acceptance: case-law blocks can alter, narrow, expand, or annotate element predicates in a testable way.

- Add precedent-aware explanation.
  - `yuho explain` should show which case-law rule affected the result.
  - `yuho refs` should expose statute-to-case and case-to-case treatment graph.
  - Acceptance: one fixture demonstrates overruled/distinguished case law changing the outcome.

## P1: Cross-Section Scope Composition

- Complete embedded `apply_scope` and `is_infringed` runtime semantics.
  - Implement expression-context evaluation in the runtime element graph.
  - Add registry resolution, fuel/depth bounds, cycle diagnostics, and fact substitution semantics.
  - Acceptance: runtime evaluator, Z3, and Lean smoke fixtures agree on nested cross-section references.

- Add section-call typing.
  - Define section input/output types.
  - Reject calls with missing facts or incompatible substituted fact schemas.
  - Acceptance: semantic analysis catches invalid `apply_scope` calls before runtime.

## P1: Formal Mechanisation

- Close the known Lean proof gaps incrementally.
  - Add binder infrastructure for scoped names.
  - Add certified reconstruction path or explicitly document solver trust.
  - Add richer doctrine/case-law semantics once runtime semantics exists.
  - Acceptance: `mechanisation/README.md` separates proved, tested, trusted, and out-of-scope claims in a table.

- Expand beyond smoke fixtures.
  - Generate representative Lean fixtures from corpus strata: simple, nested, exception-heavy, cross-ref-heavy, penalty-heavy.
  - Acceptance: mechanisation CI reports coverage by feature, not only by named sections.

## P1: Type System And Numeric Semantics

- Make money/date/duration precise.
  - Define currency, rounding, units, intervals, and calendar arithmetic.
  - Remove or heavily label 30-day/month and 365-day/year approximations.
  - Acceptance: money/duration tests cover edge cases and docs no longer overstate precision.

- Finish or narrow generics.
  - Either implement generic checking/runtime representation or mark generics as surface-only/experimental.
  - Acceptance: no docs claim full static generic checking unless tests prove it.

- Align docs with implementation.
  - Audit `docs/researcher/syntax.md` and `docs/researcher/formal-semantics.md` against parser/type-checker/evaluator.
  - Acceptance: every documented feature has a smoke parse test and at least one semantic/lint/transpile test where applicable.

## P1: Lawyer-Facing And Researcher UX

- Add literate statute mapping.
  - Support source text alongside Yuho clauses, with line/paragraph anchors.
  - Show one-to-one mapping from statutory paragraph to executable element.
  - Acceptance: HTML/Markdown report shows legal text, Yuho code, result trace, and source maps side by side.

- Add controlled-authoring mode.
  - Inspired by L4/Blawx/Catala UX, provide constrained templates for non-compiler users.
  - Acceptance: `yuho init --template statute-literate` creates a starter with legal text anchors and executable predicates.

## Non-Goals For Now

- Do not optimize syntax novelty for esolang appeal.
- Do not add more export formats before backend parity improves.
- Do not claim end-to-end legal correctness; claim parsed, checked, transpiled, evaluated, or verified only for the covered fragment.
