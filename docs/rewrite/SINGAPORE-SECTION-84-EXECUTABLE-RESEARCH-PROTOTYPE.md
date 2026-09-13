# Section 84 bounded executable research prototype

## Decision and review boundary

The maintainer accepted the existing [section 84 authority research](SINGAPORE-SECTION-84-AUTHORITY-AND-TEMPORAL-RESEARCH.md), [locked source intake](SINGAPORE-SECTION-84-SOURCE-INTAKE-REPORT.md) and [qualified-review record](../../research/singapore/section-84-pilot/QUALIFIED-REVIEW-RECORD.json) as sufficient to implement a bounded research prototype. This milestone uses those already reviewed materials; it does not make a new online source-acquisition check a prerequisite. The reviewer’s reported written confirmation covers the research baseline `c057fb84000265b412d1b6ca3d050e7b2a1d5eca` and proposed structure, subject to documented limits. It is unsigned, the reviewer’s identity is withheld, and qualification is maintainer-attested. No reviewer inspected or signed the new executable bytes or ModelBundle digest. Implementation-conformance confirmation is pending.

The [executable request](../../research/singapore/section-84-pilot/prototype/request.json) uses the existing `SuppliedProofStatus-v1` KernelInput variant. Its technical result is `satisfied`, `not_satisfied` or `unresolved`, with all supplied statuses and traces retained. This is **not** a finding on criminal responsibility, an offence, guilt, conviction, acquittal, diagnosis, fitness, CPC procedure or sentence. No anchor offence, including Penal Code s 323, is present. No new kernel variant, schema, Canonical IR rule, parser boundary or production Python behavior is introduced.

## Exact scope and proposition graph

The [scope declaration](../../research/singapore/section-84-pilot/prototype/scope.json) identifies `SingaporePenalCodeSection84Post2022ResearchPrototype-v1`, jurisdiction Singapore, Penal Code 1871 s 84, reviewed post-1-March-2022 statutory structure, expression effective-from `2022-03-01`, research cutoff `2026-09-13`, and intended use `research_prototype`. It records no case-specific expression selection, evidence assessment, diagnosis, offence determination, court outcome or legal advice. It makes no open-ended `valid_to` claim. The caller must select an applicable expression outside the kernel; the protocol’s `reference_date` is a technical input field, **not** a legal temporal selector.

The candidate graph is a technical transcription of the reviewed [proposition matrix](../../research/singapore/section-84-pilot/PROPOSITION-REVIEW-MATRIX.json), [temporal matrix](../../research/singapore/section-84-pilot/TEMPORAL-APPLICABILITY-MATRIX.json) and [review brief](../../research/singapore/section-84-pilot/QUALIFIED-REVIEW-BRIEF.md):

```text
unsoundness at the time of the act
AND (
    nature-of-act incapacity AND nature-route causation
    OR
    ordinary-standards incapacity AND contrary-to-law incapacity
        AND wrongfulness-route causation
    OR
    complete-control incapacity AND control-route causation
)
```

Every incapacity leaf is expressly a classification **at the legally relevant act time**. Each route has its own externally classified `by reason of unsoundness of mind` causal relationship, so causation proved for one route cannot combine with incapacity proved only on another route. The shared unsoundness-at-time leaf is separate. This decomposition requires eight external classifications; Yuho does not infer any of them from diagnosis or narrative evidence. The two wrongfulness components are conjunctive for the s 84(1)(b) route. The model retains both s 84(1)(b)’s incapacity operator and s 84(2)’s component text in the [source mappings](../../research/singapore/section-84-pilot/prototype/mapping.json). The graph does not execute the statutory words “Nothing is an offence” as an offence or disposition conclusion.

| Kernel leaf | Reviewed proposition | Required external classification |
| --- | --- | --- |
| `f:unsoundness-time` | P84-02 and P84-03 context | Unsoundness at the act time. |
| `f:nature-incapacity` | P84-04 | Incapacity to know nature of the act at that time. |
| `f:nature-causation` | P84-03 | Nature-route incapacity by reason of that unsoundness. |
| `f:ordinary-wrongfulness-incapacity` | P84-05, P84-06 and P84-08 | Incapacity to know ordinary-standards wrongfulness at that time. |
| `f:contrary-law-incapacity` | P84-05, P84-07 and P84-08 | Incapacity to know wrongfulness contrary to law at that time. |
| `f:wrong-causation` | P84-03 | Both wrongfulness incapacity components by reason of that unsoundness. |
| `f:control-incapacity` | P84-09 | Complete deprivation of control at that time. |
| `f:control-causation` | P84-03 | Control-route deprivation by reason of that unsoundness. |

The source-span mapping is textual support for the proposed graph, not proof of a legal interpretation. The original proposition matrix preserves its evidence classifications and unanswered per-proposition review questions. The broad written confirmation authorizes this bounded construction but is not recast as eight individual answers.

## Proof and Evidence Act boundary

Each leaf has a required externally supplied `proved`, `not_proved` or reasoned `unresolved` status. The kernel projects these to technical satisfaction without assessing testimony, experts, medical records, credibility, truth or evidential sufficiency. `not_proved` means non-establishment in the supplied classification; it does not prove factual negation. `unresolved` is not a court disposition.

