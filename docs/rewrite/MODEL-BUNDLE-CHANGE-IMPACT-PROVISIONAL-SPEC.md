# ModelBundleChangeSet-v1: provisional offline comparison specification

**Status:** proposed format and test contract, 13 September 2026; **not implemented or accepted**. Read the [lifecycle decision](MODEL-BUNDLE-UPDATE-LIFECYCLE-DECISION-REPORT.md) and existing [ModelBundle-v1](MODEL-BUNDLE-V1.md) assurance limits first. This specification adds no legal event, kernel rule, source fetch, authenticated review or deployment action.

## Operation and exact subjects

Propose one command:

```text
yuho-model-bundle diff <old-bundle-directory> <new-bundle-directory>
```

`diff` is sufficient; a separate `impact` verb would risk implying a stronger semantic analysis. Run the existing offline `validate` logic on **each** closed package independently, without an asserted-review-purpose policy. Pin/snapshot each validated core and review-file inventory for the duration of comparison; refuse unsafe paths, symlinks and concurrent byte changes rather than following mutable directory contents after validation. Compute the existing `yuho.model-bundle/v1` digest for each core. Compare only if both validate. Neither bundle is rewritten and no URL is fetched. The left/right order is a requested comparison direction, **not** chronological, legal or deployment succession. Comparing two directories with equal core digests is valid; their detached review inventories may still differ.

The generated closed record is `yuho.model-bundle-changeset/v1`; the CLI result is `yuho.model-bundle-diff-result/v1`. If retained as an artifact, compute `changeset_digest = SHA256(ASCII("yuho.model-bundle-changeset/v1") || 0x00 || canonical_change_set_bytes)` with no self-digest field in the hashed bytes. Use the pinned `yuho.sorted-json/v1` encoder, duplicate-key rejection and deterministic arrays. The change set binds both exact core digests **and** SHA-256 inventories of the exact detached review files compared, because a later review-file change should alter this report while leaving both bundle digests unchanged. No ambient timestamp, directory name, inode, mtime, Git commit, locale or network response enters the record. The report is a comparison artifact, not a revision or supersession assertion.

## Comparison keys and categories

Use `unchanged`, `added`, `removed`, `modified`, and `unknown_relationship` only for **structural** records. `modified` requires an exact, unambiguous stable *local* key in both cores; it never means a legal amendment. A matched local key is still an unverified cross-bundle identity assertion. Do not pair objects by fuzzy text similarity, section number, URL, title or nearby span. The absence of a matching key is `removed` plus `added`, with relationship unknown if a human might assert continuity.

| Collection | Alignment and comparison | Required observation |
| --- | --- | --- |
| Source artifacts | Key by raw SHA-256 digest; compare descriptor role/media/length for retained digest. | Added/removed/retained digest sets; a changed byte stream is a removed digest plus added digest, **not** an inferred replacement. A retained digest with changed role/media/declared length is a descriptor modification if both bundles validate; neither role is silently preferred. |
| Legal-source records | Key by `source_id`; compare every closed field, including work/expression/manifestation IDs, artifact digest, locator, language, jurisdiction, identifiers and dates. | Added/removed/modified/unchanged records with exact changed field names. Do not infer official continuity from an unchanged ID. |
| Work/expression/manifestation groupings | Derive groups solely from validated source records and compare exact local IDs and their sorted member/source IDs. | Group membership/metadata differences; changing an ID yields added/removed and `unknown_relationship`, not an inferred rename or legal version. |
| Extracted-text derivations | Key by exact `(child_digest,parent_digest)`; compare tool/version/configuration for retained edge. | Added/removed/modified edges; source-order has no significance. A different child digest or tool recipe is an extraction/lineage difference, not proof of different law. |
| Semantic mappings | Compare the sorted multiset of `(semantic_id,source_id,role,artifact_digest,span)` tuples. Pair by `(semantic_id,source_id,role,artifact_digest)` **only when exactly one tuple on each side**. | Exact added/removed tuples; `span_only` when that sole pair differs only in span; otherwise an ambiguous group is `unknown_relationship`. Multiple mappings for one ID are legal and must not be collapsed. |
| Semantic IDs and positive scope | Compare validated sorted `scope.semantic_ids`, `source_ids`, `expression_ids`, exclusions by `exclusion_id`, limitations, unsupported capabilities, jurisdiction/subject labels and temporal context. | Added/removed/retained IDs; changed exclusion reason and changed scope field values. An exclusion never becomes positive coverage. |
| Executable model | Compare `executable_model` fragment, format and artifact digest; optionally show exact JSON-pointer changes only if a bounded, versioned structural differ is specified. | Whole executable-request digest equality/difference. It includes case-specific facts and policy in v1, so a changed digest must **not** be labelled a legal model change without distinguishing these fields. Do not compare fixture outputs as equivalence proof. |
| Reviews | Compare canonical review-file SHA-256 by `review_id` within each validated package. | Added/removed/changed file assertions, plus separately computed subject applicability, coverage and outcome. Review bytes are outside both core digests. |

