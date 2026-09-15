# Haskell Yuho frontend: first authoritative research slice

**Status:** Bounded compiler and technical-result proof of concept under [ADR-0002](ADR-0002-HASKELL-AUTHORITATIVE-FRONTEND.md). The existing [section 84 authored source](../../research/singapore/section-84-pilot/surface/section84.yh) and [fictional offence source](../../rewrite/frontend/fixtures/synthetic/restricted_entry.yh) are the accepted inputs. This document does not claim legal advice, evidence assessment, diagnosis, guilt, conviction, acquittal, sentence, fitness or court disposition.

## Pipeline and supported syntax

`Yuho.Surface.Lexer` decodes strict UTF-8 with LF line endings and one-based byte columns. `Parser` produces a source-located `AST`; `Resolve` binds each named `f:` leaf or `g:` group into one acyclic, source-ordered tree; `Check` validates identifiers, typed synthetic offence elements, exception attachment, supplied proof statuses and contextual/source references; `Lower` produces canonical KernelInput v1 bytes. `Yuho.CLI` calls the existing Haskell kernel **in-process** for `run`. The stages are coordinated by [Yuho.Surface.Compile](../../rewrite/haskell/src/Yuho/Surface/Compile.hs) and its sibling modules; the [CLI](../../rewrite/haskell/src/Yuho/CLI.hs) is exposed as the Cabal `yuho` executable. Python is neither invoked nor embedded in this path.

This first slice accepts the unchanged `model ... { ... }` form in the two fixtures. It supports `variant SuppliedProofStatus-v1`, jurisdiction and purpose, policy, provenance source/quote references, burden annotations, limitations, section 84 `leaf` declarations, typed fictional `offence` conduct/circumstance/fault elements, an attached `exception` with circumstance/purpose elements, `all`/`any` groups, named outputs, and externally supplied `proved`, `not_proved` or reasoned `unresolved` classifications. The fictional model uses a separate `scenario ... { ... }`; section 84 retains its accepted inline `proof_assignments`. Burden and standard annotations, quote references and limitations do not become executable facts. A `not_proved` status is not factual falsity, and `unresolved` is not a court outcome.

From the repository root:

```sh
cd rewrite/haskell
cabal v2-build exe:yuho --offline --jobs=1
YUHO_BIN="$(cabal list-bin exe:yuho)"
"$YUHO_BIN" check ../../research/singapore/section-84-pilot/surface/section84.yh
"$YUHO_BIN" compile ../../research/singapore/section-84-pilot/surface/section84.yh --output /tmp/section84-kernel-input.json
"$YUHO_BIN" run ../../research/singapore/section-84-pilot/surface/section84.yh
"$YUHO_BIN" compile ../frontend/fixtures/synthetic/restricted_entry.yh --scenario ../frontend/fixtures/synthetic/scenario_all_proved.yh
```

`compile` writes compact canonical JSON without a final newline. It completes parsing, resolution, checking and lowering before publishing a requested output path; a failed compile leaves no successful output. Diagnostics on stderr contain stable SFE code, source path, line and byte column. The accepted section 84 request is exactly 7,599 bytes, SHA-256 `1ebe4d4fdd3de643e938c512fafd1c68ed437728b1249d32b6a236639a58d6e2`, and the fictional v0.1 request has SHA-256 `2c46977bbb855fac477d85f4d8dc2581d992bb87253cc1372146fb679212a535`. In-process `run` reproduces their frozen technical responses. The existing reviewed section 84 ModelBundle digest `02e51da9fa1bf285eec7cca8b55494c1d6a8e82b9b7e7e300a30b338ecbd404a` is a regression assertion; this compiler does not create another bundle or review.

## Boundary

This document records the first slice and is no longer the complete capability list. The authoritative Haskell path now accepts bounded exact-version local modules and qualified references, complete authored temporal alternatives selected by a scenario conduct date, candidate penalty terms, typed shared case facts and three-allegation case execution. See the [current DSL guide](HASKELL-YUHO-DSL-GUIDE.md). It still does not provide locks, arbitrary expressions, fact or evidence extraction, legal temporal applicability, a general execution-plan language or judicial outcomes. The Python v0.2–v0.4 implementations remain historical conformance references, not the authoritative grammar.
