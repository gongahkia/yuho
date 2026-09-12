# Yuho OCaml-versus-Haskell language spike specification

**Status:** Historical spike specification; technical gates passed and [Haskell ADR-0001](ADR-0001-HASKELL.md) accepted after [independent review](../../experiments/language-spike/results/INDEPENDENT-REVIEW.md). [Evidence bundle](../../experiments/language-spike/results/SCORECARD.md).
**Baseline:** [repository audit](REPOSITORY-AUDIT.md); the former provisional OCaml ADR was replaced by the accepted Haskell ADR.  
**Time box when authorised:** Three focused working days per candidate, followed by one review day

## Question and fairness rule

Which host makes the **same first semantic fragment** clearer to implement, test, prove against a reference and package for Yuho? Both candidates receive identical frozen JSON fixtures, expected results, parser-subprocess responses, resource limits and measurement host. No candidate-specific preprojection, hard-coded case output, native parser, solver library or ambient state is allowed in the scored kernel. Record versions, source commit, commands and any dependency/setup differences. A failed gate is reported, not waived by a weighted score.

The common legacy Python parser/projector stays in a separate subprocess for both. A Menhir/Sedlex or Haskell parser prototype may be recorded as an **unscored follow-up**; replacing Tree-sitter has the separate gates in the [architecture proposal](YUHO-REWRITE-ARCHITECTURE-PROPOSAL.md). The scored parser-diagnostic measure is faithful transport, spans and recovery-state representation through the common adapter, not a claim that either candidate already parses the new language.

## Exact common protocol

The executable reads one line of UTF-8 JSON per request on stdin and writes exactly one line of UTF-8 JSON per response on stdout. Multiple requests run in one process for steady-state checks; cold-start runs launch a fresh process. No logs, prompts or banners go to stdout. The envelope has required keys:

| Request | Type and rule |
|---|---|
| protocol | literal yuho.kernel-protocol/v1 |
| request_id | ASCII fixture ID; echoed unchanged |
| operation | evaluate or validate |
| input_schema | literal yuho.kernel-input/v1 |
| fragment | literal ClosedBooleanBranches-v1 for scored evaluation |
| source | object with relative POSIX path, original UTF-8 text and lowercase SHA-256; each ordered program node carries its own UTF-8 span |
| program | closed ordered provision/rule graph with unique IDs, named elements and All/Any nodes |
| facts | mapping from every referenced element ID to a JSON Boolean; no missing values in valid evaluation |
| policy | reference_date as ISO YYYY-MM-DD and max_nodes=1024; no wall-clock reading |

The response has required keys protocol, request_id, result_schema (yuho.kernel-result/v1), fragment, status, branches, trace, diagnostics and input_digest. Status is true, false or rejected for this first fragment; unresolved is reserved for the next exception fragment and may not be silently reported as false. Branches and essential trace edges follow declaration order. A diagnostic has code, stage, severity, path, span (UTF-8 start/end byte offsets and 1-based displayed line/column) and stable parameter map. Rejection distinguishes protocol/version, decode, invariant and unsupported-capability errors. A non-JSON crash or unexpected stdout is a failure.

Canonical response bytes are UTF-8 JSON with sorted object keys, comma/colon separators, no insignificant whitespace, Unicode preserved, declaration-order arrays and a final LF. Input digest is lowercase SHA-256 of the canonical UTF-8 bytes of the complete KernelInput object: for evaluate, the top-level input_schema, fragment, source, program, facts and policy fields; for validate, input_schema, fragment, source, parser_result and policy. It includes source.sha256 and excludes outer protocol, operation and request_id. KernelInput digests are separate from Canonical IR v1.2 semantic/artifact hashes, which remain unchanged. Freeze one exact canonical byte example before either candidate is scored.

Parser adapter operation uses the same envelope with operation=validate and a parser_result field containing accepted, legacy diagnostics and spans in place of program/facts; the candidate returns normalized diagnostics without evaluating. For this operation, status=true means accepted and status=rejected means parser-rejected; both have empty branches and trace. Paths become repository-relative POSIX paths; source-order diagnostics stay ordered. Do not normalize unresolved to false or strip source byte offsets. The exact field shapes and canonical examples are frozen in experiments/language-spike/schema/ before candidate work.

## Frozen scored fixtures

Construct B01–B05 as language-neutral KernelInput JSON from the named synthetic source cases, retaining source IDs and spans from the **same** Python projection. Construct B06–B07 from the literal closed graph below. The 15 request and expected-response byte files were frozen before either candidate in [fixtures](../../experiments/language-spike/fixtures/) at repository HEAD `6f95b1d450b44777c5aa27b16fa61db2c525f824`; [MANIFEST.json](../../experiments/language-spike/fixtures/MANIFEST.json) records their hashes. The table states the exact scenario and expected essential status/trace; no corpus legal conclusion is inferred.

