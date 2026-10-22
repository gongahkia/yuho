# Experimental SDK distribution and verification

Yuho is a diagram-first DSL and SDK for modelling Singapore criminal-law
structures. This distribution records a bounded experimental subset. The Cabal
package remains `yuho-1.0.0.0`; authoring and projection formats remain
experimental. This does not establish comprehensive legal expressiveness,
offence coverage, statutory applicability, evidential sufficiency or production
legal-decision reliability.

## Source package and complete bundle

The **Cabal source package** contains the library/CLI sources, public SDK guides,
all public schemas, unchanged dependency freeze, public consumer examples and
the fixtures needed by `yuho-sdk-test`. SDK resources are caller-supplied;
there are no invented installation-time data directories. `extra-source-files`
contains developer resources, not automatically loaded law.

The **complete reproducibility bundle** additionally contains the research
corpus, saved legal-source records, all native/protocol fixtures, Lean sources,
release metadata, validation scripts and the pinned historical kernel sources.
It is needed for `yuho-test` and `make verify`. Neither artifact contains compiler
binaries or a dependency cache. The complete bundle does not require a live Git
repository. Public distribution requires the [rights review](third-party-notices.md).
Generated local archives are private release candidates, not published releases.
The [public-surface comparison](distribution-boundaries.md) keeps repository,
archive and history decisions separate. [Legislative notices](legislation-notice.md)
and the [owner-authorisation record](owner-authorisation.md) accompany both source
artifacts; their presence does not establish redistribution clearance. Check
notice inclusion with `python3 scripts/verify_release_notices.py --archive PATH`.

After final metadata edits and release-manifest regeneration, create the larger
artifact from the complete Git checkout:

```sh
python3 scripts/generate_reproducibility_bundle.py --sdk-archive /absolute/outside/sdist/yuho-1.0.0.0.tar.gz --output /absolute/outside/yuho-reproducibility-1.0.0.0.tar.gz
```

The generator includes current tracked bytes plus the explicitly enumerated
Cabal source resources. It excludes arbitrary untracked files and caches, fixes
archive ordering/timestamps/ownership, and verifies the SDK archive against the
candidate. It embeds the exact pinned historical Git archive with a checked
SHA-256. `test/prior_bytes.py` verifies that digest before compiling it, retaining
all 318 original response comparisons without requiring `.git` in the bundle.
Extract using the supplied helper, activate the pinned Haskell/Python/Lean
environment, and run `make verify` at the printed source root:

```sh
python3 scripts/extract_reproducibility_bundle.py /absolute/outside/yuho-reproducibility-1.0.0.0.tar.gz --output-dir /absolute/outside/repro-proof
```

The full native suite contains two original negative-test symlinks to
`/etc/passwd`. The generator stores their link metadata without reading that
file. The extractor data-filters regular entries first, then recreates only
those two exact fixture paths/targets, never following them. Other links and
unsafe/duplicate paths are refused. The Cabal SDK package contains neither
fixture. No `lake update` or dependency-freeze rewrite is needed.

The existing `release/yuho-haskell-research-v1.0.0.json` retains its historical
research-language identity, format and canonical SHA-256 inventory. It is not a
complete SDK inventory or a declaration of stable authoring formats. Cabal
enumerates source-package contents; the bundle generator does not replace the
existing release-manifest generator or Haskell verifier.

## Build an extracted Cabal source package

Use GHC 9.8.4 and Cabal 3.12.1.0. From the extracted package root:

```sh
cp cabal.project.sdk cabal.project
cabal v2-build all --offline -j1 --with-compiler=ghc-9.8.4
cabal v2-test yuho-sdk-test --offline -j1 --with-compiler=ghc-9.8.4 --test-show-details=direct
```

Offline builds require a prepared Hackage index/package cache. For an empty
cache, run `cabal update` and `cabal v2-build all --only-dependencies --enable-tests
-j1 --with-compiler=ghc-9.8.4` first. The supplied freeze and pinned index state
still apply. Do not regenerate the freeze or substitute a compiler version.

The package default disables `research-tests`; the repository project explicitly
enables it. The original full native suite is unchanged. The packaged SDK suite
reuses accepted proof/projection/editing, linked reuse, typed, presumption,
temporal, computed-navigation, long-ID and source/snapshot regressions without
the bulk saved Penal Code corpus. Research-guide links, corpus commands and full
release verification require the complete bundle. The SDK guides and their
SDK-local links ship in the Cabal package.

`development` is a manual, default-off Cabal flag for `-Werror`; pinned project
templates enable it. Cabal controls optimisation rather than an unconditional
`ghc-options: -O1`.

## Reproduce the distribution proof

With Python `jsonschema==4.25.1` available, from the complete source tree:

```sh
cabal v2-sdist all --output-directory=/absolute/outside/sdist
python3 scripts/verify_sdk_distribution.py /absolute/outside/sdist/yuho-1.0.0.0.tar.gz --work-dir /absolute/outside/package-proof
```

The verifier refuses an existing work directory, records commands/exits,
extracts and builds/tests only packaged sources, then builds another independent
package from the [public consumer](../examples/sdk-distribution-consumer/Main.hs).
That package imports only `Yuho.Authoring` and depends only on the extracted
Yuho package. It exercises proof, linked, typed/integer, presumption, temporal
and computed-input execution, combined projection validation, exact source
recovery and immutable revision/replay. Documents, full projections and view
bindings are validated against the extracted schemas.

See the [quickstart](authoring-quickstart.md), [API guide](authoring-sdk.md),
[definitions](linked-definitions.md), [typed](typed-authoring.md),
[presumptions](presumption-authoring.md), [temporal](temporal-authoring.md) and
[computed bindings](computed-input-bindings.md) contracts. Simplified diagram
views do not replace complete projections or editable authored documents.

## Frozen experimental scope

| Profile | Admitted capability |
| --- | --- |
| v0.1 | Explicit proof trees and one acyclic exception guard |
| v0.2 | Scoped linked definitions; ambiguous repeated primitives reject `AREUSE` |
| v0.3 | Ground typed expressions, exact integers and finite all/any |
| v0.4 | Registered presumptions over v0.1 |
| v0.5 | Half-open interval selection among complete v0.1 expressions |
| computed-input/v0.1 | One explicitly authorised actual typed expression into one proof/presumption primitive |

All format markers remain experimental. Pin source, compiler, freeze and index
state for replay. Future experimental changes may require explicit migration;
no indefinite source/binary/byte compatibility or automatic migration is promised.
Unsupported combinations remain refused. This release preparation adds no
temporal-presumption adapter, occurrence-qualified assessment contract or new
legal-modelling capability.
