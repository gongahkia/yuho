# ModelBundle-v1: offline package and integrity validator

**Status:** accepted non-executable build/package format, 13 September 2026. This is **not** an eighth KernelInput/KernelResult variant. The seven existing kernel requests, responses and Canonical IR v1.2 digests are unchanged. The normative machine-readable shapes are the [core](../../rewrite/haskell/schema/model-bundle-core.schema.json), [review](../../rewrite/haskell/schema/model-bundle-review.schema.json) and [validation-result](../../rewrite/haskell/schema/model-bundle-validation.schema.json) schemas; the Haskell validator enforces additional cross-record and byte-level invariants.

## Meaning and limits

A bundle identifies exact stored bytes, describes asserted legal-source identities, binds executable semantic IDs to exact UTF-8 text spans, and enumerates the model's positive scope. SHA-256 verifies bytes against a supplied digest. It does not authenticate a publisher, reviewer, court, legal instrument or source URL. A structurally valid bundle is not legally correct, applicable, complete, current or certified. Review assertions are unsigned descriptive claims; `review_authentication` is always `none` in v1. The [research decision](LEGAL-SOURCE-REGISTRATION-DECISION-REPORT.md) and [threat model](MODEL-SCOPE-AND-PROVENANCE-THREAT-MODEL.md) explain why these boundaries are separate.

Only a closed unpacked directory has meaning:

```text
<bundle-root>/
  model-bundle.json
  artifacts/sha256/<64-lowercase-hex-SHA-256>
  reviews/<review-id>.json       # optional directory
```

No archive byte sequence, file metadata, filesystem ordering or URL affects the digest. The validator rejects unexpected entries, symlinks, non-regular files, non-directories where directories are expected, unsafe review names, missing and unreferenced blob files, and duplicate logical entries. It never fetches a URL. Internal artifact paths are derived only from checked lowercase digests; arbitrary or absolute paths are not manifest fields. Offline validation assumes the package directory is not modified concurrently. A future hostile concurrent-filesystem threat model needs an atomic snapshot or descriptor-relative no-follow traversal.

## Core objects and exact digest

`model-bundle.json` has `schema: "yuho.model-bundle/v1"`, `canonical_profile: "yuho.sorted-json/v1"`, `hash_algorithm: "sha256"`, a local `model_id`, `artifacts`, `legal_sources`, `derivations`, `semantic_mappings`, `scope`, and `executable_model`. Every fixed object is closed; duplicate keys reject. JSON is UTF-8, compact, sorted by Unicode object key, with no insignificant whitespace or floating-point values. It uses the existing hardened [JSON encoder and duplicate-key decoder](../../rewrite/haskell/src/Yuho/Protocol/Json.hs), but **not** the Canonical IR v1.2 digest domain and **not** an assertion of RFC 8785 JCS equivalence. The validator rejects noncanonical manifest and review bytes; it does not rewrite them. String bytes, Unicode normalization, line endings and artifact bytes are never normalized.

SHA-256 is pinned in v1. The validator reports:

```text
bundle_digest = SHA256(ASCII("yuho.model-bundle/v1") || 0x00 || canonical_core_bytes)
scope_digest  = SHA256(ASCII("yuho.model-scope/v1") || 0x00 || canonical_scope_bytes)
```

Neither digest is a field inside the core being hashed. Detached review files are outside the core and cannot change either digest. Changing any core field changes the bundle digest. Every artifact descriptor binds its exact raw-byte SHA-256, byte length, media type and role. A changed artifact with an unchanged descriptor fails validation; an updated descriptor changes the core digest. The [synthetic fixture manifest](../../rewrite/haskell/test/model-bundle-fixtures/MANIFEST.json) records byte-level test inputs.

`SourceArtifact` roles are `executable_model`, `source_text`, and `evidence`. `source_text` is only `text/plain; charset=utf-8`; `executable_model` is `application/json`. Evidence may use the listed PDF, HTML, XML, image or text media types. A legal-source record supplies local work, expression/version, manifestation and source IDs; exact artifact digest; source type; language; jurisdiction label; descriptive identifiers, publisher label and locator; and typed asserted dates. Multiple expressions can share one work, and multiple manifestations one expression. A URL is a locator, not content identity. An expression ID cannot switch work or language within one bundle, and manifestation IDs are unique. Dates must be real ISO Gregorian dates. An asserted `effective_from` cannot follow `effective_to`; publication cannot follow supersession. No date comparison establishes legal applicability.

An `ArtifactDerivation` names an exact child text artifact and parent artifact digest, plus descriptive tool name, version and configuration. Use the literal `not_recorded` if a recipe detail is unavailable; absence is not proof of repeatability. Edges are sorted, unique and acyclic. An extracted text is a separate content-addressed artifact. Keep the original PDF, HTML, XML, OCR input or other acquisition bytes separately; point spans only to the exact derived UTF-8 text. No HTML entity decoding, OCR fidelity check, normalization or parent/child text comparison is performed by this validator. A derivation record does not prove extraction accuracy or source authority.

Every `SemanticSourceMapping` binds one exact executable semantic ID to a registered legal-source record, the same registered `source_text` digest, a typed role and a half-open span. Mapping roles describe relationships only; they do not execute law. Offsets are exact UTF-8 bytes. Start/end must land on UTF-8 boundaries, be within the stored bytes, and agree with one-based line and **byte-column** positions under the existing [span validator](../../rewrite/haskell/src/Yuho/Core/Source.hs). Multiple mappings for one semantic ID are allowed and retain their sorted entries. Mapping correctness beyond byte consistency is review work.

