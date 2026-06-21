# Yuho TODO

Strict [todo.txt v1](https://github.com/todotxt/todo.txt) syntax inside the code fence below.
Priorities: (A) cheap/blocker, (B) medium, (C) large/experimental.
Projects: +language +tooling +corpus +housekeeping +education +jurisdiction +positioning +compiler.
Contexts: @grammar @ast @lint @lean @verify @transpile @cli @lsp @resolver @library @repo @memory @typecheck @docs @scrape @viz @parser @analysis @interpreter @tests.

```todo
(A) 2026-06-21 Update MEMORY.md key paths after fossil deletion +housekeeping @memory effort:XS
(B) 2026-06-21 AST: InterpretationNode carrying citation + court + endorsement (binding|persuasive|none) +language @ast effort:S
(B) 2026-06-21 Lint: warn when element has competing interpretations with no endorsement metadata +language @lint effort:S
(B) 2026-06-21 Reference encodings: rewrite s415_cheating and s300_murder using `interpretation` instead of dual-function pattern +language @library effort:S
(B) 2026-06-21 Grammar: add `treatment followed|distinguished|overruled` to caselaw block +corpus @grammar effort:S
(B) 2026-06-21 AST: caselaw treatment edges in library/reference_graph.py +corpus @ast effort:S
(B) 2026-06-21 Lint: detect overruled caselaw still cited as authority; warn on contradictory treatment chains +corpus @lint effort:M
(B) 2026-06-21 Extend `yuho refs` command to query treatment graph (--treatment, --overruled) +corpus @cli effort:S
(C) 2026-06-21 Grammar: promote `@jurisdiction` annotation to first-class statute parameter +corpus @grammar effort:M
(C) 2026-06-21 AST: JurisdictionNode and jurisdiction-scoped definition table in ast/scope_analysis.py +corpus @ast effort:M
(C) 2026-06-21 Resolver: enforce same-jurisdiction or explicit cross-jurisdiction import in services/analysis.py +corpus @resolver effort:M
(C) 2026-06-21 Encode 5 representative IPC sections under jurisdiction-typed scheme as proof-of-concept +corpus @library effort:L
(C) 2026-06-21 Grammar: civil-law primitives `party` `obligation_to` `condition_precedent` `breach` behind --feature=civil flag +language @grammar effort:L
(C) 2026-06-21 AST: civil-law primitive nodes in src/yuho/ast/nodes.py +language @ast effort:M
(C) 2026-06-21 Type checker: civil-law primitive type rules in src/yuho/ast/type_check.py +language @typecheck effort:M
(C) 2026-06-21 Proof-of-concept: encode one contract-law section under civil feature flag +language @library effort:M
(C) 2026-06-21 Grammar: agent/patient role tags on element/struct fields +language @grammar effort:M
(C) 2026-06-21 AST: FactEventNode with timestamped action + role-typed participants +language @ast effort:M
(C) 2026-06-21 Bounded quantification primitive `exists_at_most N within DURATION` for sentencing aggravators +language @ast effort:M
(C) 2026-06-21 ASP/Datalog backend under src/yuho/explain/ producing justification trace per element +tooling @verify effort:XL
(C) 2026-06-21 New CLI `yuho explain --facts FILE SECTION` returning element-by-element satisfaction trace +tooling @cli effort:M
(C) 2026-06-21 English-render the explain trace through existing transpile/english_transpiler.py +tooling @transpile effort:M
(A) 2026-06-21 New CLI `yuho irac --facts FILE STATUTE.yh` emitting IRAC-structured English via english_transpiler.py +education @cli effort:M
(A) 2026-06-21 Curate library/problem_questions/ with 10 canonical SG criminal-law hypos as .yh fact patterns +education @library effort:M
(B) 2026-06-21 Mermaid theme colour-coding AR (red) MR (blue) circumstance (green) exception (amber) in mermaid_transpiler.py +positioning @viz effort:S
(B) 2026-06-21 BNS 2023 raw scrape via scripts/scrape_bns.py mirroring scripts/scrape_sso.py +jurisdiction @scrape effort:L
(B) 2026-06-21 Encode 358-section BNS skeleton under library/bharatiya_nyaya_sanhita/ with L1+L2 pass +jurisdiction @library effort:XL
(B) 2026-06-21 IPC ↔ BNS section mapping table generated via structural diff at library/_index/ipc_bns_mapping.json +jurisdiction @library effort:M
(C) 2026-06-21 Pakistan PPC raw scrape + 20-section proof-of-concept encoding under library/pakistan_penal_code/ +jurisdiction @scrape effort:L
(C) 2026-06-21 Malaysia Penal Code Act 574 raw scrape + 20-section proof-of-concept encoding under library/malaysia_penal_code/ +jurisdiction @scrape effort:L
(C) 2026-06-21 `yuho diff --jurisdictions sg,my,pk SECTION` cross-corpus comparative diff in cli/commands/diff.py +jurisdiction @cli effort:M
(B) 2026-06-21 Auto-render SVG per statute under docs/visualizations/<section>/element-graph.svg via scripts/build_corpus.py +positioning @viz effort:M
(B) 2026-06-21 Write docs/positioning/yuho-vs-l4.md as one-page complementary-not-competing technical comparison +positioning @docs effort:S
(B) 2026-06-21 Write docs/positioning/why-criminal-law.md niche statement referencing CCLAW defeasible-semantics-for-L4 overlap +positioning @docs effort:S
(A) 2026-06-21 Stabilise error_code scheme: migrate snake_case strings in services/analysis.py to Y0001-Y9999 and expand docs/user/error-codes.md with per-code anchored explainers +compiler @analysis effort:M
(A) 2026-06-21 Formatter idempotency Hypothesis property test fmt(fmt(x)) == fmt(x) in tests/test_properties.py +compiler @tests effort:S
(A) 2026-06-21 Differential test interpreter vs Z3 backend on 90 runtime-sweep fixtures; fail on disagreement +compiler @verify effort:M
(A) 2026-06-21 Wire eval/debugger.py to new `yuho debug --break-on element FACTS.yh STATUTE.yh` CLI subcommand +compiler @cli effort:M
(A) 2026-06-21 Tighten src/tree-sitter-yuho/grammar.js conflicts list: replace explicit conflicts entries with prec.left/prec.right/prec.dynamic where possible +compiler @grammar effort:M
(B) 2026-06-21 Incremental reparse via tree-sitter Tree.edit() in parser/wrapper.py to support per-keystroke LSP reparse +compiler @parser effort:M
(B) 2026-06-21 Query-based incremental compilation keyed on (file_hash, stage) memoising parse + AST + analysis between yuho invocations +compiler @analysis effort:L
(B) 2026-06-21 Extend TranspilerBase contract: return TranspileResult(output, warnings, manifest) instead of bare str; update all 8 transpilers +compiler @transpile effort:M
(B) 2026-06-21 Per-transpiler conformance matrix: golden snapshots for 524 statutes × 8 transpilers under tests/snapshots/ with insta-style accept/reject +compiler @tests effort:L
(B) 2026-06-21 Atheris fuzz harness on Parser.parse + ASTBuilder.build to surface crashes on malformed input +compiler @parser effort:M
(B) 2026-06-21 Z3 ↔ Alloy differential test in verify/combined.py logging per-fixture disagreements as machine-readable JSON +compiler @verify effort:M
(B) 2026-06-21 Source-map provenance in transpilers: JSON sidecar mapping output spans to AST source_locations (V3 source-map shape) +compiler @transpile effort:L
(C) 2026-06-21 Watch mode `yuho check --watch FILE` re-running on .yh file change via watchdog +compiler @cli effort:S
(C) 2026-06-21 Grammar version pragma `#yuho v5.1` at top of .yh files + `yuho upgrade` mechanical rewriter between grammar versions +compiler @grammar effort:L
```
