# YuhoSurface-v0.3: synthetic temporal-expression selection

**Status:** bounded fictional compiler/kernel conformance subset, 14 September 2026. The [shared lexer and checked lowerer](../../rewrite/frontend/core.py), [exact-version module resolver](../../rewrite/frontend/modules.py), [temporal selector](../../rewrite/frontend/temporal.py), and [CLI](../../rewrite/frontend/__main__.py) compile one expressly authored rule expression selected by a supplied civil conduct date. The selector does not determine which law applies to real conduct. Authoritative dates, expressions and jurisdictional rules would need to be supplied and reviewed outside this compiler before any real-law claim.

## Three identities and the bundle digest

A **module ID and exact semantic version** identify authored `.yh` bytes and resolve imports. A **rule-family ID** names the continuing fictional rule. An **expression ID and exact version** identify one complete dated graph within that family; its version does not select its interval. The **ModelBundle-v1 digest** separately identifies exact packaged executable and source bytes. Module version ordering, expression version ordering, a `supersedes` declaration and digest ordering have no automatic applicability or legal effect.

The v0.3 [temporal root](../../rewrite/frontend/fixtures/temporal/modules/temporal_root.yh) is a versioned synthetic module. It imports two complete v0.2 [composition models](../../rewrite/frontend/fixtures/temporal/modules/composition_pre.yh) and [post-expression composition](../../rewrite/frontend/fixtures/temporal/modules/composition_post.yh), each with its exact [offence](../../rewrite/frontend/fixtures/temporal/modules/offence.yh) and [exception](../../rewrite/frontend/fixtures/temporal/modules/exception_pre.yh) / [post exception](../../rewrite/frontend/fixtures/temporal/modules/exception_post.yh) graph. Each `expression` names exactly one complete imported model; it never applies a text patch or reconstructs a graph from amendment instructions. Both child composition modules are version `1.0.0`, while the post expression is version `2.0.0`:

```yuho
language YuhoSurface-v0.3;
module fictional.restricted-entry-temporal version 1.0.0; {
  kind temporal;
  jurisdiction Fictional;
  purpose compiler_fixture;
  rule-family fictional.restricted-entry;
  import fictional.restricted-entry-composition-pre version 1.0.0 as pre;
  import fictional.restricted-entry-composition-post version 1.0.0 as post;
  expression pre-amendment version 1.0.0 {
    effective from 2030-01-01 until 2031-01-01;
    model pre;
  }
  expression post-amendment version 2.0.0 {
    effective from 2031-01-01;
    supersedes pre-amendment;
    model post;
  }
  limitations { "Wholly fictional compiler fixture"; "No court outcome or legal advice"; }
}
```

The actual fixture includes the same bounded declarations and limitations. The separate [pre-boundary scenario](../../rewrite/frontend/fixtures/temporal/scenarios/pre.yh) and [boundary scenario](../../rewrite/frontend/fixtures/temporal/scenarios/boundary.yh) supply the date and the same five local proof-status names:

```yuho
scenario M00 for fictional.restricted-entry {
  conduct_date 2030-12-31;
  proof_assignments {
    f:entry = proved;
    f:no-authorization = proved;
    f:knowledge = proved;
    f:immediate-danger = proved;
    f:rescue-purpose = not_proved;
  }
}
```

The pre expression's emergency requirement is `any(immediate-danger, rescue-purpose)`; the post expression's is `all(immediate-danger, rescue-purpose)`. Offence requirements are the same three-element conjunction. The pre scenario has a technically applicable exception and a defeated root branch; the boundary scenario has an inapplicable exception and a technically satisfied root. The child modules retain a fixed KernelInput `policy.reference_date`; it is neither the supplied conduct date nor the expression selector. These are synthetic statuses and traces, never liability, guilt, acquittal or a judicial finding.

## Civil-date, lineage and selection rules

Dates are exact `YYYY-MM-DD` Gregorian calendar strings, validated for leap years and month lengths. An interval is `effective_from <= conduct_date < effective_to`. The final expression may omit `until`, making its authored interval open-ended. No system clock, timezone, locale, network or default date participates. A missing conduct date, an uncovered gap and overlapping or multiply matching expressions fail; source order and version number are never tie-breakers. A scenario outside all intervals emits no request, lock or selection record.

Each root contains at most 16 expressions. The v0.2 limits still apply: 64 KiB per source, 4,096 tokens, 32 modules, 1 MiB aggregate module bytes, 128 root entries and depth 16. Every candidate composition is checked before selection, and all complete graphs must expose the same stable local supplied-input vocabulary. A `supersedes` reference is optional contextual lineage: it must name a same-family expression, remain acyclic and follow a coherent prior interval. Removing it can change the lock and selection record but not executable request bytes. Neither it nor an `amendment` label selects an expression.

This subset has no retroactivity, savings or transition rules, revived expressions, conduct spanning dates, continuing offences, simultaneously applicable expressions, conflict of laws, jurisdiction selection, real legislation, evidence assessment, dynamic burdens, sentencing or court outcomes.

## Canonical outputs and CLI

The [module lock](../../rewrite/frontend/fixtures/temporal/MODULE-LOCK.json) retains `yuho.module-lock/v0.1` shape with `language_version: YuhoSurface-v0.3` and compiler `yuho.rewrite.frontend/v0.3`. It binds the temporal root and all transitive exact source bytes, versions, import aliases and deterministic dependency order; SHA-256: `19bff96d56022031b19be1a4425e405bb2c3fa8f1e484095e6339b308ec2defa`. The lock is reproducibility evidence, not source authentication.

