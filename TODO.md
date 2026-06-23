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
- Syntax conventional: valid, but low priority.
  - Local evidence: grammar is conventional statically typed DSL syntax with legal blocks.
  - Marking: [Inference] Esolang experts may not care; PL/DSL experts will care more about semantics, tooling, and conformance.

## P0: Canonical Semantics

- Make runtime, Z3, Alloy, and Lean agree on shared fixtures.
  - Current support: `make verify-core` includes a backend-parity summary with feature-category rows and explicit unsupported-feature boundaries; runtime/Z3 differential fixtures cover nested `all_of`/`any_of`, exception guards, `apply_scope`, scoped fact overrides, and optional/pass values.
  - Expand fixture categories: flat elements, nested `all_of`, nested `any_of`, mixed groups, exceptions, `defeats`, `is_infringed`, `apply_scope`, penalties, money/duration, optional values.
  - Add differential tests: runtime verdict == Z3 model verdict == Lean expected verdict where available.
  - Acceptance: runtime, Z3, and Lean fixture parity reports covered and unsupported feature categories explicitly; Alloy remains explicit-unsupported until it has parity coverage.

## P0: Case Law And Doctrine

- Promote case law from explanation annotations to executable semantics.
  - Current support: `yuho explain` annotates targeted elements with active case-law holdings and marks same-statute overruled authorities inactive.
  - Current support: `yuho explain` also marks same-statute distinguished, reversed, and disapproved authorities inactive for the current explanation.
  - Current support: `yuho refs --treatment` exposes case-to-case treatment edges.
  - Current support: case-law treatment syntax accepts follows/followed, distinguishes/distinguished, overrules/overruled, reverses/reversed, approves/approved, disapproves/disapproved, and applies/applied.
  - Current support: case-law doc metadata models ratio/obiter role, jurisdiction, court level, decision date, and simple interpretive effects; active `requires`/`satisfies`/`excludes` effects can narrow or expand targeted element truth in runtime evaluation, while inactive overruled/distinguished/reversed/disapproved cases are ignored.
  - Model richer procedural burden, jurisdictional priority, and precedent conflict rules over cases and statutes where jurisdiction permits.

## P1: Formal Mechanisation

- Close the known Lean proof gaps incrementally.
  - Add binder infrastructure for scoped names.
  - Add richer doctrine/case-law semantics once runtime semantics exists.

## Non-Goals For Now

- Do not optimize syntax novelty for esolang appeal.
- Do not add more export formats before backend parity improves.
- Do not claim end-to-end legal correctness; claim parsed, checked, transpiled, evaluated, or verified only for the covered fragment.
