# ModelBundleChangeSet-v1: offline mechanical comparison

**Status:** implemented closed technical report. The [lifecycle decision](MODEL-BUNDLE-UPDATE-LIFECYCLE-DECISION-REPORT.md) remains research evidence; this document resolves its provisional choices against the accepted [ModelBundle-v1](MODEL-BUNDLE-V1.md) validator. The production [schema](../../rewrite/haskell/schema/model-bundle-change-set.schema.json), [Haskell report ADTs](../../rewrite/haskell/src/Yuho/ModelBundle/ChangeSet.hs) and [CLI snapshots](../../rewrite/haskell/test/model-bundle-diff-fixtures/CASES.json) define the executable contract.

## Command, subjects and validation

```text
yuho-model-bundle diff <old-bundle-directory> <new-bundle-directory>
```

Both arguments are complete closed `ModelBundle-v1` directories. The left/right order requests a comparison direction, not chronological or legal succession. The command validates **both** independently with the existing offline package validator, including artifact bytes, SHA-256 digests, lengths, references, semantic-ID scope, UTF-8 spans and detached unsigned reviews. It never trusts a manifest-declared digest without recomputation. It emits no comparison if either fails. It compares the validated snapshots and revalidates both packages before output, refusing detected mutation. As with the v1 package validator, this is not an atomic hostile-filesystem snapshot: a concurrent writer capable of replacing and restoring bytes between reads remains outside the assurance boundary. Operate on immutable, access-controlled copies when that threat matters.

Successful stdout is one compact, sorted-key canonical UTF-8 JSON object followed by exactly one newline. It has `schema: "yuho.model-bundle-change-set/v1"` and `canonical_profile: "yuho.sorted-json/v1"`. Failures put one canonical JSON diagnostic object on stderr and leave stdout empty. No network, Git state, directory name, file timestamp, locale, host identity or current clock enters the report. Differences are successful comparisons, not errors.

## Closed report and classifications

The [schema](../../rewrite/haskell/schema/model-bundle-change-set.schema.json) closes every object and enum. Top-level fields are:

| Field | Meaning |
| --- | --- |
| `old_bundle_digest`, `new_bundle_digest` | Exact independently validated `yuho.model-bundle/v1` core digests. |
| `core_relation` | `identical` iff the two digests match; otherwise `different`. Detached reviews do not affect it. |
| `summary` | Exact `total` row count and counts for all five classifications. |
| `changes` | Deterministically ordered, complete structural rows. |
| `directly_affected_ids` | Sorted IDs with changed positive scope, mappings, mapped source/artifact records or extraction edges, plus changed exclusion IDs. This is review focus, not a legal-effect claim. |
| `wider_downstream_impact` | Always `unknown`: the bundle lacks a complete versioned executable dependency inventory. |
| `review_impact` | Old review IDs non-applicable to a different core digest; new package's applicable, stale and partial asserted-review IDs; `review_authentication: "none"`. |

Every change row has exactly `category`, `identity`, `classification`, `old_record_digest`, and `new_record_digest`. Digests are lowercase SHA-256 or `null` when that side lacks a record. For non-review rows they are `SHA256(ASCII("yuho.model-bundle-change-record/v1") || 0x00 || canonical_record_json)`. For review rows they are SHA-256 of the exact validated detached review-file bytes. An artifact row's `identity` is its validated raw-byte SHA-256; its record digest hashes the descriptor (byte length, media type and role). No row digest authenticates a legal source.

`classification` is exactly `added`, `removed`, `unchanged`, `modified`, or `unknown-relationship`. A stable identity present once on both sides with equal canonical content is unchanged; with differing content it is modified. A one-sided identity is added or removed. `unknown-relationship` explicitly records a group for which no sound cross-bundle pairing exists. It does not assert a rename, equivalence, amendment or legal event. For differing artifact digests, normal added/removed rows remain and an `artifacts/unpaired-digests` row reports that correspondence between unmatched byte identities is unknown. For ambiguous multiple mappings with the same base key, one group row remains unknown rather than guessing which spans correspond.

The closed categories, in output order, are `artifacts`, `legal_sources`, `work_groups`, `expression_groups`, `manifestations`, `derivations`, `semantic_mappings`, `scope`, `executable_model`, `metadata`, and `reviews`. Rows sort by category, identity, classification and digests. Stable keys are artifact digest; source, work, expression and manifestation local ID; child/parent digest pair; mapping `(semantic_id,source_id,role,artifact_digest)` when unique on both sides; scope item kind and ID; the single executable-request slot; core metadata field name; and review ID. Work/expression groups compare sorted source-record membership. The executable row compares the complete validated artifact reference, so it can flag a changed case-specific request without claiming a changed legal model. Set-like scope fields use accepted canonical ordering. Authored arrays *inside* the executable request are compared through the artifact digest and are never resorted.