The separate `yuho.temporal-selection/v0.1` record is compact sorted-key UTF-8 JSON with no final newline. It contains `schema`, root module ID/version, rule family, supplied conduct date, all candidate IDs/versions and tagged end states (`date` or `open`), the selected ID/version, exact SHA-256 of its composition source module, module-lock SHA-256 and reason `conduct_date_within_effective_interval`. It contains no timestamp, host, path, identity or “current law” claim. The committed [pre](../../rewrite/frontend/fixtures/temporal/pre-selection.json) and [post](../../rewrite/frontend/fixtures/temporal/post-selection.json) records have SHA-256 `a86cb78750c8ad77e21fafa78a067de9242ef26128a0c20a197daf8616a2c484` and `2f6d22b3e9142ce7acdeb6b351599e5c4d475c26f8e3dabfa53697e8360e1a14`.

From the repository root, with the pinned offline Haskell executables installed or built:

```sh
MODULE_ROOT=rewrite/frontend/fixtures/temporal/modules
SCENARIOS=rewrite/frontend/fixtures/temporal/scenarios
FRESH_DIR=$(mktemp -d)
YUHO_KERNEL_BIN=$(cd rewrite/haskell && cabal list-bin exe:yuho-kernel)
YUHO_BUNDLE_BIN=$(cd rewrite/haskell && cabal list-bin exe:yuho-model-bundle)
python3 -m rewrite.frontend check "$MODULE_ROOT/temporal_root.yh" --module-root "$MODULE_ROOT" --scenario "$SCENARIOS/pre.yh" --verify-lock rewrite/frontend/fixtures/temporal/MODULE-LOCK.json
python3 -m rewrite.frontend compile "$MODULE_ROOT/temporal_root.yh" --module-root "$MODULE_ROOT" --scenario "$SCENARIOS/pre.yh" --output "$FRESH_DIR/pre-request.json" --lock-output "$FRESH_DIR/pre-lock.json" --selection-output "$FRESH_DIR/pre-selection.json"
python3 -m rewrite.frontend compile "$MODULE_ROOT/temporal_root.yh" --module-root "$MODULE_ROOT" --scenario "$SCENARIOS/boundary.yh" --output "$FRESH_DIR/post-request.json" --lock-output "$FRESH_DIR/post-lock.json" --selection-output "$FRESH_DIR/post-selection.json"
"$YUHO_KERNEL_BIN" < "$FRESH_DIR/pre-request.json"
"$YUHO_KERNEL_BIN" < "$FRESH_DIR/post-request.json"
python3 - "$MODULE_ROOT" "$FRESH_DIR" <<'PY'
from pathlib import Path
import sys
from rewrite.frontend import bundle, temporal
root, fresh = map(Path, sys.argv[1:])
resolved = temporal.resolve(root / "temporal_root.yh", root)
for name, expression in (("pre", "pre-amendment"), ("post", "post-amendment")):
    model = next(candidate.model for item, candidate in resolved.candidates if item.identifier.text == expression)
    print(name, bundle.build(model, (fresh / f"{name}-request.json").read_bytes(), fresh / f"{name}-bundle"))
PY
"$YUHO_BUNDLE_BIN" validate "$FRESH_DIR/pre-bundle"
"$YUHO_BUNDLE_BIN" validate "$FRESH_DIR/post-bundle"
"$YUHO_BUNDLE_BIN" diff "$FRESH_DIR/pre-bundle" "$FRESH_DIR/post-bundle"
```

`check` emits one canonical JSON status line and writes no outputs. v0.3 `compile` requires all three explicit output paths, validates every candidate, then publishes request, lock and selection through temporary files with rollback on publication failure. Existing files and unsafe output paths reject. `--verify-selection` and `--verify-lock` require exact canonical byte equality. SFE038–SFE051 cover invalid temporal declarations/vocabulary, duplicate expressions, dates, missing dates, interval errors, no/multiple matches, lineage, unsupported versions, conflicting output paths and verification mismatch. Existing SFE001–SFE037 retain their meanings; unsafe paths still use SFE015/SFE035. Every diagnostic has source path, line and UTF-8 byte column.

The [pre request](../../rewrite/frontend/fixtures/temporal/pre-request.json), SHA-256 `e06597d71ec7119a8282931168af9b417e21cb9e031daab2324e3171defd0d92`, yields bundle `c13134d95328634892c0f16b585d28282b40792741dd9e0e01809ff009e224d5`. The [post request](../../rewrite/frontend/fixtures/temporal/post-request.json), SHA-256 `f384d62c6f3fe199b842381b9bd87bfe9f5abbfe2aa7437f572b0daebbda2012`, yields bundle `ac3491abe4f41b26e3161587fab68cb991348a8abeb29f97ec905150a4a25ac0`. Each bundle has one manifest and three content-addressed artifacts; both are fictional, unsigned, unreviewed and non-authoritative. The [synthetic ChangeSet snapshot](../../rewrite/frontend/fixtures/temporal/change-set.json) is a structural byte comparison, not proof of amendment, supersession or applicability. Module locks and selection records remain repository compiler artifacts outside ModelBundle-v1; its accepted schema has no role for them.

## Compatibility boundary

The v0.3 selector uses already checked v0.2 composition graphs and the unchanged `SuppliedProofStatus-v1` lowerer. The accepted [architecture proposal](YUHO-REWRITE-ARCHITECTURE-PROPOSAL.md) keeps KernelInput separate from Canonical IR v1.2; no new kernel input or intermediate representation was introduced. Existing section 84, v0.1 and v0.2 sources are unedited. Their frozen request, response, lock and bundle bytes remain regression gates, not inputs to temporal selection. The result is a typed technical rule result and trace; it does not assess facts or determine real-world applicability.
