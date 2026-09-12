# Yuho rewrite migration contract

**Status:** Proposed inventory for maintainer review, 12 September 2026  
**Authority:** [Repository audit](REPOSITORY-AUDIT.md), cited executable paths and the [accepted Haskell ADR](ADR-0001-HASKELL.md); this is not a promise of permanent .yh syntax compatibility.

The maintainer has chosen a freely redesigned new surface language. Current .yh behaviour is evidence for migration and differential testing. The contract distinguishes *semantic behaviour to preserve*, *temporary migration compatibility* and *intentionally redesigned behaviour*. A fixture is normative only when its expected meaning and scope are reviewed. Existing Python outputs can be wrong, incomplete or ambiguous.

## 1. Semantic behaviour to preserve

| Supported subset | Observable equivalence target | Evidence and boundary |
|---|---|---|
| Closed Boolean branches | Inherited ancestor requirements, recursive all_of/any_of, alternative sibling subsection leaves, ordered paths and definition-only failure. | [test_runtime_subsections.py](../../tests/test_runtime_subsections.py); first formal fragment ClosedBooleanBranches-v1 excludes arbitrary expressions, exceptions, outcomes and penalties. |
| Registered acyclic exception guards | A satisfied branch evaluates a registered is_infringed target in the caller's fact context; branch-scoped defeat, missing target/cycle/unsupported guard diagnostics and unresolved aggregate remain explicit. | [test_runtime_exception_dependencies.py](../../tests/test_runtime_exception_dependencies.py); next fragment AcyclicGuardedExceptions-v1. Legacy first-firing order is observed but needs priority review before generalizing. |
| Supported typed facts | Primitive and typed fact values are distinguished; supplied burden/standard metadata mismatches affect element results when both sides supply metadata. | [test_burden_runtime.py](../../tests/test_burden_runtime.py), [facts.py](../../src/yuho/eval/facts.py). This is not a full evidential proof-state algebra. |
| Guarded penalties | Select penalty source IDs from satisfied branches, inherit ancestor blocks, keep unguarded blocks cumulative and report distinct simultaneously true sibling guards with YRTP001. | [test_runtime_penalties.py](../../tests/test_runtime_penalties.py); no general Z3 parity for these cases. |
| Limited case effects | Preserve reviewed supported treatment/precedence/declaration-order cases as a later fragment, with explicit support status. | [test_case_law_effects.py](../../tests/test_case_law_effects.py); only three SG files contain case-law blocks, and no broad doctrine claim follows. |

The target is semantic equivalence of status, essential trace edges, citation/source IDs and ordered diagnostics on reviewed fixtures, not universal agreement with Python truthiness, fact-key collision order or known corpus mistakes. Missing or unsupported evidence must not become false. Current overall_satisfied is an Optional[bool] compatibility projection, not a general proof-status semantics. Corrected behaviour gets an intentional-divergence record with old result, new result, reason and reviewer.

## 2. Temporary migration compatibility

This category keeps existing supported workflows usable during staged replacement. It does not force the new surface language to accept the old grammar.

### Source, parser and analysis

The legacy reader accepts .yh/.yuho UTF-8 sources, first-line #yuho v5.1/v5.1.0 pragma, comments/doc-comments, literals, structs/types/functions, statutes/subsections, imports, references, exceptions, penalties and feature-gated civil forms. [wrapper.py](../../src/yuho/parser/wrapper.py) strips a BOM, rejects NUL and source/files over 10 MiB, reports ERROR/MISSING nodes, and supports incremental edits in UTF-8 byte positions. [builder.py](../../src/yuho/ast/builder.py) uses Tree-sitter fields/byte spans and retains doc comments; other trivia is not lossless in AST/IR. The typed-struct-literal after non-doc comment issue is rejected with Y0103. Generated parser.c/node-types.json lag grammar.js/grammar.json outcome rules. These facts define a legacy parser subprocess oracle and migration diagnostics, **not** the acceptance grammar for new syntax.