The declared per-leaf `defence`/`legal` burden and `balance_of_probabilities` standard are **contextual validation annotations** repeating the reviewed general-exception burden context, not eight independent burden-allocation rulings. The kernel checks a supplied annotation against the declaration and rejects a mismatch with `KINV007`; a matching annotation supplies no proof. The [authority research](SINGAPORE-SECTION-84-AUTHORITY-AND-TEMPORAL-RESEARCH.md) keeps Evidence Act s 107’s accused-side general-exception burden and presumption of absence distinct from the prosecution’s ultimate beyond-reasonable-doubt charge burden. This prototype has no charge or offence elements, does not adjudicate either burden, and does not encode s 107 as a `RegisteredPresumptionDerivations-v1` route.

## Reproducible bundle

The offline [builder](../../research/singapore/section-84-pilot/prototype/pilot.py) verifies the existing [SOURCE-LOCK.json](../../research/singapore/section-84-pilot/SOURCE-LOCK.json) against three immutable browser-saved HTML files and all eight generated-packet artifacts. It reproduces the committed request, mapping and scope from the locked Penal Code extracted-text bytes. The committed request embeds six short exact statutory substrings and a separate synthetic status-source line; it does not commit the full browser page or full extracted statute. A fresh closed bundle contains five content-addressed artifacts: the canonical executable request, the locked Penal Code HTML evidence artifact, the exact UTF-8 section 84 extraction, the selected excerpt, and the synthetic status-source text. Four descriptive source records link the artifacts; two derivation records link extracted text to HTML and excerpt to extracted text. Fifteen executable semantic IDs have 17 exact text-span mapping records. The two extra mappings bind each wrongfulness leaf to s 84(1)(b)’s incapacity wording as well as its s 84(2) component. Bundle scope enumerates those IDs, the source records, expression identifiers and exclusions.

The bundle builder checks exact locks and static artifact bytes before writing, assembles in a fresh temporary directory, invokes `yuho-model-bundle validate` offline, checks the returned digest, and publishes only after success using Linux `renameat2` with no-replace semantics. A failed build leaves no destination. The validated canonical digest is:

```text
02e51da9fa1bf285eec7cca8b55494c1d6a8e82b9b7e7e300a30b338ecbd404a
```

This is SHA-256 over `yuho.model-bundle/v1`, a zero byte, and the canonical bundle-core manifest bytes. A review assertion is **not** included. Structural validity and matching hashes identify the frozen bytes; they do not authenticate source origin, certify current law, establish case applicability or approve this implementation for production. The browser capture’s labels and the earlier Gazette research remain described in the [source intake](SINGAPORE-SECTION-84-SOURCE-INTAKE-REPORT.md) and [authority register](../../research/singapore/section-84-pilot/AUTHORITY-REGISTER.json). Redistribution permission for captured source material remains unresolved; full source bytes stay outside Git.

Run from the repository root, after setting `INTAKE_SOURCE_DIR` and `INTAKE_OUTPUT_DIR` to the immutable external source and generated-packet directories and obtaining the existing pinned Haskell binaries:

```sh
python3 research/singapore/section-84-pilot/prototype/pilot.py verify-artifacts \
  --input-dir "$INTAKE_SOURCE_DIR" --packet-dir "$INTAKE_OUTPUT_DIR"
"$YUHO_KERNEL_BIN" < research/singapore/section-84-pilot/prototype/fixtures/requests/X01-nature.json
python3 research/singapore/section-84-pilot/prototype/pilot.py run-synthetic \
  --input-dir "$INTAKE_SOURCE_DIR" --packet-dir "$INTAKE_OUTPUT_DIR" \
  --request-path research/singapore/section-84-pilot/prototype/fixtures/requests/X01-nature.json \
  --kernel "$YUHO_KERNEL_BIN"
python3 research/singapore/section-84-pilot/prototype/pilot.py build-bundle \
  --input-dir "$INTAKE_SOURCE_DIR" --packet-dir "$INTAKE_OUTPUT_DIR" \
  --destination "$FRESH_PARENT/bundle" --validator "$YUHO_BUNDLE_BIN"
"$YUHO_BUNDLE_BIN" validate "$FRESH_PARENT/bundle"
```

`FRESH_PARENT` must exist and `bundle` must not. Each request is one canonical JSON object; send one trailing newline to the persistent kernel protocol. The pilot `run-synthetic` command additionally checks that the request differs from the committed model only in its exact synthetic proof-status values and three-character request ID; an altered policy date, narrative field or model declaration is outside this pilot scope. The stored baseline request classifies every leaf as reasoned `unresolved`. The [fixture manifest](../../research/singapore/section-84-pilot/prototype/fixtures/CASES.json) lists 12 accepted technical results (including that baseline) and 12 rejected requests with committed canonical snapshots. Results expose complete ordered traces and preserve supplied statuses separately from technical projection. Rejected requests contain no partial rule result. Existing kernel input and bundle resource limits apply unchanged.

## Review transfer and next gate

The baseline qualified review does not transfer to the new digest. A later narrow implementation-conformance confirmation should inspect the exact committed request, mappings, synthetic cases, limitations, and validated bundle digest. It may then provide a new, accurately scoped review assertion for those exact bytes, with the same unsigned/authentication limits unless a separate authentication mechanism is introduced. This prototype does not perform that human confirmation or add any autonomous Singapore-law outcome.
