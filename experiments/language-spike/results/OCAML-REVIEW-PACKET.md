# OCaml review packet

**Candidate:** OCaml 5.3.0 native compiler, `-O3`; all warnings are errors except 4 (fragile pattern matches), 42 (type-directed record-field disambiguation) and 70 (missing `.mli` files), suppressed in the [Makefile](../ocaml/Makefile). Four modules, 780 nonblank/noncomment logical lines: `json.ml` 207, `sha256.ml` 120, `kernel.ml` 398, `main.ml` 55. `kernel.ml` is the highest-complexity module. It uses ordinary variants, records, modules and explicit `result`; no GADT, functor framework, first-class module or PPX-derived semantics. The standard-library-only build is pinned to OCaml 5.3.0.

| Semantic/protocol rule | Location |
|---|---|
| UTF-8 validation, one response per line, stdout flush | `main.ml` |
| Duplicate-key JSON rejection, explicit sorted-key canonical encoding | `json.ml` |
| Source and KernelInput SHA-256 | `sha256.ml`, `kernel.ml` `decode_input`/`inner_digest` |
| Typed node/span/diagnostic decoding and supported fragment validation | `kernel.ml` `decode_span`–`decode_input` |
| Unique IDs, max nodes, nonempty groups, unsupported kind, total referenced facts | `kernel.ml` `validate_program` |
| Inherited requirements, alternative executable leaves, definition-only false | `kernel.ml` `leaf_branches`, `run` |
| All/Any evaluate every member in order, ordered trace edges and branch reduction | `kernel.ml` `evaluate_requirement`, `evaluate_branch`, `run` |
| Parser diagnostic transport and structured rejection | `kernel.ml` `run`, `decode_failure` |

For B06, `leaf_branches` yields `synthetic:S`. `evaluate_requirement` visits `group:all`, `a=true`, `group:any`, `b=false`, `c=true` and builds a trace for every node before Boolean reduction. The `Any` group is true because `c` is true, and `All` is true because `a` and `Any` are true. IDs, `["S"]` paths, byte spans and ordered child IDs appear in the [frozen response](../fixtures/expected/B06.json) and [exported vector](OCAML-PROOF-VECTORS.json). A Lean-neutral relation would map the OCaml variants to finite named facts and `Leaf | All | Any` constructors. The manual mapping is three conceptual steps: decode the JSON vector, reconstruct nodes/facts by ID and ordered child list, then check Boolean values and trace edges against the relation. Implemented proof glue is **0 LOC**; a JSON bridge and theorem are future work. Recorded assumptions are closed total facts, inherited conjunction, alternative branch disjunction and evaluation without short-circuit omission. The relation still needs explicit trace-order and source-span constructors; no vector field is intentionally discarded and no end-to-end soundness claim is made.

Partial/unsafe inventory: `String.get` in the JSON parser and UTF-8 validator is guarded by explicit position bounds. `Bytes.get/set`, `Array.get/set` and fixed arrays in SHA-256 are indexed by the padding construction and 0–63 loops. The JSON parser uses a local `Syntax` exception internally but catches it at `parse` and returns `result`; `Stack_overflow` is also caught at that parser boundary. The kernel uses `Result.bind`, `List.assoc_opt`, and exhaustive variant matching for expected failures. Deep program decoding after JSON parsing could still overflow before the max-node invariant check; that is untested outside frozen cases and needs production hardening. These operations are disclosed for independent review rather than scored as safe by the implementer.

To reproduce a failure, run `cd experiments/language-spike/ocaml && make all`, then `/usr/bin/python3 ../harness/run.py` from `experiments/language-spike`; the common harness gives the first differing case and bytes. R01–R04 exercise typed rejection and P02 exercises UTF-8 diagnostic transport. The clean build transcript is [OCAML-BUILD.log](OCAML-BUILD.log).

**Implementer self-assessment, not a final reviewer score:** Variants and explicit `result` make the evaluation path visible. The local JSON parser and SHA implementation make this candidate longer and add byte-level review work; no OCaml package manager was required for the scored kernel. A separate reviewer should inspect `kernel.ml`'s invariant traversal and the parser's exception boundary. Maintainer score: **pending**. Separate non-implementing runtime score: **pending**.
