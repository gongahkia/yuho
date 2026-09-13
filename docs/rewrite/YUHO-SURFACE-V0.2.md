# YuhoSurface-v0.2: bounded versioned module composition

**Status:** synthetic compiler/kernel conformance subset, 13 September 2026. The shared [Python frontend](../../rewrite/frontend/core.py) retains the v0.1 lexer, source-located AST and lowerer; [modules.py](../../rewrite/frontend/modules.py) adds offline module resolution and explicit composition. The [CLI](../../rewrite/frontend/__main__.py) accepts both versions. This is not a package manager, a general criminal-law language or a real-law model.

## Architecture decision

The accepted [rewrite proposal](YUHO-REWRITE-ARCHITECTURE-PROPOSAL.md) §2 explicitly makes `yuho.kernel-input/v1` a separate subprocess boundary from Canonical IR v1.2 and shows the existing Python parser branching to each artifact. Its §3 keeps Canonical IR v1.2 as read/compare migration evidence: it lacks the kernel's source spans and uses opaque snapshots and AST adapters. The [migration contract](MIGRATION-CONTRACT.md) also treats the two as separate. The v0.1 `rewrite/frontend/core.py` lowerers directly construct KernelInput. YuhoSurface-v0.2 follows that accepted direct KernelInput path and does not create a competing general intermediate representation or alter Canonical IR. A future compiler-boundary change would require a separate versioned decision.

## Closed grammar subset and identity

Each v0.2 file starts `language YuhoSurface-v0.2; module <canonical-id> version <exact-major.minor.patch>; { ... }`. Module IDs use lowercase dotted segments. Versions have three nonnegative decimal components, with no range or `latest`. Every module declares `kind offence`, `kind exception` or `kind composition`, `jurisdiction Fictional`, `purpose compiler_fixture`, explicit `export` declarations, provenance, a contextual burden annotation and non-executable limitations. Symbols are private unless exported.

An offence child has typed `conduct`, `circumstance` and `fault` elements plus a named requirement group. An exception child has typed `circumstance` and `purpose` elements plus its group. Both permit `all` and `any` acyclic local trees; neither is attached merely by being imported. The [root composition](../../rewrite/frontend/fixtures/modules/composition.yh) imports exact versions with mandatory aliases and explicitly selects the two models, attaches the exception and names four technical outputs:

```yuho
import fictional.restricted-entry version 1.0.0 as entry;
import fictional.emergency-rescue version 1.0.0 as rescue;
compose {
  offence entry::o:entry;
  exception rescue::x:emergency-rescue;
  attach rescue::x:emergency-rescue to entry::o:entry;
  outputs {
    offence_requirements entry::g:offence-requirements;
    exception_applicable rescue::g:emergency-requirements;
    defeated_branch entry::p:entry;
    final_rule entry::r:entry;
  }
}
```

The offence [module](../../rewrite/frontend/fixtures/modules/offence.yh), exception [module](../../rewrite/frontend/fixtures/modules/exception.yh), root and [scenario](../../rewrite/frontend/fixtures/scenarios/module_all_proved.yh) are wholly fictional, non-authoritative, unreviewed and only for compiler/kernel conformance. The scenario remains a separate `scenario ... { proof_assignments { ... } }` document. Its five externally supplied statuses are joined with the authored graph only at KernelInput lowering. Imported semantic IDs are qualified by module ID and exact version, independent of checkout location. Contextual annotations, quote/source references and limitations cannot become executable propositions. The four output declarations are checked names of existing technical graph nodes, not new KernelResult fields.

`SuppliedProofStatus-v1` is the least existing kernel variant with supplied `proved`/`not_proved`/reasoned `unresolved` classifications and a guarded defeating exception. The root selects a restricted-entry technical branch; only when its requirements are satisfied does the emergency branch affect the result. The kernel returns technical status and trace, not guilt, liability, conviction, acquittal, sentence, diagnosis, fitness or judicial disposition. There is no evidence assessment or legal advice.

## Offline resolution, lock and limits

One explicit `--module-root` directory is required. The resolver indexes `.yh` files in sorted order, checks every declaration, resolves exact `(module ID, version)` pairs, rejects duplicate pairs and traverses imports deterministically. Imported references require `alias::symbol` and an explicit export. An unused import is locked but does not execute or attach its declarations. No registry, network, implicit search path, environment-dependent version selection, absolute import path or parent traversal exists. Root and descendants must be regular in-root files; symlinks and unsupported filesystem objects reject.