| ID | Source and facts | Expected essential result |
|---|---|---|
| B01 | [test_runtime_subsections.py::test_sibling_subsection_leaves_are_alternative_branches](../../tests/test_runtime_subsections.py), first=true, second=false | Overall true; ordered s1(a)=true, s1(b)=false; paths (1,a), (1,b). |
| B02 | Same source, first=false, second=false | Overall false; both branches false. |
| B03 | test_nested_branch_inherits_ancestor_requirements_conjunctively, common=false, first=true, second=false | Overall false; inherited common=false recorded at root path. |
| B04 | Same source, common=true, first=false, second=true | Overall true; s2(1)=true; inherited common and both Any children appear in source order. |
| B05 | test_definition_only_provision_is_not_an_empty_satisfied_offence, empty fact map | Overall false, provision_kind=definition_only, zero executable branches. |
| B06 | Hand-authored closed nested All(leaf a, Any(leaf b, leaf c)); a=true,b=false,c=true | Overall true; All and Any trace edges retained, no short-circuit omission of cited elements. |
| B07 | Same B06, a=true,b=false,c=false | Overall false; all three leaf results present. |

B06–B07 use source path fixtures/closed-boolean.yh, provision ID synthetic:S, path ["S"], and the ordered tree All(leaf a, Any(leaf b, leaf c)). Leaf source spans are three consecutive nonoverlapping ASCII byte ranges in the frozen source "a\nb\nc\n": a=[0,1), b=[2,3), c=[4,5); display positions are (1,1), (2,1), (3,1). The All and Any nodes have stable IDs group:all and group:any. The source SHA-256 of exactly these six UTF-8 bytes is 880553fca8fcea94e325ee2cfb48e5a985cc797f39a14cc6d3cedecfeb2ae4d2. This fixture is a semantic KernelInput, not a promise that "a\nb\nc\n" is accepted new-language syntax.

Rejection cases use B06 with exactly one mutation and fixed diagnostic tuples:

| ID | Mutation | Required code / stage / severity |
|---|---|---|
| R01 | Remove fact c | KINV001 / validate / error |
| R02 | Duplicate element ID b at c's position | KINV002 / validate / error |
| R03 | Replace group:any with an opaque legacy-expression tag | KCAP001 / capability / error |
| R04 | Change outer protocol to yuho.kernel-protocol/v2 | KPROT001 / protocol / error |

Each rejection returns status=rejected, no branches or trace edges, and a diagnostic path naming the mutated field. R01–R03 carry the mutated node's span; R04 has null span because no source node is at fault. Both candidates must emit these same codes, stages, severities and paths.

Parser transport cases use these exact UTF-8 legacy sources:

| ID | Source bytes (JSON-style escapes shown) | Expected adapter status |
|---|---|---|
| P01 | string label := "café"\n | accepted; zero diagnostics. This is the Unicode byte-column edit target in [test_parser_incremental.py](../../tests/test_parser_incremental.py). |
| P02 | statute 1 "Café" {\n | rejected; Y0101 parse error, MISSING:}, zero-width UTF-8 byte span [19,19), displayed 1:20. |
| P03 | statute 1 "Bad" { | rejected/incomplete; Y0101 parse error, MISSING:}, zero-width byte span [17,17), displayed 1:18; matches [test_lsp_server.py](../../tests/test_lsp_server.py). |
| P04 | Exact multiline source in [test_hardening.py::test_comment_before_typed_struct_literal_is_rejected](../../tests/test_hardening.py) | rejected with Y0103 at displayed line 8. |

Store original bytes and the Python parser's response as the sole P02/P03 diagnostic golden before either candidate runs; the P02/P03 values above were checked by a single local parser/analysis invocation on 12 September 2026. Compare accepted/rejected, code, stage, severity and byte/display spans. The known Python Unicode error-snippet slicing defect is not a normative message oracle. The malformed incremental-edit fallback in test_parser_incremental.py is a later parser-retirement gate because it depends on an in-memory Tree-sitter tree, not this subprocess transport. A new-language parser's future diagnostics need a separate reviewed golden set.

Two **unscored migration probes** use [s84](../../library/penal_code/s84_act_person_unsound_mind/statute.yh) and [s511](../../library/penal_code/s511_attempt_commit_offence/statute.yh) with empty facts to check no vacuous conviction during projection. Acyclic exception cases from [test_runtime_exception_dependencies.py](../../tests/test_runtime_exception_dependencies.py) and guarded penalty cases from [test_runtime_penalties.py](../../tests/test_runtime_penalties.py) are the next-fragment backlog, not grounds to declare first-fragment failure. In particular section 84 plus CPC disposition is not a spike parity fixture.

