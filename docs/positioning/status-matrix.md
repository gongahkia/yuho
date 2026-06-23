# Yuho Feature Status Matrix

This matrix is an honesty layer for Yuho's public claims. A row marked
`stable` means the surface is implemented and covered by retained tests. It
does not mean the legal interpretation is complete or court-authoritative.

Status labels:

- `stable`: implemented, documented, and covered by retained tests.
- `partial`: useful, but known semantic or coverage gaps remain.
- `experimental`: available for research or export, but not a trust boundary.
- `unsupported`: not implemented as a supported Yuho surface.

| Surface | Status | Tested by | Notes |
|---|---|---|---|
| Parser | stable | `tests/test_*grammar*.py`, `make verify-coverage` | tree-sitter grammar parses the checked-in SG Penal Code corpus. |
| AST builder | stable | `tests/test_core_units.py`, `tests/test_new_constructs.py` | Produces Python AST nodes used by analysis, transpilers, and verifiers. |
| Type checker | partial | `tests/test_semantics.py`, `tests/test_civil_feature_grammar.py` | Nominal checking exists; generics and some numeric/legal abstractions are limited. |
| Lint | stable | `tests/test_lint_command.py`, `make verify-coverage` | Includes statute-core and fidelity diagnostics. |
| Formatter | partial | `tests/test_fmt_cli.py` | Useful for supported statute shapes; not a canonical pretty-printer for every grammar construct yet. |
| Runtime eval | partial | `scripts/verify_runtime_tests.py`, `tests/test_runtime_z3_differential.py` | Element truth still often comes from boolean fact keys; richer evidential facts remain TODO. |
| Explain | partial | `tests/test_explain_cli.py` | Explains element satisfaction; does not yet explain mature precedent/proof-standard semantics. |
| Debug | partial | `tests/test_debug_cli.py` | Useful element trace output; shares runtime fact-model limits. |
| Reference graph | stable | `tests/test_reference_graph.py`, `tests/test_cli_refs.py` | Corpus graph for statute references and cycles. |
| Z3 | partial | `tests/test_soundness_sanity.py`, `tests/test_z3_apply_scope.py`, `make verify-runtime-tests` | Conformance-tested SMT backend; solver encoding remains the trust boundary. |
| Alloy | experimental | `tests/e2e/test_verify_pipeline.py` | Bounded model output; unsupported constructs must be treated explicitly. |
| Lean | partial | `make verify-mechanisation`, `make verify-structural-diff` | Mechanised spec/smoke evidence, not full corpus proof coverage. |
| JSON transpiler | stable | `tests/test_transpile_snapshot_matrix.py` | Snapshot-tested over SG Penal Code. |
| English transpiler | stable | `tests/test_transpile_snapshot_matrix.py` | Controlled English, not legal advice. |
| LaTeX transpiler | stable | `tests/test_transpile_snapshot_matrix.py` | TeX rendering depends on local TeX packages. |
| Mermaid transpiler | stable | `tests/test_transpile_snapshot_matrix.py`, `scripts/verify_mermaid_verbose.py` | Text output is snapshot-tested; image rendering depends on Mermaid CLI. |
| Mermaid mindmap transpiler | stable | `tests/test_transpile_snapshot_matrix.py` | Text output is snapshot-tested. |
| Akoma Ntoso | stable | `make verify-akn-xsd`, `tests/test_akn_validator.py` | XML round-trips against the vendored OASIS XSD for the SG corpus. |
| LegalRuleML | stable | `tests/test_transpile_snapshot_matrix.py`, `scripts/lrml_roundtrip.py` | Export surface, not an independent semantics oracle. |
| DOCX | partial | `tests/e2e/test_new_transpilers.py` | Registered output target; not part of the full deterministic snapshot matrix. |
| LSP | partial | `tests/test_lsp*.py` where present, manual editor use | Language-server surface exists; editor UX is not the core trust boundary. |

## Claim Boundary

Yuho can parse, check, lint, transpile, evaluate, and verify the covered
fragment of its DSL. It should not be described as proving end-to-end legal
correctness. Legal correctness still depends on source fidelity, open-textured
terms, fact modeling, jurisdictional context, precedent, burden of proof, and
the verifier/transpiler trust boundary.

## External Baselines

- Catala emphasizes literate legislative programming and one-to-one mapping
  between statute text and executable specification.
- L4 emphasizes broader legal specification tooling, priority/meta-rules, IDE
  flows, and decision-service surfaces.
- OpenFisca is stronger as a mature policy-computation engine and API surface.
- Blawx is stronger as a non-programmer-friendly Rules as Code authoring and
  explanation environment.
- Akoma Ntoso and LegalRuleML are standards/interchange targets, not proof of
  Yuho semantics by themselves.
