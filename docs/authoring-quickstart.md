# Experimental Haskell SDK quickstart

This is a headless Haskell SDK for explicit legal requirement trees, selected
supplied assessments and one represented acyclic exception guard. It does not
weigh evidence or determine legal completeness. The API and serialized formats
are experimental. Use the [SDK guide](authoring-sdk.md) for the full contract.

## Recommended reading order

Start here and run the lifecycle below. Then use the SDK guide's
[current API/accessor map](authoring-sdk.md#current-api-map) to navigate the public
records, and its [export recipe](authoring-sdk.md#export-recipe) for complete
projections, view bindings and distinct JSON/XML/SVG filenames. Consult the
detailed contracts and historical tranche sections only as needed; they are not
prerequisites to this quickstart. Checked original-source anchors are available now.
For a cohesive requirement → assessment → source → explicit revision interaction,
use [focus, reveal and revise](authoring-sdk.md#focus-reveal-and-revise) after the
lifecycle below. It uses the same public facade and leaves view state separate
from authored selections.

After this lifecycle, [linked definitions](linked-definitions.md) documents the
optional v0.2 profile for explicit expression reuse across scoped analyses. The
quickstart itself retains the existing v0.1 example.
For concrete typed relationships and exact integer comparisons, the separate
[typed-authoring guide](typed-authoring.md) provides the opt-in v0.3 lifecycle.

## Build a real consumer outside the checkout

Yuho is used here as an **explicit local Cabal package**, not an assumed Hackage
release. GHC 9.8.4 and the checkout's existing dependency cache are required for
the offline commands. No browser or JavaScript binding is involved.

From the Yuho checkout, build the existing example and export its bounded hurt
document. Then create a separate project containing only the quickstart source,
package configuration, pinned dependency constraints and explicitly supplied JSON:

```sh
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
yuho_checkout=$(pwd)
consumer_bin=$(cabal list-bin exe:yuho-authoring-consumer --offline --with-compiler=ghc-9.8.4)
quickstart_dir=$(mktemp -d /tmp/yuho-quickstart.XXXXXX)
"$consumer_bin" --model hurt --artifacts "$quickstart_dir/input"
cp "$yuho_checkout/examples/authoring-quickstart/Main.hs" "$quickstart_dir/"
cp "$yuho_checkout/examples/authoring-quickstart/yuho-sdk-quickstart.cabal" "$quickstart_dir/"
cp "$yuho_checkout/cabal.project.freeze" "$quickstart_dir/"
printf 'packages: .\n          "%s"\nwith-compiler: ghc-9.8.4\nindex-state: 2026-09-12T03:17:42Z\njobs: 1\n' "$yuho_checkout" > "$quickstart_dir/cabal.project"
cd "$quickstart_dir"
cabal v2-build exe:yuho-sdk-quickstart --offline -j1 --with-compiler=ghc-9.8.4
quickstart_bin=$(cabal list-bin exe:yuho-sdk-quickstart --offline --with-compiler=ghc-9.8.4)
"$quickstart_bin" "$quickstart_dir/input/data/hurt-01_intention_no_exception.document.json" "$quickstart_dir/output"
```

The generated `packages` entry names your actual checkout. The copied freeze is used unchanged.
The new package declares `yuho ==1.0.0.0` and imports only `Yuho.Authoring` from
Yuho. Runtime resources are explicit arguments; it never searches the checkout.
The retained hurt model is a bounded research fixture with synthetic supplied
classifications and explicit scope assumptions, not complete current criminal law.

## Follow the supported lifecycle

The complete, tested program is [Main.hs](../examples/authoring-quickstart/Main.hs)
with its [Cabal configuration](../examples/authoring-quickstart/yuho-sdk-quickstart.cabal).
It does the following:

1. Loads the supplied authored graph with strict `decodeDocument`. To construct
   a graph instead, use the public records as shown in the
   [hurt consumer](../examples/authoring-consumer/Hurt.hs).
2. Creates an original synthetic source and a checked reference **before** any
   projection exists:

   ```haskell
   let note = SourceRecord "source:quickstart-note" "synthetic" Nothing
         (Just "Synthetic: Mei reports pain (痛) in her arm after the push.")
   anchor <- sourceAnchorCodePoints note 11 58
   -- Stored UTF-8 bytes [11,60); no byte/line/column arithmetic required.
   ```

3. Attaches that reference to the existing case assertion, constructs a separate
   synthetic `Assessment` and explicitly selects it with `selectAssessment`.
   Its supplied `proved` classification is an authored input, not a conclusion
   inferred from the source link. Assertion and assessment scopes remain explicit.
4. Checks `analysisReady (validateAnalysis document analysisId)`, then calls
   `compileAnalysis` and `evaluateAnalysis`. These return diagnostics on failure.
5. Calls `projectEvaluation`, `inspectAssessment` and `recoverOriginalSource`.
   It creates a focused `applicationView` and exports JSON/XML/SVG using the
   existing encoders, alongside the complete projection and omission bindings.
   The [export recipe](authoring-sdk.md#export-recipe) also covers the dedicated
   law-occurrence encoders and generic case/application encoders, and demonstrates
   selected-assessment focus versus input focus with retained alternatives.
6. Edits the case narrative through `editCaseAssertion`, validates and explicitly
   evaluates the candidate. The supplied classifications remain unchanged; the
   compatible comparison reports changed provenance without computed changes.
   It demonstrates `PSTALE` when attaching the older evaluation to the revision.
7. Saves both versions with `encodeDocument`, reloads the saved revision with
   `decodeDocument`, validates it, and reproduces its evaluation.

Expected stdout reports `before: satisfied`, `after: satisfied`, distinct snapshot
IDs, the exact original excerpt, and `savedReloaded: true`. Inspect `output/summary.json`,
`application.svg`, `application.projection.json`, `assessment-inspection.json`,
`narrative.comparison.json` and the saved authored documents.

## Boundaries to retain

- An edit's success establishes addressing/replacement, not executable validity.
  Validate the resulting candidate; do not evaluate an invalid draft.
- Supplied classifications, computed consequences and evaluation/skip states are
  separate. Editing narrative or sources does not automatically revise assessments.
- The hurt example's acknowledgement gate is a **consumer operation**. Its explicit
  inputs and admission receipt are documented in the [SDK guide](authoring-sdk.md).
  This quickstart demonstrates bare SDK operations; `compileAnalysis` does not
  enforce that additional consumer policy or validate the scope assumptions' truth.
- Anchors refer to the exact retained text. `sourceAnchorBytes` uses zero-based,
  half-open UTF-8 byte offsets; `sourceAnchorCodePoints` uses Unicode code-point
  offsets. Both accept `Integer`, validate bounds and produce existing `SourceRef`
  records with one-based UTF-8 byte columns. LF advances a line; CR is a byte.
  Offsets address `sourceText`, not the surrounding JSON or generated kernel text.
  Empty/EOF spans are valid. Code points are not UTF-16 units or grapheme clusters.
- A source revision does not relocate anchors. Same-length replacement can leave
  an anchor structurally valid while changing its excerpt. Old snapshots keep old
  text; the constructors do not detect all stale selections or verify meaning.
- Snapshots retain exact prior inputs. Changed law records, including labels, can
  make `compareAnalyses` incompatible. This example's narrative edit keeps the law.
- The authored document is the editable interchange format. The complete projection
  is derived output with observations and mappings. A simplified SVG/XML/legacy
  JSON view is not lossless authoring interchange.

The external setup is exercised by:

```sh
python3 test/authoring_quickstart.py "$consumer_bin" --review-dir /tmp/yuho-sdk-review
```

Run that command from the Yuho checkout before changing directory, or use its
absolute script path. It creates and builds a separate Cabal project using only
the documented local package dependency, copied freeze and public imports, then
runs the lifecycle and validates the resulting schemas and exports.