## Measurements and thresholds

Run one candidate at a time on the same idle, resource-safe x86_64 host. Record OS/kernel, CPU, RAM, compiler/runtime versions, repository commit, toolchain lockfiles and fixture SHA-256. Use fresh processes and /usr/bin/time -v (or equivalent max-RSS reporting), with the Python parser outside the timed kernel process. Do not run full corpus, grammar generation, Lake build or Docker during this spike. If the machine cannot safely run the measurements, mark them unavailable and defer the decision.

| Measure | Procedure | Acceptance threshold |
|---|---|---|
| Trace parity | Run B01–B07 and R01–R04; compare schema-validated status, ordered branches/essential trace edges, paths and diagnostic tuple. | 11/11 exact structural matches after only documented path normalization; zero unresolved-to-false coercions. |
| Deterministic serialization | Repeat every case 100 times across 10 fresh processes, randomized input-object key order; compare canonical output bytes per case. | One identical byte sequence and digest per case, no stdout contamination. |
| Parser diagnostics | Replay P01–P04 adapter responses 100 times; compare accepted/rejected, code, stage, severity, byte span and displayed span. | 4/4 exact structural matches; Y0103 remains labeled migration-only. Message text is reviewed separately. |
| Cold start | 30 fresh launches per candidate; each reads B06 and exits; report median/p95 elapsed and CPU time. | Median ≤250 ms and p95 ≤500 ms on the fixed host; no run >2 s. Record values even when both pass. |
| Peak RSS | 30 fresh B06 launches and one 1,000-request in-process B01–B07 cycle; /usr/bin/time -v max RSS. | ≤128 MiB for each workload; growth from first to last 100 requests ≤16 MiB after warm-up. |
| Packaging | Build an offline-installable executable/artifact from pinned dependencies on the selected host; install in a clean user directory and replay B01/P02. Record build time, artifact size and runtime shared-library dependencies. | Both cases pass without source tree, network or Python in the kernel process; executable launches on the declared x86_64 target. Other platforms are later release gates. |
| Implementation clarity | Two reviewers inspect only fragment/parser-adapter/protocol code; record changed logical LOC, module count, highest module LOC, exposed invariants, unsafe/partial operations and a 0–5 rubric for traceability of each semantic rule. | Mean rubric ≥4/5, zero unexplained partial operations, no fixture-specific branch. A ≤20% LOC difference is not decisive alone. |
| Proof-boundary ergonomics | Each candidate exports all B cases to the identical Lean-neutral JSON vector and maps one B06 trace to a proposed Lean relation; record manual mapping steps, lines of glue and unresolved representational gaps. No theorem build required here. | All 7 vectors decode with no information loss in IDs, paths or trace edges; zero unrecorded semantic assumptions. Review mapping complexity qualitatively. |

Latency/RSS thresholds are **spike gates**, not claims about current Python performance or future corpus performance. If both pass, compare medians/p95, RSS and reviewer notes; a sustained >25% advantage on at least two operational measures may influence the decision only after parity and clarity pass. If either misses a gate, fix only a bounded implementation defect within the time box; otherwise record the failure.

## Decision rule and evidence bundle

Parity, determinism, diagnostics and packaging are mandatory. If both candidates pass, compare reviewed clarity and proof mapping, packaging, latency and RSS. A technical tie means both satisfy every mandatory gate and neither has a material advantage in any of those dimensions; **maintainer preference decides a genuine tie**. The maintainer currently leans toward Haskell, which is legitimate maintainability evidence but cannot change the fixtures, implementation effort, measurements or score reporting. If neither passes, extend the spike specification or reconsider the boundary; do not declare a winner. The two independent clarity reviews must precede a final decision.

The scorecard must include raw JSON fixtures and hashes, expected/actual response diffs, command logs, 30-run latency/RSS samples, build/install transcript, LOC/rubric sheets, proof-mapping notes, rejected cases and a short signed decision. No language choice followed from this specification alone. The completed [scorecard](../../experiments/language-spike/results/SCORECARD.md) records one independent runtime review and the maintainer's Haskell maintainability decision. The maintainer did not supply a second numerical code-review score; the earlier two-score plan remains historical rather than a claim about completed reviews.

The local Draft 2020-12 schema initially used opaque relative `$id` values that made its cross-file `$ref` unresolvable. Stable absolute schema URIs were substituted after candidate implementation and both candidates were rerun through the same validator; no frozen request, response or source bytes changed. See the [reproducibility record](../../experiments/language-spike/results/REPRODUCIBILITY.md).