[analysis.py](../../src/yuho/services/analysis.py) exposes phase validity, errors/warnings/lint/semantic and Canonical IR summary through AnalysisResult.validation_payload. AnalysisError.to_dict carries stage, message, error_code, location and node type. Preserve legacy consumer fields and stage/source semantics while Python owns the endpoint; version replacements and deprecations explicitly. Analysis disk cache is bounded JSON, not SQLite. No production central .yuho configuration format was found.

### CLI and exit behaviour

[main.py](../../src/yuho/cli/main.py) registers doctor, init, check, ci-report, upgrade, lint, fmt, ast, transpile, diff, test, verify, debug, explain, irac, literate, refs, schema and completion. Existing flags/aliases, stdin and output modes are command-specific ([CLI reference](../user/cli-reference.md)). The installed second executable is yuho-lsp ([pyproject.toml](../../pyproject.toml)). Inventory actual command fixtures before native cutover; a proposed eval/trace/export command cannot silently remove a current workflow.

The [published exit-code guide](../user/cli-exit-codes.md) describes 0 success, 1 error, 2 warning and 130 interrupt, but implementation differs: check returns 0 on warning-only normal/JSON/SARIF paths, lint uses 2 for warning-only, verify uses 2 for unavailable/invalid prerequisites, and Click uses 2 for usage errors. Preserve observed behaviour for legacy callers during coexistence. The maintainer must approve a corrected **per-command prospective** exit contract before the native CLI freezes; do not assert the current table is uniformly true.

### Diagnostics and machine data

Stable legacy diagnostic families are Y0001–Y0007, Y0100–Y0103, Y0199, Y0200, Y0250, Y0300, Y0400 and Y0499 ([analysis.py](../../src/yuho/services/analysis.py)); YIR&lt;CONSUMER&gt;001 capability rejection ([canonical.py](../../src/yuho/ir/canonical.py)); YRTP001 penalty overlap, YROD001–YROD003 outcome and YRDG001–YRDG003 dependency guard ([statute_evaluator.py](../../src/yuho/eval/statute_evaluator.py)); lint rule names/severity live in [lint.py](../../src/yuho/cli/commands/lint.py). Keep codes, stage, severity, path and spans where a legacy machine consumer relies on them; free text can be reviewed separately.

Machine formats include ci-report JSON version yuho-ci-report-v1; SARIF 2.1.0 with rule IDs, %SRCROOT% and 1-based spans; JUnit XML from test; facts JSON primitive shorthand or a facts object with value/type/source/date/jurisdiction/evidential_status/burden/standard_of_proof/confidence ([facts schema](../user/facts-schema.json)); AST JSON schema 1.0.0 ([json_schema.py](../../src/yuho/transpile/json_schema.py)); source maps v3 and provenance sidecars 1.0.0. The sidecar contains a current timestamp and is not byte-deterministic. Analysis cache version is yuho-analysis-cache-v2. Version and schema-validate replacement outputs rather than copying incidental whitespace.

Canonical IR is yuho.canonical-ir v1.2. Its source hash is SHA-256 of the UTF-8 source argument; semantic digest hashes compact sorted-key Unicode JSON of to_dict without source_hash; artifact digest includes source_hash. Source spans are omitted, while field/list/enum/string conversions contribute to bytes. **Keep these semantics unchanged.** Its AST snapshots and adapter requirements mean it is migration evidence, not the first new wire boundary. KernelInput v1 and its digest are independent.

### LSP, exports and packaging

[server.py](../../src/yuho/lsp/server.py) implements a stdio pygls server with didOpen/didChange/didSave/didClose diagnostics, hover, same-file/imported cross-section definition and references, keyword completion, regex semantic tokens and yuho.check code action. It caches source/tree/AST/analysis by URI; incremental parse is followed by an analysis reparse. Replay protocol-visible JSON-RPC requests, versions, spans and diagnostics before retiring it. The VS Code integration is in editors/vscode-yuho.

