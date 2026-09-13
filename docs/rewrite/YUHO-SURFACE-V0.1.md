# YuhoSurface-v0.1: bounded reusable frontend

**Status:** compiler and kernel conformance subset, 13 September 2026. The authoritative [Python frontend](../../rewrite/frontend/core.py) supplies one UTF-8 lexer, source-located AST, parser, name/type checker and deterministic lowerer. The [CLI](../../rewrite/frontend/__main__.py) is `python3 -m rewrite.frontend`; the former section 84 script is a [compatibility wrapper](../../research/singapore/section-84-pilot/surface/frontend.py). This is neither the legacy production Tree-sitter grammar nor a complete criminal-law language. Canonical IR v1.2 and KernelInput v1 remain separate and unchanged.

## Authored syntax and technical meaning

The [fictional model](../../rewrite/frontend/fixtures/synthetic/restricted_entry.yh) and [separate scenario](../../rewrite/frontend/fixtures/synthetic/scenario_all_proved.yh) use two document roles. `model <id> { ... }` declares `variant`, fictional `jurisdiction`, `purpose`, `request`, `policy`, `provenance`, `annotations`, one typed `offence`, one attached `exception`, `outputs` and `limitations`. The offence requires `conduct`, `circumstance` and `fault` elements; the emergency exception requires `circumstance` and `purpose` elements. Named `all` and `any` groups form acyclic, source-ordered trees. Each element names an exact quote. `scenario <request-id> for <model-id> { ... }` supplies one `proved`, `not_proved` or reasoned `unresolved` classification per element. The model contains no assignment; KernelInput combines model and scenario at the existing protocol boundary.

```yuho
offence o:entry rule r:entry program p:entry path entry {
  element conduct f:entry quote q:entry;
  element circumstance f:no-authorization quote q:authorization;
  element fault f:knowledge quote q:knowledge;
  all g:offence-requirements (f:entry, f:no-authorization, f:knowledge);
}
exception x:emergency-rescue to o:entry rule r:rescue program p:rescue path rescue {
  element circumstance f:immediate-danger quote q:danger;
  element purpose f:rescue-purpose quote q:rescue;
  all g:emergency-requirements (f:immediate-danger, f:rescue-purpose);
}
```

The fixture is **wholly fictional, non-authoritative and solely for compiler/kernel conformance testing**. Its rule states that restricted-area entry without authorization and with knowledge satisfies synthetic offence requirements; immediate danger to another person plus protective or rescue purpose activates the synthetic exception. Its `outputs` name the offence requirement group, exception group, defeatable branch and final rule; they are checked declarations, not new KernelResult fields. In `SuppliedProofStatus-v1`, the offence requirement trace may be `satisfied` while an applicable exception makes the root branch `not_satisfied` with reason `defeated`. The target exception rule is evaluated when needed; the kernel omits it when root requirements already determine failure. Every evaluated branch has complete child traces. `not_proved` is a supplied classification, not factual falsity. `unresolved` is a technical state, not a court disposition.

`SuppliedProofStatus-v1` is the least existing fragment with both externally supplied three-valued classifications and an `is_infringed` guard that defeats a branch. `AcyclicGuardedExceptions-v1` has the defeating edge but only Boolean facts. Lowering builds two registered rules, five leaves, one exception guard, total synthetic proof statuses and exact UTF-8 byte spans in synthetic source text. Contextual burden annotations, source labels and limitations do not generate facts or alter evaluation. Spans use one-based line and UTF-8 **byte-column** positions. The bundle recipe binds semantic IDs to those bytes; it does not authenticate an authority.

## CLI, diagnostics and packaging

From the repository root:

```sh
python3 -m rewrite.frontend check rewrite/frontend/fixtures/synthetic/restricted_entry.yh
python3 -m rewrite.frontend check rewrite/frontend/fixtures/synthetic/restricted_entry.yh \
  --scenario rewrite/frontend/fixtures/synthetic/scenario_all_proved.yh
python3 -m rewrite.frontend compile rewrite/frontend/fixtures/synthetic/restricted_entry.yh \
  --scenario rewrite/frontend/fixtures/synthetic/scenario_all_proved.yh \
  --output "$FRESH_DIR/request.json"
"$YUHO_KERNEL_BIN" < "$FRESH_DIR/request.json"
python3 - "$FRESH_DIR/request.json" "$FRESH_DIR/bundle" <<'PY'
from pathlib import Path
import sys
from rewrite.frontend import bundle, core

model_path = Path("rewrite/frontend/fixtures/synthetic/restricted_entry.yh")
model = core.parse_synthetic(model_path.read_text(encoding="utf-8"), str(model_path))
print(bundle.build(model, Path(sys.argv[1]).read_bytes(), Path(sys.argv[2])))
PY
"$YUHO_BUNDLE_BIN" validate "$FRESH_DIR/bundle"
```

`compile` writes compact sorted-key UTF-8 KernelInput to stdout with **no newline**, or publishes atomically to an explicit nonexistent output path. `check` emits one canonical JSON status line. Failure emits canonical JSON on stderr with stable code, path, one-based line and byte column; it creates no successful output. Existing SFE001–SFE016 meanings remain for section 84. The synthetic subset adds SFE017 (typed declaration), SFE018 (exception target), SFE019 (cross-rule/type-incompatible reference), SFE020 (output target), and SFE021 (non-fictional authority claim). Unknown syntax, source roles and statuses reject. Inputs are limited to 64 KiB, 4,096 tokens and 256 nodes/assignments. Source is strict UTF-8 and LF only; strings have no escapes. Input symlinks and unsafe output paths reject.

The [synthetic bundle recipe](../../rewrite/frontend/bundle.py) packages the compiled request and two exact synthetic text artifacts into a fresh four-file `ModelBundle-v1`. It is structurally valid, fictional, unsigned and unreviewed. The authored `.yh` file remains outside that bundle; ModelBundle-v1's executable artifact is the complete scenario-bound KernelInput. Its digest is `091cb0f9286dd8dd67cbd686d92a410d7a928fe8fa2d03396821e814ca4976db`. Different scenario assignments change executable bytes and bundle digest. Two fresh builds of the same model and scenario compare byte-for-byte.

The section 84 [authored source](../../research/singapore/section-84-pilot/surface/section84.yh) still uses embedded `proof_assignments` and its locked excerpt. The shared frontend's compatibility path emits its frozen 7,599-byte request, SHA-256 `1ebe4d4fdd3de643e938c512fafd1c68ed437728b1249d32b6a236639a58d6e2`, without a trailing newline. Its reviewed six-file bundle remains `02e51da9fa1bf285eec7cca8b55494c1d6a8e82b9b7e7e300a30b338ecbd404a`. This milestone does not expand or re-review that model.

This v0.1 syntax has no modules, imports, macros, general negation, arbitrary expressions, evidence assessment, dynamic burdens, real-jurisdiction selection, temporal applicability, sentencing, court outcomes or arbitrary multi-rule composition. The [v0.2 synthetic subset](YUHO-SURFACE-V0.2.md) adds bounded exact-version modules and one explicit composition form while preserving these v0.1 bytes. The frontend and kernel produce technical rule results and traces only; they provide no legal advice or judicial disposition.