The `ModelScopeManifest` uses only `coverage_mode: "enumerated_only"`. It lists the exact positive semantic IDs extracted from the executable model artifact, exact source IDs and expression IDs, stable exclusion IDs and reasons, limitations, unsupported capabilities, jurisdiction and subject-matter labels, and an explicitly tagged temporal context. Exclusions are outside positive scope and never count as review coverage. The validator requires the sorted positive semantic-ID inventory to equal the model's registered rule/provision/requirement/exception/presumption/penalty/term IDs and the set of mapped IDs; it rejects extra or missing IDs. It uses the seven existing **static** kernel decoders/validators, not a rule evaluation. For v1 the executable artifact is a complete canonical `yuho.kernel-input/v1` `evaluate` request, so it includes a frozen synthetic or case-specific fact context. A future reusable model template requires its own versioned artifact profile. The bundle validator checks the request's inline source text SHA-256 against the registered exact `source_text` artifact. It does not alter the request or pass a new bundle field into KernelInput.

Set-like arrays are canonical: artifacts by digest; legal-source records by source ID; semantic mappings by semantic ID, digest, start and end; derivations by child then parent digest; scope IDs and other set-like label arrays lexically; exclusions by exclusion ID; review purposes and covered IDs lexically. Arrays representing authored source order inside the pinned executable request remain unchanged. Sorted JSON mapping keys never justify reordering those semantic arrays.

## Detached unsigned review assertions

Each optional `reviews/<review-id>.json` names an exact bundle digest and scope digest, a nonempty closed purpose list (`source_fidelity`, `semantic_fidelity`, `scope_completeness`, `jurisdictional_applicability`), explicit positive coverage by exact scope digest or enumerated semantic/source IDs, limitations, outcome, UTC timestamp, and descriptive reviewer identity/role. Outcomes are `asserted_acceptable`, `changes_required`, or `informational`. Names, roles, organisations and qualifications are supplied text, not authenticated credentials. The purpose label does not establish competence, independence or completion.

A review whose bundle or scope digest differs is **stale/non-applicable**, not silently transferred to the current core. A review covering only some current IDs is partial. Unknown current IDs in an otherwise applicable review reject structurally; a historical stale assertion can retain IDs from its former bundle. The optional `--require-asserted-review-purpose` policy succeeds only when an applicable `asserted_acceptable` assertion positively covers the requested purpose and full current scope. Source-ID-only coverage can satisfy `source_fidelity`, not `semantic_fidelity`. This policy checks an **assertion exists**; it does not authenticate the reviewer or certify the model. Empty `reviews/` is valid for basic structural validation. A future signed attestation may wrap the bundle digest without changing core bytes.

## Validation order, limits and result

Run `yuho-model-bundle validate <bundle-directory>`; optionally add `--require-asserted-review-purpose <purpose>`. The validator checks package entry types/inventory, bounded canonical JSON and closed shapes, structural references/counts/ordering, streaming artifact hashes and lengths, the pinned model's static validation and semantic-ID inventory, source-binding and UTF-8 spans, then detached reviews. No rule is evaluated and no network request occurs. It emits one deterministic canonical `yuho.model-bundle-validation/v1` JSON line. `status` is `valid`, `invalid`, `policy_unmet`, or `io_error`; diagnostics have stable code/path/message. `bundle_digest` and `scope_digest` are present only after valid core validation. `applicable_asserted_reviews`, `stale_reviews` and `partial_reviews` are sorted ID lists; `review_authentication` remains `none`.

Exit codes: `0` valid and requested assertion policy met; `1` structurally invalid bundle; `2` usage, path or I/O failure; `3` structurally valid but requested asserted-review policy unmet. A rejection yields no partial legal judgment or kernel response. Missing online sources are irrelevant to offline validation when pinned artifacts are present.

Limits: manifest 1 MiB; each review 1 MiB; at most 64 reviews, 256 artifacts, 32 MiB per artifact, 128 MiB combined declared artifact bytes, 1,024 source records, 8,192 mappings, 8,192 positive semantic IDs, 1,024 exclusions, 4,096 derivations and JSON metadata depth 16. The executable request retains its own 1 MiB kernel JSON limit. Artifact hashing streams 64 KiB chunks; span-bearing text is read one artifact at a time after size validation. `MBRES001` reports limits, `MBDEC001/002` malformed/noncanonical JSON, `MBINV001` structural/reference/integrity failures, `MBCAP001` unsupported profiles, `MBPKG001` unsafe package entries, `MBIO001` I/O, and `MBUSAGE001` command usage. No code means `not_satisfied` or legal uncertainty.

## Lifecycle and assurance boundary

1. Acquire a source manifestation and freeze its exact bytes.
2. Optionally derive exact UTF-8 text as a separate blob with descriptive lineage.
3. Register work, expression, manifestation and artifact assertions.
4. Map each executable semantic ID to exact text bytes and span.
5. Declare an enumerated positive scope and explicit exclusions.
6. Validate offline and compute the bundle/scope digests.
7. Obtain detached review assertions naming those exact digests.
8. Optionally check an asserted-review purpose under the limited policy above.
9. Pass the existing executable request artifact to the unchanged kernel through its existing protocol.

The accepted [criminal-outcome boundary](CRIMINAL-OUTCOME-BOUNDARY-DECISION-REPORT.md) still applies: model scope and review labels do not turn technical branch satisfaction into conviction, acquittal or sentence. Authentication, trust roots, reviewer authorisation, official acquisition, source updates, legal applicability, completeness and legal fidelity require later independent boundaries and jurisdiction-specific review.