[TranspileTarget](../../src/yuho/transpile/base.py) registers JSON, English, LaTeX, Mermaid flow/mindmap, Alloy, DOCX, Akoma Ntoso XML and LegalRuleML with aliases/extensions. PDF and SVG/PNG are externally rendered derivatives. The 524×8 snapshot matrix contains text fingerprints, not independent semantic judgments. Source-map v3 and XML/XSD tests are relevant, but exporters mostly visit AST and can be lossy. Keep legacy export endpoints until reviewed target-specific goldens and source mapping pass; new-language output may intentionally differ.

Packaging currently uses Python >=3.10, Click and Tree-sitter runtime dependencies, uv.lock, install.sh requiring uv 0.11.14 and default Python 3.13, Hatch C-parser build, wheels/sdist and Docker linux/amd64 plus linux/arm64. CI tests Ubuntu Python 3.10–3.13. macOS/Windows parity is unverified by the audit; Windows is rejected by the Tree-sitter Makefile despite a suffix branch in the build hook. New binaries need declared platform install/launch tests before cutover. Observable controls include YUHO_ANALYSIS_CACHE, YUHO_CACHE_DIR, XDG_CACHE_HOME, CI, NO_COLOR, FORCE_COLOR, TERM, YUHO_LOG_LEVEL, YUHO_ALLOY_JAR/ALLOY_JAR and Click completion. Installer/release/test toggles are workflow controls, not DSL semantics.

## 3. Intentionally redesigned behaviour and non-promises

The new language may change keywords, declaration order syntax, comments/trivia policy, grammar pragma, file extension, recovery text, formatter layout and export prose. Legacy Y0103 is a temporary safety diagnostic, not a new grammar rule. Exact AST JSON field layout and v1.2 source hashes are not new-language semantic contracts. Preserve v1.2 read/compare support only where migration consumers require it; do not mutate its schema to fit the kernel.

The new semantic model may introduce typed proof states, outcomes, procedural dispositions, temporal/fault/causal/participant relations and doctrine packages. These are **new requirements**, not features already implemented end to end. Current typed outcomes are partial; no checked-in .yh file declares an outcome, and generated parser artifacts are stale. General case-law breadth, civil primitives, arbitrary generic types, hosted OpenAPI, full Z3/Alloy/Lean parity and blanket legal correctness are outside the initial equivalence contract. BNS, Malaysia and Pakistan skeleton corpora are not reviewed executable doctrine. README's unqualified whole-DSL verification wording is not an assurance baseline.

Singapore Penal Code section 84 plus a CPC disposition is reserved for a later product-discriminating slice. It requires the cross-Act package and CPC corpus work (#63/#66), typed outcomes (#51), exact authoritative source versions, hash-bound provenance, reviewed fact pattern, named legal reviewer and a specified procedural consequence. Existing s84/s511 empty-fact tests prove only a no-vacuous-satisfaction regression. Known s299 and ss302/304 concerns (#52/#53) likewise require legal review rather than blind Python parity.

## 4. Fixture classification and promotion

Every comparison fixture must record ID, source file/hash, schema and implementation versions, capability fragment, facts/reference date, expected status/trace/diagnostics, category, rationale and reviewer. Use these classes:

- **semantic-preserve:** reviewed observable rule in the supported fragment, such as synthetic subsection and dependency cases;
- **temporary-compatibility:** CLI/LSP/schema/parser/export workflow to keep during migration;
- **review-and-correct:** old output is inconsistent, ambiguous or legally suspect; record the approved new result;
- **experimental/unsupported:** parse-only, partial outcome, civil/temporal or backend-rejected construct; expect a typed capability result, not invented semantics.

Promotion to normative status needs a reviewed expected judgment and source authority where doctrine is involved. Differential agreement alone is insufficient. Keep old/new values and signed rationale for intentional changes. The [language spike](LANGUAGE-SPIKE-SPEC.md) defines the initial exact kernel fixtures and normalization rules.