The summary must separately name retrieval, artifact, extraction, manifestation, expression, work, mapping, executable-request, scope, metadata and review differences. `retrieval_changed` may be reported only as changed *recorded locator/retrieval metadata*, not a claim about what an online endpoint currently serves. `legal_event`, `deployment_change` and `rollback` are **never** computed categories.

## Conservative semantic-ID review focus

Let `old_ids` and `new_ids` be the exact positive inventories, and `retained = intersection`. For every ID, emit distinct fields rather than one misleading `affected` Boolean:

* `added_ids`, `removed_ids`: exact set differences, not an inference of enactment/repeal.
* `direct_record_change_ids`: retained IDs whose own mapping multiset changed, whose mapped text artifact/source record changed, or whose mapped text's validated derivation ancestor set/recipe changed. This is **review focus**, not an established effect on the rule's evaluation.
* `byte_evidence_unchanged_ids`: retained IDs whose mapping tuples, mapped bytes/source record/derivation ancestry and **whole executable request digest** are identical. This says only those checked bytes/records match; a changed scope, external law or earlier review could still matter.
* `model_change_impact_unknown_ids`: **all retained IDs** when executable-request digests differ, unless a future versioned, complete dependency extractor proves a narrower conservative relation. A source-only change with identical model bytes may still alter legal fidelity; it is not automatically harmless.
* `unknown_relationship_ids`: IDs for which cross-bundle identity or many-to-many mapping pairing cannot be established from exact keys. Do not invent a rename, even if text matches.

The derivation-ancestor comparison is a bounded traversal of the existing acyclic artifact-derivation graph, not the legal-rule graph. The Haskell validators check rule/exception/presumption references within each request, but [`semanticIds`](../../rewrite/haskell/src/Yuho/ModelBundle/Validate.hs) exports only a sorted inventory, not a complete versioned graph over definitions, inherited requirements, exception targets, presumption conditions, penalty guards and term containment. The v1 comparison therefore **does not propagate semantic impact** through those references. For a changed model request, conservatively mark all retained IDs as unknown. An optional future reference extractor must be complete for each closed fragment, reject missing edges/cycles, bound reverse reachability and test against both memoized and reference evaluators before narrowing that set. Comparing similar JSON nodes or passing fixture outputs is not semantic equivalence.

## Review-impact algebra

1. Classify each package's own review assertions under its *own* validated bundle/scope digest, using existing `applicable`, `stale`, `partial`, outcome and purpose rules. Preserve all review IDs in sorted order; do not choose the favorable assertion.
2. If `old_digest != new_digest`, **no old assertion applies to the new bundle**, regardless of `scope_digest`, shared IDs or size of change. Report `old_reviews_non_applicable_to_new` for every old review. A copied old file in the new directory is stale by subject. A metadata-only core change is enough.
3. If digests are equal, an old assertion naming that digest remains applicable *to that core* even if absent from the new directory; package-local review inventory and external availability are separate observations. Review-file additions/removals never alter core identity.
4. Report new-package `applicable_asserted_reviews`, `stale_reviews`, `partial_reviews`, `missing_purposes`, `changes_required_reviews`, and `conflicting_assertions` without converting any into approval. Two applicable assertions with opposed `asserted_acceptable` and `changes_required` outcomes for the same purpose/overlapping coverage are a conflict for human policy, not an invalid core. All remain `review_authentication: "none"`.
5. Current [ReviewAssertion-v1](../../rewrite/haskell/schema/model-bundle-review.schema.json) has no change-set, prior-bundle, expiry or revocation field. A new reviewer may assert coverage only by issuing a new v1 assertion naming the **new** bundle/scope digests, exact purpose/IDs and limitations. If a later workflow must cite old digest or change-set digest, use a separately versioned review-context/ReviewAssertion-v2 object; those citations are context, never transferred coverage. Do not mutate v1 schema or infer revocation from a removed file.

