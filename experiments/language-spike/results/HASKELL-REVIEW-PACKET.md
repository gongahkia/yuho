# Haskell review packet

**Candidate:** GHC 9.8.4, Haskell2010, `-O2 -Wall -Werror`; no language extensions or warning suppressions. Four modules, 512 nonblank/noncomment logical lines: `Json.hs` 104, `Sha256.hs` 70, `Kernel.hs` 315, `Main.hs` 23. `Kernel.hs` is the highest-complexity module: decoding, invariant checks, branch selection, evaluation and result assembly share one module. Parsec 3.1.17.0 and the pinned base libraries are declared in [language-spike.cabal](../haskell/language-spike.cabal). No type families, Template Haskell, overlapping instances or effect framework.

| Semantic/protocol rule | Location |
|---|---|
| UTF-8 line decoding, one response per request, stdout flush | `Main.hs` |
| Duplicate-key JSON rejection, explicit sorted-key canonical encoding | `Json.hs` |
| Source and KernelInput SHA-256 | `Sha256.hs`, `Kernel.hs` `decodeInput`/`innerDigest` |
| Typed node/span/diagnostic decoding and supported fragment validation | `Kernel.hs` `decodeSpan`–`decodeInput` |
| Unique IDs, max nodes, nonempty groups, unsupported kind, total referenced facts | `Kernel.hs` `validateProgram` |
| Inherited requirements, alternative executable leaves, definition-only false | `Kernel.hs` `leafBranches`, `run` |
| All/Any evaluate every member in order, ordered trace edges and branch reduction | `Kernel.hs` `evaluateRequirement`, `evaluateBranch`, `run` |
| Parser diagnostic transport and structured rejection | `Kernel.hs` `run`, `decodeFailure` |

For B06, `leafBranches` yields one `synthetic:S` branch. `evaluateRequirement` visits `group:all`, leaf `a=true`, `group:any`, `b=false`, `c=true` in declaration order. It evaluates all members before reducing `Any` to true and `All` to true. The branch `trace_ids` and each group's `children` retain these IDs; paths remain `["S"]`, and spans are source byte ranges 0–1, 2–3 and 4–5. [B06 frozen response](../fixtures/expected/B06.json) and [exported proof vector](HASKELL-PROOF-VECTORS.json) show the exact mapping. A proposed Lean relation can consume a finite list of named facts and an inductive `Leaf | All | Any` tree, then derive each Boolean value and ordered trace. The manual mapping is three conceptual steps: decode the JSON vector, reconstruct nodes/facts by ID and ordered child list, then check each Boolean value and trace edge against the relation. Implemented proof glue is **0 LOC**; a JSON-to-relation adapter and theorem are future work. Recorded assumptions are closed total facts, inherited conjunction, alternative branch disjunction and evaluation without short-circuit omission. The relation still needs explicit trace-order and source-span constructors; no theorem or end-to-end soundness claim is made.

Partial/unsafe inventory: `Data.Array.!` appears only in the SHA-256 round schedule/constants, with indices constructed in fixed 0–63 loops and schedule references 0–63. `fromIntegral` narrows byte-length arithmetic to 64-bit SHA length and has the standard SHA-256 length limit. Parsec can fail through `Either`; `Map.lookup` is handled. No `head`, `tail`, `fromJust`, `error`, `undefined` or unchecked semantic lookup appears. Very deep adversarial JSON/program nesting beyond the frozen bounded cases has not been stress-tested; decoding precedes the max-node check, so production input-depth hardening remains open. This packet explains operations; independent reviewers must judge whether they are sufficiently safe.

To reproduce a failure, run `cd experiments/language-spike/haskell && cabal v2-build --offline --jobs=1`, then `/usr/bin/python3 ../harness/run.py` from `experiments/language-spike`; the common harness reports the first differing case and exact bytes. `R01` exercises missing facts, `R02` duplicate IDs, `R03` unsupported capability, `R04` protocol version, and `P02` UTF-8 byte/display diagnostic transport. Clean offline build details are in [HASKELL-BUILD.log](HASKELL-BUILD.log).

**Implementer self-assessment, not a final reviewer score:** The algebraic types and `Either` flow make the rule mapping direct, and `traverse` retains trace order. `Kernel.hs` concentrates several responsibilities; the custom SHA implementation adds low-level review burden. A separate reviewer should inspect the inheritance rule and rejected-input boundary in particular. Maintainer score: **pending**. Separate non-implementing runtime score: **pending**.