Different bundle digests make **every old review assertion non-applicable to the new core**, including metadata-only differences. Same digest means the same core, regardless of directory name or detached-review-file changes; a review naming that digest remains applicable to that core if otherwise valid. New package review IDs are reported according to the existing v1 validator, without choosing a favorable outcome or converting an unsigned assertion into approval. A change set cannot renew, transfer or revoke review. New assertions must name the new bundle digest and exact positive coverage. Exclusions do not count as review coverage.

## Resource and failure contract

Each package retains every [ModelBundle-v1 resource limit](MODEL-BUNDLE-V1.md#validation-order-limits-and-result). Comparison is indexed by maps and sets, with sorting; time is O(n log n) in the number of bounded records plus the existing two validation passes, and memory is O(n) for report records. Artifact validation streams hashes in 64 KiB chunks; comparison uses validated descriptors and digests instead of loading both artifact sets.

At most 100,000 change rows may be emitted. The canonical JSON **including its final newline** is capped at 1,048,576 bytes. This is intentionally stricter than the approved 64 MiB ceiling because the existing closed JSON decoder has a one MiB input limit; the comparator must not write a stored change set it cannot decode. Count and byte overflow reject the entire report with `MBCDRES001`, with no truncated success. The schema and Haskell decoder reject unknown fields, unknown classifications, inconsistent counts/digests, duplicate keys and noncanonical arrays; stored change sets are not silently rewritten.

| Exit | Meaning | Stream |
| --- | --- | --- |
| `0` | Both bundles valid and complete report emitted, including identical cores. | Report on stdout; stderr empty. |
| `1` | One or both bundles invalid, or detected snapshot inconsistency. | Side-tagged diagnostics on stderr; stdout empty. |
| `2` | Usage, path or ordinary I/O failure. | Diagnostics on stderr; stdout empty. |
| `3` | Reserved for the existing unmet asserted-review policy; never used by `diff`. | — |
| `4` | Comparator row or output-byte limit exceeded. | `MBCDRES001` on stderr; stdout empty. |

Existing `MB*` validator codes retain their classes. `MBCDUSAGE001`, `MBCDIO001`, `MBCDINV002` and `MBCDRES001` identify comparator usage, I/O, detected mutation and output limits. Error messages omit absolute input paths and operating-system prose. Valid bundle differences do not trigger an error or policy gate.

## Snapshots, compatibility and prohibited interpretations

The [28 synthetic comparison cases](../../rewrite/haskell/test/model-bundle-diff-fixtures/CASES.json) cover equal cores, authoring-order equivalence, detached reviews, changed source metadata/bytes, extraction, source/work/expression/manifestation additions, mapping spans, positive scope in both directions, a changed executable request, ambiguous byte and mapping identity, non-BMP Unicode and CRLF, invalid inputs and resource rejection. Their [manifest](../../rewrite/haskell/test/model-bundle-diff-fixtures/MANIFEST.json) pins fixture bytes; committed `snapshots/DC*.json` pin canonical stdout or stderr. Ordinary tests compare snapshots byte-for-byte and never regenerate them. To deliberately update snapshots after a reviewed contract change, regenerate fixtures explicitly, build the pinned executable, then invoke `python test/model_bundle_diff_protocol.py "$(cabal list-bin exe:yuho-model-bundle)" --update-snapshots` from `rewrite/haskell`; review the full resulting diff before committing.

This operation changes neither `ModelBundle-v1` bytes/digests nor any KernelInput/KernelResult variant, Canonical IR v1.2, parser, production Python or accepted fragment response. Comparing a future bundle version requires an explicit comparator/versioning decision; unknown versions fail the existing validator. No row means enactment, repeal, commencement, supersession, temporal applicability, legal equivalence, reviewed fidelity, approved deployment or safe rollback. Unchanged bytes do not establish continuing legal correctness. URLs remain descriptive locators. The comparator does not fetch sources, inspect deployment state, authenticate review, infer executable dependency edges or issue legal conclusions.

**Resolution of provisional differences:** the prior sketch used `changeset` without a hyphen, a separate success envelope, 16 MiB output, and exit `4`/`5` for invalid new/both packages. The accepted implementation uses the approved `change-set` identifier, a direct successful report on stdout, the stricter shared-decoder one MiB bound, and exit `1` for any invalid side. It omits a speculative change-set digest and detailed legal-event fields; the existing bundle digest remains the only accepted core identity. The earlier research report is preserved unchanged as decision evidence.