`missing review`, `partial review`, `stale review`, `changes_required`, `conflicting unsigned assertions` and `revoked review` are distinct. The last cannot be established in v1: authentication and trusted revocation require a later policy. A change set itself is never a review assertion or legal sign-off.

## Proposed closed shape and ordering

Illustrative **schema sketch**, not accepted production JSON:

```json
{
  "schema": "yuho.model-bundle-changeset/v1",
  "canonical_profile": "yuho.sorted-json/v1",
  "old_bundle_digest": "<64 lowercase hex>",
  "new_bundle_digest": "<64 lowercase hex>",
  "old_review_files": [{"review_id": "review:old", "sha256": "<64 lowercase hex>"}],
  "new_review_files": [],
  "changes": {
    "artifacts": {"added": [], "removed": [], "unchanged": [], "modified": [], "unknown_relationship": []},
    "source_records": [], "work_groups": [], "expression_groups": [],
    "manifestation_records": [], "derivations": [], "semantic_mappings": [],
    "scope": [], "executable_model": [], "metadata": [], "reviews": []
  },
  "id_review_focus": {
    "added_ids": [], "removed_ids": [], "direct_record_change_ids": [],
    "byte_evidence_unchanged_ids": [], "model_change_impact_unknown_ids": [],
    "unknown_relationship_ids": []
  },
  "review_impact": {
    "old_reviews_non_applicable_to_new": [], "new_applicable": [],
    "new_stale": [], "new_partial": [], "missing_purposes": [],
    "changes_required": [], "conflicting_assertions": [],
    "review_authentication": "none"
  }
}
```

Use a separate closed `yuho.model-bundle-diff-result/v1` envelope with `status`, optional `changeset_digest`, optional complete `change_set`, and ordered diagnostics; no partial change set on failure. `status` values: `compared`, `invalid_old`, `invalid_new`, `invalid_both`, `io_error`, `unsupported_comparison`. Unknown fields and duplicate keys reject. The final schema must define every nested row, exact discriminators and mutually exclusive status shapes; the sketch above must not be accepted as an arbitrary extension map.

Ordering: record families in fixed schema order; set-like ID/digest arrays lexicographically; source/work/expression/manifestation rows by local ID; mapping rows by `(semantic_id,source_id,role,artifact_digest,start,end)`; derivation rows by `(child,parent)`; review rows by ID and file digest; diagnostic rows by input side (`old`, then `new`) and stable path. Source-ordered arrays **inside the executable artifact** retain authored order and are compared as bytes/JSON arrays, never sorted for a diff. Render compact sorted-key JSON plus one newline. If either package changes between validation and comparison, fail rather than emit a potentially inconsistent result.

## Diagnostics, exits and resource envelope

Proposed exits, distinct from the existing `validate` operation:

| Exit | Meaning | Output |
| --- | --- | --- |
| `0` | Both validated and complete comparison emitted, including equal digests. | `compared` and a complete change set. |
| `1` | Old package invalid, new valid. | `invalid_old`; no partial change set. |
| `4` | New package invalid, old valid. | `invalid_new`; no partial change set. |
| `5` | Both packages invalid. | `invalid_both`; side-tagged diagnostics, no change set. |
| `2` | Usage, path, snapshot or I/O failure on either side. | `io_error`; side-tagged code, no change set. |
| `3` | A recognized but unsupported bundle/compare profile or policy request. | `unsupported_comparison`; no change set. |

