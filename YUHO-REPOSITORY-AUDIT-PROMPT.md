# Yuho Repository Audit Prompt

Copy this entire prompt into the Codex runtime that has the Yuho repository checked out. Attach or place these two documents in `docs/rewrite/` first if convenient:

- `YUHO-REWRITE-DECISION-REPORT.md`
- `YUHO-REWRITE-ARCHITECTURE-PROPOSAL.md`

---

You are auditing the Yuho repository to validate a proposed clean rewrite. Do not implement the rewrite yet.

Read these documents completely before inspecting code:

1. `docs/rewrite/YUHO-REWRITE-DECISION-REPORT.md`
2. `docs/rewrite/YUHO-REWRITE-ARCHITECTURE-PROPOSAL.md`

If the files are elsewhere, locate them by exact filename. Also read every applicable `AGENTS.md` before acting.

The current proposal recommends OCaml for the production toolchain, leaves the proof assistant open pending a Lean/Rocq/F* spike, permits a free redesign of `.yh`, and proposes a universal criminal-law kernel plus versioned jurisdiction packages with Singapore as the reference implementation.

Your job is to test the proposal against the real repository. Treat documentation and README claims as hypotheses until corroborated by code, tests, generated artefacts and CI configuration.

Work read-only. Do not modify source, configuration, generated artefacts, dependencies, issues or Git state. You may create only one new file, `docs/rewrite/REPOSITORY-AUDIT.md`, if that path does not overwrite existing work. If it already exists or the worktree has overlapping changes, return the report in chat and do not write a file. Do not commit.

## Required investigation

### 1. Repository and dependency map

- Record current branch, HEAD, status and relevant tool versions.
- Map top-level packages, entry points and dependency direction.
- Identify cycles, global registries, import-time side effects and plugin discovery.
- Produce a subsystem retirement order for parser, AST/IR, runtime, analyses, solver, exporters, corpus tools, LSP, CLI and formal artefacts.
- Identify user changes in the worktree; do not touch them.

### 2. External compatibility contracts

- Enumerate CLI commands, flags, exit codes and stdout/stderr formats.
- Enumerate public Python imports and any documented library API.
- Enumerate JSON/schema versions, file formats, cache formats, generated outputs and LSP methods.
- Search docs, workflows, scripts and tests for consumers.
- Classify every contract as `preserve`, `migrate with adapter`, `redesign`, `internal only`, or `unknown`.
- Cite exact files and symbols for every finding.

### 3. Language and corpus reality

- Locate every grammar/parser implementation and generated parser artefact.
- Determine which parser is authoritative in batch compilation, LSP/editor tooling and tests.
- Inventory grammar constructs and measure their occurrence across `.yh` files.
- Identify constructs that parse but have no runtime semantics, constructs used only by exporters, and unreachable/dead syntax.
- Locate all comment/trivia attachment logic and reproduce or precisely trace the comment-before-typed-structure defect.
- Identify formatter/round-trip guarantees, ambiguity handling and recovery behaviour.
- Report corpus categories, generation sources, review metadata and which files are semantically exercised rather than merely parsed.

### 4. Representation pipeline

- Trace at least three representative inputs from source through CST, AST, canonical IR, analysis, runtime and export.
- Include one simple rule, one exception/defence, and one typed-outcome or cross-Act example if present.
- List the actual in-memory types and serialised versions at each phase.
- Resolve the apparent canonical-IR v1.1/v1.2 discrepancy.
- Identify where source spans, statutory citations, comments, effective dates or stable IDs are lost.
- Identify catch-all nodes, untyped dictionaries and implicit defaults that could admit invalid states.

### 5. Production semantics

- Locate the authoritative evaluator and all alternate/reference evaluators.
- For conditions, exceptions, priorities, temporal rules, causation, fault, participants, attempts, consent, private defence, proof burdens/presumptions, outcomes and sentencing, classify support as `implemented`, `partial`, `schema only`, `corpus only`, `export only`, `experimental`, or `absent`.
- Find every place an unknown, unsupported, solver-unknown or missing value collapses to Boolean, empty, zero or success.
- Identify nondeterminism, ambient state, current-time reads, unordered iteration and unbounded search.
- Identify the strongest existing semantic regression tests and their blind spots.

### 6. Solvers and formal correspondence

- Trace every Z3 and Alloy call from public entry point to encoded query and decoded result.
- State whether each use is normative evaluation, validation, analysis, export or smoke testing.
- Record handling of `unknown`, timeout and unsupported theory.
- Inventory Lean definitions and theorems by concept and status: proved, admitted/axiomatised, bounded, generated, stale or unused.
- Search for any production-IR-to-Lean generator, shared schema, test-vector bridge or refinement proof.
- Determine exactly which current formal claims, if any, apply to the production evaluator.
- Propose one representative theorem for the proof-tool spike using actual repository concepts.

### 7. Migration evidence

- Identify fixtures that can serve as a Python behavioural oracle.
- Select 20–30 representative `.yh` files for a migration conformance suite, covering syntax and semantic risk rather than popularity alone.
- Identify behaviours that should intentionally change in the new design.
- Identify the smallest Singapore vertical slices that exercise homicide/causation/fault, defence plus procedure/proof status, and participation.
- Do not assert current Singapore law from memory; cite the repository source material and flag anything requiring external legal-source verification.

### 8. OCaml-versus-Haskell falsification check

Using the actual dependency and feature map, identify evidence that weakens or reverses the proposed OCaml decision. In particular:

- parser and incremental-editor requirements;
- solver API shape;
- recursive IR and typed-expression ergonomics;
- exporter and FFI dependencies;
- distribution targets;
- performance-critical workloads;
- formal artefact reuse;
- maintainer workflow.

Do not choose based on language taste. State what the comparative spike must measure and which repository fixtures it should use.

## Commands and method

- Prefer `rg` and `rg --files` for discovery.
- Run only safe, non-mutating diagnostics and tests.
- Do not install or upgrade dependencies unless explicitly authorised.
- If a full test is expensive or broken, run targeted probes and report the exact blocker.
- Distinguish verified facts, strong inferences and open questions.

## Required report structure

Write `REPOSITORY-AUDIT.md` with:

1. Executive findings
2. Snapshot and limitations
3. Actual architecture and dependency map
4. External compatibility matrix
5. Grammar and corpus inventory
6. Representation/provenance trace
7. Semantic support matrix
8. Solver and formal-assurance boundary
9. Python retirement dependency graph
10. Recommended migration fixture set
11. Contradictions with the rewrite documents
12. Changes required to the proposed architecture
13. OCaml decision: confirmed, weakened or reversed
14. Blocking questions for the maintainer
15. Appendix of commands, files and symbols inspected

Use exact repository-relative paths and symbol names. Add line numbers only when stable enough to help immediate review. For each conclusion, label confidence `high`, `medium` or `low` and explain material uncertainty.

Finish with a short machine-readable YAML block containing:

```yaml
audit:
  head: "..."
  worktree_clean: true
  language_recommendation: confirmed | weakened | reversed
  ir_versions_observed: []
  external_contracts: []
  retirement_order: []
  blocker_ids: []
  proposed_spike_fixtures: []
```

Stop after the audit. Do not scaffold OCaml or Haskell and do not change implementation code.