The canonical [module lock](../../rewrite/frontend/fixtures/modules/MODULE-LOCK.json) is `yuho.module-lock/v0.1`. Compact UTF-8 JSON with lexically sorted keys and no trailing newline records `schema`, `language_version`, `compiler`, exact root ID/version, modules sorted by ID/version, each module's exact raw-byte SHA-256 and byte length, sorted direct import ID/version/alias edges, and a dependency-first `topological_order`. It omits machine paths, clocks, usernames and filesystem metadata. `--verify-lock` compares the exact canonical resolved lock bytes with a supplied lock, so changed dependency bytes fail. The lock establishes reproducibility, not legal authority or authenticity.

The v0.2 limits are 64 KiB per source, 4,096 tokens per source, 32 modules in a configured root, 1 MiB aggregate module bytes, 128 root directory entries, 16 nested directory levels and 16 import levels. The existing checker also bounds semantic nodes and scenario assignments. Comparisons use indexed module identities and sorted edges; resolution is O(total source bytes + modules log modules + import edges log import edges), within the stated bounds. Module diagnostics retain path, one-based line and UTF-8 byte-column. SFE001–SFE021 keep v0.1 meanings; SFE022–SFE037 identify declaration/version/import/export/composition/path/limit/lock failures. Import failures include the importer and an import-chain hint where relevant. Failed compilation publishes neither request nor lock. `check` writes no output files; repeated `--module-root` flags reject.

## Reproduce the synthetic path

From the repository root, with the pinned offline Haskell binaries available:

```sh
MODULE_ROOT=rewrite/frontend/fixtures/modules
SCENARIO=rewrite/frontend/fixtures/scenarios/module_all_proved.yh
FRESH_DIR=$(mktemp -d)
YUHO_KERNEL_BIN=$(cd rewrite/haskell && cabal list-bin exe:yuho-kernel)
YUHO_BUNDLE_BIN=$(cd rewrite/haskell && cabal list-bin exe:yuho-model-bundle)
python3 -m rewrite.frontend check "$MODULE_ROOT/composition.yh" --module-root "$MODULE_ROOT" --verify-lock "$MODULE_ROOT/MODULE-LOCK.json"
python3 -m rewrite.frontend compile "$MODULE_ROOT/composition.yh" --module-root "$MODULE_ROOT" --scenario "$SCENARIO" --output "$FRESH_DIR/request.json" --lock-output "$FRESH_DIR/module-lock.json"
"$YUHO_KERNEL_BIN" < "$FRESH_DIR/request.json"
python3 - "$MODULE_ROOT" "$SCENARIO" "$FRESH_DIR" <<'PY'
from pathlib import Path
import sys
from rewrite.frontend import bundle, modules
root, scenario, fresh = map(Path, sys.argv[1:])
resolved = modules.resolve(root / "composition.yh", root)
request = (fresh / "request.json").read_bytes()
print(bundle.build(resolved.model, request, fresh / "bundle"))
PY
"$YUHO_BUNDLE_BIN" validate "$FRESH_DIR/bundle"
```

The committed synthetic request is [request.json](../../rewrite/frontend/fixtures/modules/request.json), SHA-256 `2d2d46fb5cb05d004a9ec1beef7bef233e8c70e83e0af6bd506135c0852cae2a`; the module-lock SHA-256 is `badac18187f709389a8ae8d16e5adde77d94d9d151d922dc5d3564b20415a845`. The structurally valid, unsigned, unreviewed four-file bundle has digest `d2a6c48b02883ca0fd06810fd8d60a21773c7e8b73be07a05f61e754371f675d`. It contains a manifest, two synthetic source artifacts and the compiled request artifact. Authored modules and lock remain repository compiler artifacts because the accepted ModelBundle-v1 profile has no module-lock role. Scenario changes alter request and bundle digests.

## Compatibility and exclusions

Both [YuhoSurface-v0.1](YUHO-SURFACE-V0.1.md) programs remain accepted without syntax edits. The section 84 request stays 7,599 bytes, SHA-256 `1ebe4d4fdd3de643e938c512fafd1c68ed437728b1249d32b6a236639a58d6e2`, without a final newline; its reviewed six-file bundle digest remains `02e51da9fa1bf285eec7cca8b55494c1d6a8e82b9b7e7e300a30b338ecbd404a`. The v0.1 fictional request remains `2c46977bbb855fac477d85f4d8dc2581d992bb87253cc1372146fb679212a535`, and its bundle remains `091cb0f9286dd8dd67cbd686d92a410d7a928fe8fa2d03396821e814ca4976db`.

This subset supports one explicit synthetic offence/exception composition, not arbitrary graph linking, multi-exception policies, modules with executable cross-references, imports from remote registries, version ranges, temporal-law selection, real legal doctrine, dynamic burden shifting, general computation, evidence assessment or court outcomes. Future bundle versions require an explicit packaging and comparator decision before module sources or locks become core artifacts.
