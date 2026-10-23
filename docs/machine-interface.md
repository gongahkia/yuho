# Local machine interface

Start with the [compiler guide](compiler-guide.md), then the
[language workbench](language-workbench.md). The existing native commands and
[source composition](source-composition.md) remain authoritative. This interface is
an opt-in local control envelope, not a new kernel protocol or universal authoring
format. It uses the same built executable's existing commands with argument arrays;
it does not invoke a shell or provide a service. Python is only a sample client.

## Command and schemas

```sh
# From the checkout, in the pinned GHC 9.8.4 / Cabal environment:
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
YUHO="$(cabal list-bin exe:yuho --offline --with-compiler=ghc-9.8.4)"
# Paths in requests resolve against the process working directory, not the request file.
printf '%s\n' '{"format":"yuho.machine-request/v0.1-experimental","input_kind":"native-yh","operation":"inspect","path":"examples/source-composition/proof/relationship.yh","scenario":"examples/source-composition/proof/true.yh","stage":"all"}' | "$YUHO" machine -
# Alternatively: "$YUHO" machine /absolute/request.json
```

[Request schema](../schema/machine-request-v0.1-experimental.schema.json) and
[response schema](../schema/machine-response-v0.1-experimental.schema.json) describe
the two explicitly versioned records. Requests are closed: unknown, duplicate,
inapplicable, wrongly typed and unsupported fields/versions fail. Exactly one JSON
request is accepted, up to 65,536 UTF-8 bytes. Request files must be regular,
non-symlink files. Paths are made absolute before delegation; leading hyphens or
spaces in a filename do not become flags. Source loaders retain their own path,
file-size, sibling/import and profile restrictions.

| `input_kind` | `operation` | Additional fields | Effects and output |
| --- | --- | --- | --- |
| `native-yh` | `inspect` | optional `scenario`, `stage` | Non-evaluating compiler stages; `stage` = all/parsed/checked/normalized/lowered |
| `native-yh` | `check`, `compile`, `run` | optional `scenario` | Existing native payload. Check/compile may evaluate for acceptance in typed/presumption loaders; run evaluates |
| `native-yh` | `diagram` | required `output`, `view`, `encoding`; optional `scenario` | New file; simplified semantic graph only. `view` = rule/modules/case/trace; `encoding` = json/xml/svg. Model-specific restrictions still apply; may evaluate |
| `composition-yh` | `check` | optional `against` | Non-evaluating current-source validation; optional exact saved-plan attachment check |
| `composition-yh` | `run` | required `output` | Fresh evaluation of current checked sources; new export directory |
| `computed-input-json` | `check` | none | Public `decodeComputedInputDocument` and `validateComputedInput`; compiles for validation, no evaluation |
| `computed-input-json` | `replay` | required `output` | Existing `compose replay`: evaluates the frozen embedded artifact; no live `.yh` reads; new export directory |

Every request also requires `format`, `input_kind`, `operation`, `path`. There are
no extra CLI flags for this dispatcher. Historical native help/output contracts
remain unchanged; `yuho machine --help` is a human-readable usage exception.

The input/operation matrix extends the executable
[Round 1 capabilities](../test/compiler_capabilities.json) in
[machine capabilities](../test/machine_capabilities.json). Native `.yh` includes
modules, scoped cases, named references, quantification and other constructs beyond
source composition. Inspection still refuses unsupported stages/forms explicitly;
that does not imply native execution is unsupported. Composition admits one grounded
relationship/integer named-expression observation into the fixed Synthetic proof
form or its presumption wrapper, under the Round 2 scope/mapping restrictions.
Standalone v0.1–v0.5 authored JSON remains available via public Haskell decoders but
is **not exposed** through this dispatcher. Only the existing computed-input artifact
has JSON check/replay operations here. No `.yh`/SDK universal equivalence is claimed.

## Responses, failures, files and effects

For valid machine invocations, stdout is exactly one response JSON plus newline on
both success and failure. Exit 0 means operation success; exit 1 means refusal or
execution failure. `success` describes operation acceptance, **not** a legal or
technical rule outcome. A successful run can contain `not_satisfied` or `unresolved`.
The `payload` retains the native JSON structure and profile-specific identities.
`diagnostics` retains native source diagnostics including codes, paths, lines,
byte columns and related locations. Public SDK diagnostics retain their object IDs
and JSON locations. Control-envelope errors use `SMJSON`, `SMREQUEST`, `SMLIMIT`,
`SMIO` or `SMCONTRACT` and JSON pointers; they invent no source span.

Non-JSON subprocess logs go to stderr, never into payloads. Ordinary tested success
and refusal paths have empty stderr. OS termination, a broken output pipe or an
unrecoverable process failure is not a promise of a complete JSON response; callers
must check process termination and parsing. Native operation failures emit no export
references. Existing file publication refuses overwrites. Composition stages its complete artifact set beside the destination, then uses
Linux atomic no-replace publication; handled write/publication failures remove
only private staging files and never expose a partial requested directory. It
refuses existing destinations, symlink ancestors and unsupported publication
platforms/filesystems. See the [publication contract](source-composition.md#failure-safe-export-publication-linux). `effects` describes requested operation effects, not a transaction
log proving how far a failing operation reached.

`semantic_profiles` lists profiles explicitly available in native payloads. Empty
with `profile_authority: not_reported_by_operation` means that operation (for example
plain proof check, or the compose export acknowledgement) did not report them. Read
the exported `report.json` for component reports/snapshots. The interface never runs
a second compilation/evaluation to populate a common metadata slot, and never
fabricates observations, source positions or normalized stages. It adds no timestamps
or random IDs. Identical requests at identical paths and unchanged sources give
deterministic payloads; output-directory acknowledgements naturally name their paths.

Composition exports preserve `artifact.json`, `report.json`, `projection.json`,
`view-bindings.json`, `view.json`, `view.xml`, `view.svg`, `source-map.json`.
`projection.json` contains complete native component projections and qualified
`computedNavigation` records (`integrationNode`, `componentProjection`,
`componentNode`). Follow those relationships; matching label/origin strings is not
provenance. Reports preserve typed computation, explicit mapping rationale,
generated execution-only assessment, downstream proof/presumption computation and
separate immutable snapshots. A typed technical status is not an evidential finding.

Opening these existing files or extracting an anchored excerpt requires no command
and no reevaluation. **Replay does evaluate**, using frozen embedded authorship;
it is not a reformat operation. A fresh source run reads current files. Use compose
check with `against` to detect changed live sources before any attempted attachment.
The original `.yh` files never acquire generated assessment records.

Source lexer columns count one-based UTF-8 bytes. Inspection retains token starts;
SDK retained-source anchors use zero-based half-open byte offsets. Generated kernel
spans refer to generated material, not to the original `.yh` file or a legislative
location. The sample client follows `referenceSource`/`referenceSpan` into exact
retained UTF-8 source text, without parsing display labels.

## Non-Haskell client

[client.py](../examples/language-workbench/client.py) uses only the Python standard
library and subprocess argument arrays. Copying the workbench permits external use:

```sh
# Set YUHO to the already built absolute executable path first.
WORKBENCH="$PWD/examples/language-workbench"
cd /tmp
python3 "$WORKBENCH/client.py" "$YUHO" "$WORKBENCH" /tmp/yuho-client-new
```

The destination must not exist. The client checks, inspects without evaluating,
executes, reads complete navigation/source anchors/SVG, revises a supplied scenario,
retains both snapshots, observes stale-plan refusal and replays the frozen original.
No credentials or network are used. TypeScript callers can use the same JSON schemas
and process contract; no TypeScript SDK is claimed.