Validate both sides independently before deciding `1/4/5`; an I/O or unsupported-profile failure must identify its side and not masquerade as `invalid`. Reuse existing stable `MB*` validator diagnostics as nested side-tagged causes, plus a separately versioned `MBCD*` family for comparison-specific limit, snapshot and shape failures. Neither invalidity nor absent review yields a negative kernel judgment. Do not expose absolute filesystem paths or non-deterministic OS error prose in canonical diagnostics.

Retain all individual ModelBundle-v1 limits on **each** input: manifest/review 1 MiB each, 64 reviews, 256 artifacts, 32 MiB per artifact, 128 MiB combined artifacts, 1,024 source records, 8,192 mappings/positive IDs, 1,024 exclusions, 4,096 derivations, depth 16. Additional comparison limits: at most 512 distinct artifact digests, 2,048 source-record IDs, 16,384 mapping rows, 16,384 semantic IDs, 8,192 derivation edges, 128 review files and 32,768 total emitted change rows; canonical change-set bytes and result bytes each at most **16 MiB**, nesting depth 16. Refuse rather than truncate if a bound is exceeded. Stream artifact validation through the existing 64 KiB hasher; comparison should normally use validated digests and bounded core metadata, not reload both 128 MiB artifact sets in memory. A future reference-closure extractor would need its own declared ≤32,768-edge cap and proof of completeness. These figures are technical limits to test on the constrained host, not legal or corpus thresholds.

## Synthetic fixture and property matrix

Use a new independent comparison family, retaining MB01–MB72 unchanged. Pair only synthetic, validated bundles for successful comparisons. Minimum accepted cases: identical core in different directory names; same core with added/removed review; metadata-only change; locator change with same bytes; artifact substitution with changed digest; added/removed evidence artifact; changed extraction recipe with same text; changed extracted text/CRLF/Unicode; changed source/work/expression/manifestation records; changed date label; added/removed/same semantic ID; one-to-many mapping and unambiguous span-only change; changed scope exclusion/limitation; changed executable facts/policy with same semantic IDs; changed declaration order; multiple review purposes; fresh new-digest assertion; partially covered and conflicting unsigned reviews; branch-like comparisons sharing an old digest; reverse-order comparison. Keep legal-event labels absent.

Minimum rejected/unknown cases: invalid old, invalid new and both invalid; digest mismatch, mutation during comparison, missing historical directory, symlink/traversal, unsupported profile, output and count overflow; stale review copied into new directory; same ID with changed meaning; different IDs with identical text; ambiguous mapping pairing; changed model with undetected downstream reference; claimed renumbering without a supplied identity relation. No corpus amendment or SSO page is a normative fixture.

Bounded properties: deterministic canonical bytes and digest; directory/mtime independence; same core digest despite review changes; changed core field changes digest (within generated cases); old-review non-transfer for every unequal digest; exact equal-digest applicability; symmetric structural sets under reversed pair with directional add/remove swap; no fuzzy rename; complete positive-scope mapping inventory; exact UTF-8/artifact boundaries inherited from validation; bounded derivation-ancestor traversal; changed whole-model digest never yields a claimed complete narrow impact set; deterministic diagnostics; invalid input never produces a change set; output limit refusal; all 318 accepted kernel responses remain byte-identical. A change set test proves technical comparison behavior only, not refinement, legal amendment, legal applicability or reviewed fidelity.

## Prohibited interpretations and implementation gate

Do not label the right side “current law,” “legally effective,” “approved successor” or “newest” merely because it is the second argument. `unchanged` means exact compared fields/bytes match; it does **not** mean a provision remains legally correct. `added`/`removed` do not mean enactment/repeal. `span_only` does not mean harmless formatting. `unknown_relationship` is not semantic `unresolved`. A `changeset_digest` authenticates neither acquisition nor reviewer. A retrieved page changing, an ELI amendment relation, an Akoma Ntoso lifecycle event, or a PROV revision assertion must be recorded as supplied material and reviewed separately before being described as a legal event.

Before implementation, approve the closed row schema, status/exit matrix, side-tagged diagnostics, finite limits, snapshot strategy, review-file snapshot digest policy, and explicit comparison wording. If the comparator cannot stably snapshot both packages or its output cannot fit safe limits without truncation, defer or narrow the result; do not weaken accepted ModelBundle-v1 or kernel bytes to accommodate it.
