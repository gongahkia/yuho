# ADR-0002: Haskell owns the authoritative Yuho language path

**Status:** Accepted, 14 September 2026. This decision extends [ADR-0001](ADR-0001-HASKELL.md).

Haskell is Yuho's authoritative production implementation language. The Haskell library owns the lexer, parser, source-located AST, resolver, type and semantic checker, legal modelling types, KernelInput lowering, CLI, runtime orchestration, semantic kernel and canonical technical results. An authoritative `yuho check`, `compile` or `run` command must not invoke Python. Tree-sitter may serve editor tooling and syntax highlighting; it is not the authoritative parser.

The existing [Python v0.1–v0.4 frontend](../../rewrite/frontend/core.py) remains frozen migration and conformance evidence, not the production execution path. Migration compares authored sources, structured diagnostics, exact requests and response bytes against its accepted fixtures. Only the bounded v0.1 section 84 and fictional offence-plus-exception forms have a [Haskell frontend](HASKELL-YUHO-FRONTEND-POC.md) in this milestone. Exact-version modules, temporal selection and multi-fragment plans have **not** been ported. Canonical IR v1.2 remains unchanged and separate from KernelInput v1; a new compiler boundary needs its own decision.

ModelBundle and provenance tooling support authored models but do not determine the language roadmap. The immediate goal is an operable research proof of concept for bounded Singapore criminal-law modelling, with technical derivations rather than legal decisions. Hashes and successful execution do not establish source authenticity, current law, factual truth or a judicial outcome. No production legal-decision system is claimed.
