# Yuho Haskell production foundation

This workspace is the bounded production implementation under [accepted ADR-0001](../../docs/rewrite/ADR-0001-HASKELL.md). It implements `ClosedBooleanBranches-v1` and the separately [specified `AcyclicGuardedExceptions-v1`](../../docs/rewrite/ACYCLIC-GUARDED-EXCEPTIONS-V1.md). The [language spike](../../experiments/language-spike/README.md) and its fixtures, candidates, measurements and proof vectors remain frozen historical evidence. The Python parser, Tree-sitter, CLI, LSP, exporters and corpus tools are unchanged. This executable is a versioned subprocess, not a replacement product entry point.

The one Cabal package keeps responsibilities in separate modules: `Yuho.Core.Types` and `Core.Source` own typed source identity and span checks; `Protocol.Json`, `Decode` and `Encode` own the bounded JSON boundary, closed request schema and canonical response; `Kernel.Validate`, `Evaluate` and `Run` own the original ordered Boolean semantics and structured rejection. `Yuho.Exception.Decode`, `Validate`, `Evaluate`, `Encode` and `Run` own the new raw registry, resolved acyclic graph, pure exception semantics and fragment-specific result. `app/Main.hs` owns line-oriented process I/O. `test/Main.hs` runs frozen-byte goldens, production hardening cases and semantic properties; `test/protocol.py` and `test/exception_protocol.py` exercise persistent executables. The [production request](schema/request.schema.json) and [result](schema/result.schema.json) schemas discriminate both fragments without changing the frozen spike schemas.

## KernelInput/Result v1 decisions

- One UTF-8 JSON request per line yields one canonical UTF-8 JSON response per line. No log text goes to stdout. A request can be at most **1,048,576 bytes excluding the line terminator**; the stream reader drains an overlong line and returns `KDEC002` before processing the next request. JSON container nesting is capped at **64** and `policy.max_nodes` must be **1–1,024**. IDs are counted in the parsed token tree before recursive domain construction; all semantic nodes are checked again after construction.
- All fixed-shape protocol objects have closed fields, including nested source, policy, parser result, diagnostic, provision, requirement, exception, guard and span objects; facts and diagnostic parameters are typed dynamic-key maps. Duplicate JSON object keys, including differently escaped equal keys, fail decoding. `KPROT001` distinguishes protocol version; `KDEC001/002` cover JSON/shape/resource decoding; `KINV001–006` cover missing facts, duplicate IDs, spans, other invariants, missing references and cycles; `KCAP001` covers unsupported fragment or constructor; `KERR001` denotes evaluation inconsistency. Every rejected request has `status=rejected` and no legal rule result; invalid input cannot be interpreted as a negative legal judgment.
- The production fragment **keeps `definitions`**. A provision with `definitions=true` cannot also contain requirements or children. A program with no executable branch must contain an explicitly marked definition provision; it then yields `definition_only` and `status=false`, preserving the frozen semantic contract without accepting an unmarked empty program. A leaf must omit `members`; each `all`/`any` group must have at least one member. Facts are total over leaf IDs and cannot introduce extra names. Semantic IDs are unique across provision and requirement nodes.
- `reference_date` is exactly `YYYY-MM-DD` and must exist in the Gregorian calendar. Parser `accepted=true` cannot coexist with an error-severity diagnostic. An unsupported source version or operation is rejected; the parser diagnostic transport remains a transport fixture, not a new parser.
- Source text is retained as `Text` for identity and as UTF-8 `ByteString` for hashing and spans. Offsets are zero-based, half-open UTF-8 byte offsets; displayed lines and columns are **one-based byte columns**, consistent with the current Tree-sitter convention. Both ends must be UTF-8 code-point boundaries, lie within the source byte length, and agree with the displayed line/column calculated by counting LF bytes. Parent spans contain child spans. This is a v1 policy; changing the editor-facing display convention requires a versioned contract.
- Canonical output explicitly sorts mapping keys and uses compact separators while retaining declaration order in arrays and trace edges. Aeson supplies maintained string/Unicode parsing and string escaping; `Protocol.Json` uses its exposed token stream so duplicate keys are visible before a map can overwrite them. Crypton supplies SHA-256. Properly paired surrogate escapes and non-BMP Unicode are accepted; malformed surrogates are rejected. Canonical IR v1.2 and its hash rules are untouched.

