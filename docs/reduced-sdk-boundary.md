# Reduced experimental SDK: private exact-boundary checks

The reduced SDK is the preferred internal candidate, with no final owner
approval for public distribution. It contains the reviewed 154 regular-file
paths: 120 unchanged library modules, 23 schema/conformance JSON files, two
synthetic-consumer files and nine package/notice/guide resources. No CLI,
research corpus, dataset, mascot pixels or excerpt-dependent tests are included.
Original authorisation and artwork approval remain recorded; no licence choice
is reopened. All admitted experimental profiles and refusals are unchanged.

## Reproduce and inspect

Use GHC 9.8.4, Cabal 3.12.1.0 and the existing prepared dependency cache. From
the checkout, with output paths outside it:

```sh
python3 scripts/reduced_sdk.py build --output /absolute/outside/sdk-a
python3 scripts/reduced_sdk.py build --output /absolute/outside/sdk-b
cmp /absolute/outside/sdk-a/yuho-1.0.0.0.tar.gz /absolute/outside/sdk-b/yuho-1.0.0.0.tar.gz
python3 scripts/reduced_sdk.py verify --archive /absolute/outside/sdk-a/yuho-1.0.0.0.tar.gz
python3 scripts/reduced_sdk.py extract --archive /absolute/outside/sdk-a/yuho-1.0.0.0.tar.gz --output /absolute/outside/extracted
```

The [inventory](../release/reduced-sdk-inventory.json) is explicitly unapproved.
Its complete bytes are pinned in the verifier. The recipe copies only listed
source paths, including four maintained templates under `release/reduced-sdk/`.
It checks source digests before staging and archive path/type/digest membership
after Cabal generation. It refuses extra/missing/changed files, duplicate or
ambiguous names, traversal/absolute paths, unlisted directories and all links
or special files. A matching file count alone proves nothing. The extraction
operation validates all members before writing regular files to a new external
directory; it never follows archive links.

Updating both the source inventory and its explicit code pin requires renewed
review. The pin detects unreviewed data-file drift relative to the reviewed
tool; it is not a signature or protection against an authorised edit to the
tool itself. Neither `owner_approved=false` nor a passing digest check supplies
publication permission. No automatic inventory-refresh/approve option exists.

The 154 paths are unchanged from the independently reviewed proposal. Only the
reduced `yuho.cabal` and `cabal.project.sdk` bytes change: the unused
`research-tests` declaration and assignment are removed. The original full
package still uses that flag to control research tests. Keep the original
dependency freeze; use the reduced template's `development` flag. Consumers of
the earlier private proposal should remove their redundant `-research-tests`
assignment. No dependency, Haskell interface or authoring format changes.

From an extracted root, copy `cabal.project.sdk` to `cabal.project` and build
with `cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4`. Build the
packaged synthetic example as a separate application with a local dependency
on that extracted library. It imports only `Yuho.Authoring` and covers all
admitted profiles, computed provenance and synthetic Unicode source recovery.
It does not replace the complete research verification workflow.

## Content-scoped rights evidence

The external discovery/provenance baseline remains
`experimental-sdk-rights-remediation/rights-matrix.json`, SHA-256
`8309afa44d426669ce4c5223fd21ee70fe699fd068db1ad8962716ef27fc53c9`.
It is a retained review prerequisite, not part of the reduced SDK and not a
licence grant. The [existing evidence policy](../release/rights-content-evidence.json)
is the version-controlled authority for challenged records, retained reviewed
scopes, synthetic portions, original artwork and additional review inputs.
The generated matrix is a derived report, not the sole place to store a new
rights question. Existing archive-membership fields describe earlier review
snapshots; the reduced package keeps its separate exact inventory.

```sh
python3 scripts/rights_inventory.py --input /outside/prior-rights-matrix.json --output /outside/rights-matrix.json --root .
python3 scripts/rights_inventory.py --input /outside/rights-matrix.json --validate-only --root .
```

Full validation is the default. Required identities come from the policy,
independently of the matrix being checked. Every one of the 374 challenged
rows, retained reviewed rows, original assets, synthetic reviews and additional
review owners must be present. Duplicates, same-count substitutions and omitted
reviewed scopes fail. `--partial` is an explicit subset/fixture mode, marked in
its output; it cannot certify full coverage and does not relax correspondence
for records it includes.

Every scope has a deterministic ID qualified by owning origin/path and a stable
policy role or review key. Array order and human-readable labels are not
identities. Namespace, source reference, locator, evidence, category and status
must agree with that scope's authoritative record. Owner-authorisation,
challenge evidence, retained evidence, synthetic/project authorship and unknown
provenance are distinct reference namespaces. Retained descriptions or lists of
URLs stay exact recorded claims, not automatically verified upstream permission.
Unknown provenance uses an explicit unresolved namespace and an unknown marker
or null source reference; no URL is invented. Blank identifiers in a namespace
requiring a reference fail. Current reviewed files, legislative evidence and
owner-authorisation attachments are checked by digest in the CLI. Missing or
changed sources require review rather than automatic scope removal.

### Record an additional unresolved question

Preserve the original derived input containing the question. To propose importing
an additional unknown-source scope into the **same existing policy**, use:

```sh
python3 scripts/rights_inventory.py --input /outside/matrix-with-question.json --record-unresolved --output /outside/proposed-rights-content-evidence.json --root .
```

This writes a policy proposal outside the checkout and does not activate it.
It preserves the supplied locator, source marker, evidence and unresolved status,
and binds the question to its owner file/digest. It does not invent excerpt
locations. The importer currently supports unknown-source questions only; a new
identified external source needs deliberate source/permission review in the
existing policy. The independently reported extra s161 scope is a **synthetic
preservation fixture**, not a new factual allegation about that research file.

Review the proposal, then deliberately update the existing policy and its
`POLICY_SHA256` pin in the tool under normal source review. This is not owner
publication approval. There is no automatic last-write-wins or approval option.
Generate from the recorded input after activation and validate it. Repeated
generation retains scope IDs and all evidence exactly and produces identical
bytes. Unregistered additions, changed evidence/status or conflicting identities
stop generation before output is written. Do not delete an unresolved scope to
make the tool pass. An explicit revision to an existing review key retains its
identity, but conflicting older derived inputs must be deliberately reconciled
or regenerated from the retained raw baseline; they are never silently merged.
Removing a record from the policy while it remains in input also causes a
conflict rather than silently dropping the evidence.

The policy retains all 201 ten-word and 173 six-word-only challenges by path,
digest, content locator and source reference. No statutory paragraphs are
duplicated. Three substantial illustrations and the demonstrated manual-review
passages have separate conditional-legislation scopes; shorter candidates stay
unresolved. The prior conservative scopes for external material are bound
exactly, including the standard Apache licence text's existing permission record.
Original code, synthetic text and separately permitted third-party excerpts
remain distinct. Original mascot authorisation is unchanged. Lexical matches,
recorded references and inventory checks establish traceability, not ownership,
source accuracy, historic collection compliance or redistribution clearance.

Full `make verify` registers both permanent regression scripts. These test the
private boundary without modifying accepted schemas, fixtures or evaluators.
The existing notice checker continues to check notices only; it is not the
reduced allowlist verifier. The [complete bundle](distribution.md) and public
repository/history remain separate surfaces with unresolved source/permission
conditions. No file is deleted and no history is rewritten by this workflow.
