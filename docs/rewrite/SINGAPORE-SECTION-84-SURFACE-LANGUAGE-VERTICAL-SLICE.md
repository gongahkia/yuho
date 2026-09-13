# Section 84 surface-language vertical slice

**Status:** bounded research authoring frontend for the reviewed section 84 prototype. The authored [Yuho source](../../research/singapore/section-84-pilot/surface/section84.yh) compiles to the frozen [SuppliedProofStatus-v1 request](../../research/singapore/section-84-pilot/prototype/request.json). This is a frontend slice, not a new kernel variant, Canonical IR version, legal model or production language migration.

## Parser boundary

The [accepted architecture](YUHO-REWRITE-ARCHITECTURE-PROPOSAL.md) treats legacy Yuho v5.1 Tree-sitter acceptance as a migration oracle, not the grammar for new syntax. Its checked-in generated parser also lags some grammar rules, as the [migration contract](MIGRATION-CONTRACT.md) records. This slice therefore uses a closed, task-local [lexer, parser, resolver, checker and lowerer](../../research/singapore/section-84-pilot/surface/frontend.py), while the existing Python parser/AST/Canonical IR and Haskell protocol boundary stay unchanged. This does not establish a general second production parser. Promotion to the selected Haskell production language, editor integration and a general grammar requires a later explicit design and compatibility gate.

The source begins with `model <id> { ... }` and contains exact `variant`, `jurisdiction`, `purpose`, `request`, `policy` and `root` declarations. It has five typed blocks:

| Block | Supported authoring form | Runtime role |
| --- | --- | --- |
| `provenance` | `source`, `mapping_source`, ordered `quote` declarations | Bind exact locked excerpt and mapping IDs; not an authority claim. |
| `annotations` | `burden section107 defence legal balance_of_probabilities;` | Validate contextual metadata; it cannot establish a proof status. |
| `propositions` | Named `leaf`, `all` and `any` declarations, with optional secondary `support` quote | Build one acyclic, source-ordered technical requirement tree and check reviewed support spans. |
| `proof_assignments` | `proved`, `not_proved`, or reasoned `unresolved` for every leaf | Supply classifications externally to the kernel. |
| `limitations` | Quoted, non-executable scope statements | Authoring guidance; excluded from KernelInput and bundle core. |

For example, the authored wrongfulness route is:

```yuho
all g:wrongfulness (f:wrong-causation, f:ordinary-wrongfulness-incapacity, f:contrary-law-incapacity);
```

The parser makes immutable AST nodes carrying token text and one-based line/UTF-8 byte-column positions. Resolution checks exact IDs and references, acyclicity, single tree use and proof-assignment coverage. The type/semantic checker enforces the one reviewed model, variant, scope, source IDs, quote bytes, proposition mapping and contextual annotation vocabulary. Lowering constructs the rule tree and facts from those nodes. It uses the existing locked extraction solely for source bytes and spans, then encodes sorted-key compact UTF-8 JSON with the existing pilot canonical encoder. Compilation writes atomically to a **new** output path; invalid source creates no successful output.

The six short authored quotes must reproduce the locked excerpt bytes and order. Leaves point to named quotes and reviewed proposition IDs. The two wrongfulness leaves additionally name the shared incapacity wording with `support q:wrong_operator`; the checker compares every declared support span with the immutable [mapping](../../research/singapore/section-84-pilot/prototype/mapping.json). Groups and references, including all three incapacity routes and their route-specific causation, come from the authored tree. `all g:wrongfulness` retains both ordinary-standards and contrary-to-law components. Section 107 burden and balance-of-probabilities metadata are validated and copied as annotations; neither the frontend nor the kernel weighs evidence. The immutable [scope](../../research/singapore/section-84-pilot/prototype/scope.json) remains separate. The source file is a repository authoring artifact and is **not** added to the reviewed ModelBundle.

## Reproduction and diagnostics

From the repository root, with `INTAKE_SOURCE_DIR` and `INTAKE_OUTPUT_DIR` set to the locked external input and generated-packet directories:

```sh
python3 research/singapore/section-84-pilot/surface/frontend.py compile \
  --source research/singapore/section-84-pilot/surface/section84.yh \
  --input-dir "$INTAKE_SOURCE_DIR" --packet-dir "$INTAKE_OUTPUT_DIR" \
  --output "$FRESH_PARENT/section84-request.json"
cmp "$FRESH_PARENT/section84-request.json" \
  research/singapore/section-84-pilot/prototype/request.json
```

`FRESH_PARENT` must be an existing, non-symlinked directory; the destination must not exist. Diagnostics are structured JSON on stderr with `code`, source `path`, one-based `line` and byte `column`, and a message. `SFE001` is syntax/UTF-8; `SFE002` duplicate IDs; `SFE003` unknown references; `SFE004` unsupported model/scope/policy; `SFE005` leaf/proposition type; `SFE006` combinator operand or tree shape; `SFE007` root; `SFE008` cycle; `SFE009` assignment coverage; `SFE010` proof status/reason; `SFE011` burden/standard; `SFE012` contextual annotation used as an operand; `SFE013` deferred syntax; `SFE014` source/mapping mismatch; `SFE015` unsafe I/O path; `SFE016` resource limit. Source input is limited to 64 KiB, 4,096 tokens and 256 proposition or assignment nodes. Strings have no escapes; source is strict UTF-8 with LF endings. Unsupported syntax fails closed rather than acquiring implicit semantics.

The compiled request is exactly 7,599 bytes, SHA-256 `1ebe4d4fdd3de643e938c512fafd1c68ed437728b1249d32b6a236639a58d6e2`, with the same no-final-newline convention as the frozen request. The [focused tests](../../research/singapore/section-84-pilot/test/test_surface.py) compile every accepted synthetic assignment case and replay it through the unchanged Haskell kernel. They also assemble and validate a fresh six-file ModelBundle from the compiled request, compare every file with the existing builder's output, and confirm digest `02e51da9fa1bf285eec7cca8b55494c1d6a8e82b9b7e7e300a30b338ecbd404a`. The authored source is excluded, so the earlier [implementation-conformance confirmation](../../research/singapore/section-84-pilot/IMPLEMENTATION-CONFORMANCE-RECORD.json) still names the same bundle digest; it does not review this new frontend's own bytes.

This grammar has no imports, macros, free-form expressions, negation, evidence narratives, temporal selector, offence, exception defeat, presumption rule, penalty, charge, outcome or sentence. It models no facts independently of supplied proof classifications and makes no diagnosis, guilt, conviction, acquittal, fitness, CPC disposition, legal-currency or advice claim. Generalising it beyond this model requires a separate milestone and new tests.