The result is a typed `Either` validation/evaluation flow, with ADTs for result status and provision kind. The exception fragment validates the whole registry, resolves qualified targets to rule keys and rejects cycles before evaluation. It shares one total fact map, reference date and policy across all targets. It evaluates every guard attached to an ordinarily satisfied branch, reports every true exception, keeps declaration order only in traces and distinguishes defeat from failed ordinary requirements. The new fragment result includes per-rule/branch status and reason, exception source/target/status observations and dependency edges. Its [proof-neutral vectors](test/exception-fixtures/PROOF-VECTORS.json) do not select a proof tool. These tests establish bounded protocol and technical semantics, not legal fidelity or a proof of correspondence.

| Capability | Kernel status | Boundary |
|---|---|---|
| `ClosedBooleanBranches-v1` | Implemented; 15 frozen responses remain exact | Total Boolean facts, recursive named groups, inherited branches. |
| `AcyclicGuardedExceptions-v1` | Implemented and synthetic-tested | Closed acyclic registry, same context, simple registered guards and branch defeat only. Valid wire requests currently produce Boolean judgments; unresolved aggregation is tested internally. |
| Typed facts, burdens, penalties, outcomes, CPC and case-law effects | Unsupported | Require later versioned fragments and independent review. |
| New parser, native CLI/LSP, corpus migration or formal proof | Not part of this executable | Existing Python/Tree-sitter owners remain; proof-tool choice is undecided. |

## Toolchain and dependencies

`cabal.project` selects **GHC 9.8.4** and serial builds. The project index state and `cabal.project.freeze` pin the complete resolved dependency graph; `yuho-foundation.cabal` pins each direct dependency exactly. `-Wall -Werror -O1` applies to library, executable and tests; no warning suppression or advanced Haskell extension is used. The only extension is `OverloadedStrings` in modules that need string literals as `Text`.

| Dependency | Why it is here |
|---|---|
| `base` | Standard ADTs, `Either`, traversal and subprocess I/O. |
| `aeson` | Maintained JSON tokenizer, Unicode and string escaping; canonical object order remains explicit in our encoder. |
| `bytestring` | Bounded wire bytes, UTF-8 source bytes and output builders. |
| `containers` | Deterministic fact maps, duplicate-key and duplicate-ID sets. |
| `crypton` | Maintained SHA-256 implementation for source and input digests. |
| `text` | Decoded source, IDs, paths and diagnostic fields. |
| `time` | Real Gregorian calendar-date validation. |
| `QuickCheck` (tests) | Semantic invariants over randomized fact values and JSON key order. |
| `directory`, `filepath` (tests) | Locate repository fixture files without hard-coded absolute paths. |

Transitive packages in the freeze file are pinned because they are required by these direct libraries; they carry no Yuho semantics. The exposed Aeson token API is a deliberate upgrade-review point: changing Aeson requires rerunning duplicate-key, Unicode, depth and canonical-byte tests.

## Reproduce

From this directory, with the pinned GHC/Cabal available:

```sh
cabal v2-build exe:yuho-kernel --jobs=1
cabal v2-test foundation-test --jobs=1 --test-show-details=direct
python test/protocol.py "$(cabal list-bin exe:yuho-kernel)"
python test/exception_protocol.py "$(cabal list-bin exe:yuho-kernel)"
```

The [hardening cases](test/fixtures/CASES.json) are H01–H21; `test/fixtures/generate.py` documents how they derive from the frozen source inputs. H12 is over the request-byte limit and is checked at the subprocess boundary. The [exception cases](test/exception-fixtures/CASES.json) are E01–E40 with a SHA-256 [manifest](test/exception-fixtures/MANIFEST.json); `test/exception-fixtures/generate.py` regenerates them. E35 exercises line draining. The production tests also compare every still-valid frozen spike response byte for byte. See [test evidence](TEST-RESULTS.md) for the checked host and commands.

Before any doctrine-specific exception priority or defeat relation, a new versioned fragment and legal review are required. Typed facts and guarded penalties are not implemented here. Native parser, LSP, proof correspondence and cross-platform packaging gates remain separate from this kernel result.
