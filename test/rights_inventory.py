"""Actual CLI regressions for evidence preservation, references and completeness."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rights", ROOT / "scripts/rights_inventory.py")
rights = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rights)
# Exact independent 03 retest input. The extra scope is explicitly a synthetic
# preservation question, not a claim of a newly discovered quotation in s161.
ORIGINAL_ROUNDTRIP = {'rows': [{'repository_path': 'library/penal_code/s161_public_servant_taking_gratification_other/illustrations.yh', 'origin': 'current checkout', 'content_type': 'yh', 'sha256': '47b787e486608d82f0ccd83277363d7699078defa0c41dc016e2ec19e11d121e', 'symlink_target': None, 'classification': 'Mixed content; see per-content evidence and permission scopes', 'source_and_acquisition_provenance': 'Repository-authored implementation/configuration/synthetic fixture or commentary; originality not independently authenticated', 'source_urls': [], 'known_or_claimed_rights_holder': 'Authorised original rights holders; no blanket contributor assignment established', 'license_or_permission': 'Approved Apache-2.0 for authorised original portions only', 'evidence_locations': ['docs/owner-authorisation.md', 'release/owner-apache-authorisation.json', 'independent-review:rights-inventory.json#library/penal_code/s161_public_servant_taking_gratification_other/illustrations.yh'], 'release_surfaces': {'A_public_tree': 'present at observed public baseline b3a8ebcb; local candidate updates assessed separately', 'B_sdk_archive': False, 'C_full_bundle': True, 'D_git_or_previous_artifacts': True}, 'technically_required': {'sdk': False, 'full_research': True}, 'synthetic_or_original_replacement': 'Not needed for original implementation; synthetic technical fixtures possible', 'clearance_status': 'Conditional or unresolved portions remain; no full-file clearance', 'recommended_disposition': 'Retain original scope and notices; review any actual contributor claim separately', 'owner_decision_required': 'No new licence choice; resolve any actual third-party/contributor authority question', 'verification_after_disposition': 'Unchanged semantic bytes, full research gate; extracted-package proof for included SDK resources', 'previous_classification': 'Original and covered by approved Apache-2.0', 'rights_scopes': [{'category': 'original', 'content_locator': 'authored code/representation/analysis only; external portions separately scoped', 'source_reference': 'release/owner-apache-authorisation.json', 'evidence': 'retained owner grant for authorised original portions', 'status': 'not proof of universal ownership or full-file clearance'}, {'category': 'conditional_legislation', 'content_locator': 'statutory illustration string bodies; original comments/representation separately scoped', 'source_reference': 'library/penal_code/_raw/act.json#section=161', 'evidence': 'independent rights retest: matrix-classification-challenges.json / legislative-lexical-challenges.json', 'status': 'Lexical matches identify source-review candidates, not ownership, protectability, accuracy or permission; no quotation copied into this policy'}, {'category': 'unresolved', 'content_locator': 'additional independently identified nonlegislative excerpt, lines 1-2', 'source_reference': 'unknown third-party source', 'evidence': 'independent retest preservation fixture', 'status': 'unresolved; no grant'}], 'fully_cleared': False}]}


def main():
    policy = rights.load_policy()
    registry = rights.authoritative(policy)
    target = rights.key(ORIGINAL_ROUNDTRIP["rows"][0])
    legacy_extra = ORIGINAL_ROUNDTRIP["rows"][0]["rights_scopes"][-1]
    assert legacy_extra == rights.scope("unresolved",
        "additional independently identified nonlegislative excerpt, lines 1-2",
        "unknown third-party source", "independent retest preservation fixture", "unresolved; no grant")
    approval = json.loads((ROOT / "release/owner-apache-authorisation.json").read_bytes())
    assert approval["mascot_owner_statement"]["license_approval"]["answer"] == "Apply Apache-2.0 to the four mascot files"
    raw = {"rows": [{"origin": origin, "repository_path": path, "sha256": record["sha256"],
                       "classification": rights.UNRESOLVED} for (origin, path), record in registry.items()]}
    raw["rows"] += [
        {"origin": "permanent synthetic fixture", "repository_path": "original.hs", "sha256": "0" * 64,
         "classification": rights.ORIGINAL, "source_and_acquisition_provenance": "original implementation",
         "evidence_locations": ["explicit original-scope fixture"]},
        {"origin": "permanent synthetic fixture", "repository_path": "unknown.md", "sha256": "0" * 64,
         "classification": rights.ORIGINAL}]
    positive = rights.refine(raw, policy)
    unknown = next(r for r in positive["rows"] if r["repository_path"] == "unknown.md")
    assert unknown["classification"] == rights.UNRESOLVED
    assert unknown["rights_scopes"][0]["source_reference"] == "unknown"
    pure = next(r for r in positive["rows"] if r["repository_path"] == "original.hs")
    assert pure["classification"] == rights.ORIGINAL
    assert len(policy["challenged_original_files"]) == 374
    assert all(next(r for r in positive["rows"] if rights.key(r) == (c["origin"], c["path"]))["classification"] == rights.MIXED
               for c in policy["challenged_original_files"])
    assert all(next(r for r in positive["rows"] if rights.key(r) == (a["origin"], a["path"]))["classification"] == rights.ORIGINAL
               for a in policy["original_assets"])
    with tempfile.TemporaryDirectory(prefix="yuho-rights-scopes-") as folder:
        work = Path(folder)
        calls = 0

        def cli(label, document, flags=(), expected=0, diagnostic=None, tool=None, source_root=ROOT):
            nonlocal calls
            calls += 1
            source = work / (label + ".input.json")
            output = work / (label + ".output.json")
            source.write_bytes(rights.encoded(document))
            command = [sys.executable, str(tool or ROOT / "scripts/rights_inventory.py"),
                       "--input", str(source), "--root", str(source_root), *flags]
            if "--validate-only" not in flags:
                command += ["--output", str(output)]
            original_input = source.read_bytes()
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            assert (result.returncode == 0) == (expected == 0), (label, result.stdout, result.stderr)
            if diagnostic:
                assert diagnostic in result.stdout + result.stderr, (label, result.stdout, result.stderr)
            assert source.read_bytes() == original_input, label
            if expected:
                assert not output.exists(), (label, "failed generation wrote output")
            return json.loads(output.read_bytes()) if output.exists() else None

        def activate(proposed, name):
            # Deliberate reviewed-input/pin activation in a disposable copy only.
            directory = work / name
            (directory / "scripts").mkdir(parents=True)
            (directory / "release").mkdir()
            data = rights.encoded(proposed)
            (directory / "release/rights-content-evidence.json").write_bytes(data)
            code = (ROOT / "scripts/rights_inventory.py").read_text()
            code = re.sub(r'POLICY_SHA256 = "[a-f0-9]+"',
                          'POLICY_SHA256 = "' + hashlib.sha256(data).hexdigest() + '"', code)
            path = directory / "scripts/rights_inventory.py"
            path.write_text(code)
            return path

        cli("existing-reviewed-full", positive, ["--validate-only"])
        cli("legacy-unrecorded-conflict", ORIGINAL_ROUNDTRIP, ["--partial"], 1, "unrecorded scope")
        evidence_input = work / "self-overwrite.input.json"
        evidence_input.write_bytes(rights.encoded(ORIGINAL_ROUNDTRIP))
        saved_evidence = evidence_input.read_bytes()
        rejected = subprocess.run([sys.executable, str(ROOT / "scripts/rights_inventory.py"),
            "--input", str(evidence_input), "--root", str(ROOT), "--record-unresolved", "--output", str(evidence_input)],
            cwd=ROOT, capture_output=True, text=True)
        calls += 1
        assert rejected.returncode != 0 and "must not overwrite" in rejected.stderr
        assert evidence_input.read_bytes() == saved_evidence
        proposed = cli("record-original-review", ORIGINAL_ROUNDTRIP, ["--record-unresolved"])
        record = proposed["additional_reviewed_scopes"][-1]
        assert record["scope"] == legacy_extra and (record["origin"], record["path"]) == target
        tool = activate(proposed, "review-one")
        first = cli("roundtrip-one", ORIGINAL_ROUNDTRIP, ["--partial"], tool=tool)
        second = cli("roundtrip-two", first, ["--partial"], tool=tool)
        assert rights.encoded(first) == rights.encoded(second)
        extra = next(s for s in first["rows"][0]["rights_scopes"] if s["evidence"] == legacy_extra["evidence"])
        assert rights.body(extra) == legacy_extra
        assert extra["scope_id"] == rights.identity(target, record["review_key"])
        cli("roundtrip-validate", first, ["--partial", "--validate-only"], tool=tool)
        # The original three-scope fixture remains unchanged; a second question has
        # a separate supplied locator/evidence and therefore a separate identity.
        multiple = copy.deepcopy(first)
        second_extra = rights.scope("unresolved", "second synthetic preservation question; no actual excerpt alleged",
                                    None, "second independent synthetic fixture", "unresolved; no grant")
        multiple["rows"][0]["rights_scopes"].append(second_extra)
        proposed_two = cli("record-second-review", multiple, ["--record-unresolved"], tool=tool)
        tool_two = activate(proposed_two, "review-two")
        two = cli("multiple-unresolved", multiple, ["--partial"], tool=tool_two)
        assert len(two["rows"][0]["rights_scopes"]) == 4
        ids = [s["scope_id"] for s in two["rows"][0]["rights_scopes"]]
        assert len(set(ids)) == 4 and extra in two["rows"][0]["rights_scopes"]
        again = cli("multiple-repeat", two, ["--partial"], tool=tool_two)
        assert rights.encoded(two) == rights.encoded(again)
        removed = copy.deepcopy(two)
        removed["rows"][0]["rights_scopes"].remove(extra)
        cli("reviewed-scope-removed", removed, ["--partial", "--validate-only"], 1, "omitted", tool_two)
        cli("reviewed-scope-removed-generation", removed, ["--partial"], 1, "omitted", tool_two)
        revised_policy = copy.deepcopy(proposed_two)
        revision = revised_policy["additional_reviewed_scopes"][0]
        revision["scope"]["status"] = "unresolved; explicitly revised synthetic review question"
        revised_tool = activate(revised_policy, "review-revised")
        cli("old-review-conflicts-with-explicit-revision", two, ["--partial"], 1, "correspondence", revised_tool)
        raw_revision = copy.deepcopy(two)
        del raw_revision["rows"][0]["rights_scopes"]
        revised = cli("deliberately-revised-input", raw_revision, ["--partial"], tool=revised_tool)
        changed_scope = next(s for s in revised["rows"][0]["rights_scopes"] if s["scope_id"] == extra["scope_id"])
        assert changed_scope["status"] == revision["scope"]["status"]
        duplicate_policy = copy.deepcopy(proposed_two)
        duplicate_policy["additional_reviewed_scopes"].append(copy.deepcopy(duplicate_policy["additional_reviewed_scopes"][0]))
        duplicate_tool = activate(duplicate_policy, "review-duplicate")
        cli("duplicate-authoritative-scope", two, ["--partial", "--validate-only"], 1, "duplicate authoritative", duplicate_tool)
        # A newly reviewed question on a previously unregistered owner preserves
        # the existing base ID too; owner identity is never an array position.
        pure_document = {"rows": [copy.deepcopy(pure)]}
        pure_document["rows"][0]["rights_scopes"].append(copy.deepcopy(legacy_extra))
        pure_policy = cli("record-new-owner", pure_document, ["--record-unresolved"])
        pure_tool = activate(pure_policy, "review-new-owner")
        pure_result = cli("new-reviewed-owner", pure_document, ["--partial"], tool=pure_tool)
        assert pure["rights_scopes"][0] in pure_result["rows"][0]["rights_scopes"]
        # Unknown legacy evidence is represented explicitly, without a fake URL.
        assert extra["source_reference"] == "unknown third-party source" and extra["reference_namespace"] == "unknown"
        explicit_unknown = cli("unknown-provenance", {"rows": [raw["rows"][-1]]}, ["--partial"])
        cli("unknown-provenance-validate", explicit_unknown, ["--partial", "--validate-only"])
        legacy_unknown = copy.deepcopy(explicit_unknown)
        for value in legacy_unknown["rows"][0]["rights_scopes"]:
            del value["scope_id"]
            del value["reference_namespace"]
        migrated_unknown = cli("legacy-unknown-marker", legacy_unknown, ["--partial"])
        assert migrated_unknown["rows"][0]["rights_scopes"][0]["source_reference"] == "unknown"

        def target_row(document):
            return next(r for r in document["rows"] if rights.key(r) == target)

        def negative(label, edit, diagnostic=None):
            mutated = copy.deepcopy(positive)
            edit(mutated)
            cli(label, mutated, ["--validate-only"], 1, diagnostic)

        def reference(document, value):
            next(s for s in target_row(document)["rights_scopes"] if s["category"] == "conditional_legislation")["source_reference"] = value

        negative("blank-source", lambda d: reference(d, ""), "blank source")
        negative("whitespace-source", lambda d: reference(d, "   "), "blank source")
        negative("unrelated-invented-source", lambda d: reference(d, "unrelated invented source"), "correspondence")
        other = next(c for c in policy["challenged_original_files"] if "#section=165" in c["source_reference"])
        negative("valid-elsewhere-source", lambda d: reference(d, other["source_reference"]), "correspondence")
        negative("wrong-namespace", lambda d: target_row(d)["rights_scopes"][0].update(reference_namespace="unsupported"), "namespace")
        negative("wrong-allowed-namespace", lambda d: target_row(d)["rights_scopes"][0].update(reference_namespace="retained_evidence"), "correspondence")
        negative("wrong-content-locator", lambda d: target_row(d)["rights_scopes"][0].update(content_locator="unrelated content"), "correspondence")
        negative("wrong-evidence-record", lambda d: target_row(d)["rights_scopes"][0].update(evidence="unrelated review"), "correspondence")
        negative("wrong-scope-id", lambda d: target_row(d)["rights_scopes"][0].update(scope_id=rights.identity(target, "wrong")), "correspondence")
        negative("duplicate-scope", lambda d: target_row(d)["rights_scopes"].append(copy.deepcopy(target_row(d)["rights_scopes"][0])), "duplicate scope")
        negative("missing-challenged-row", lambda d: d["rows"].remove(target_row(d)), "required reviewed/challenged row missing")
        negative("duplicate-challenged-row", lambda d: d["rows"].append(copy.deepcopy(target_row(d))), "duplicate rights row")
        negative("same-count-unrelated-row", lambda d: target_row(d).update(repository_path="unrelated-same-count.md"), "required reviewed/challenged row missing")
        negative("wrong-owner", lambda d: target_row(d).update(origin="unrelated origin"), "required reviewed/challenged row missing")
        negative("reviewed-scope-partially-removed", lambda d: target_row(d)["rights_scopes"].pop(), "omitted")
        negative("forged-cleared-row", lambda d: target_row(d).update(fully_cleared=True), "not a clearance")
        negative("legacy-clearance-summary", lambda d: target_row(d).update(clearance_status="Fully cleared"), "summary")
        negative("original-label-over-mixed", lambda d: target_row(d).update(classification=rights.ORIGINAL), "classification")
        for value in [1, "true", None]:
            negative("invalid-clearance-" + str(value), lambda d, v=value: target_row(d).update(fully_cleared=v), "not a clearance")
        negative("public-clearance", lambda d: d.update(public_release_cleared=True), "public release")
        dataset = ("current checkout", "library/_index/sso_acts.json")
        def drift(document):
            row = next(r for r in document["rows"] if rights.key(r) == dataset)
            next(s for s in row["rights_scopes"] if s["category"] == "unresolved")["category"] = "conditional_legislation"
            row["classification"] = rights.classification(row["rights_scopes"])
            row["clearance_status"] = rights.clearance_summary(row["rights_scopes"])
        negative("unresolved-relabeled-conditional", drift, "correspondence")
        cli("partial-not-full", first, ["--validate-only"], 1, "partial inventory", tool)
        # A change/removal of the actual reviewed source is refused. Its evidence
        # remains in both the immutable input and policy; no failed output exists.
        source_copy = work / "source-copy"
        for name in [target[1], policy["source_export"], *policy["reference_attachments"]]:
            path = source_copy / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / name).read_bytes())
        (source_copy / target[1]).write_bytes(b"Changed synthetic content for stale-attachment test\n")
        cli("stale-reviewed-source", two, ["--partial"], 1, "stale/missing reviewed source", tool_two, source_copy)
        (source_copy / target[1]).unlink()
        cli("removed-reviewed-source", two, ["--partial"], 1, "stale/missing reviewed source", tool_two, source_copy)
        (source_copy / target[1]).write_bytes((ROOT / target[1]).read_bytes())
        (source_copy / "release/owner-apache-authorisation.json").write_bytes(b"{}\n")
        cli("stale-approval-reference", two, ["--partial", "--validate-only"], 1, "stale/missing source-reference", tool_two, source_copy)
        conflict_policy = copy.deepcopy(policy)
        synthetic = next(r for r in conflict_policy["synthetic_portions"] if "Cheating.hs" in r["path"])
        synthetic["evidence"] = "conflicting independent record"
        conflict_tool = activate(conflict_policy, "review-conflicting-synthetic")
        cli("conflicting-authored-source-records", positive, ["--validate-only"], 1, "conflicting authored synthetic", conflict_tool)
        # Independent scopes for synthetic text and an explicitly hypothetical
        # permitted excerpt retain distinct categories; no real permission alleged.
        fixture_policy = copy.deepcopy(policy)
        fixture_policy["retained_external_or_unresolved"].append({"origin": "permanent synthetic fixture",
            "path": "synthetic-and-excerpt.md", "sha256": "0" * 64,
            "reviewed_scopes": [{**rights.scope(category, locator, source, "hypothetical fixture only", "separate terms"),
                "review_key": category, "reference_namespace": "retained_evidence"}
                for category, locator, source in [("original", "original structure", "fictional original record"),
                    ("synthetic", "original fictional text", "fictional synthetic record"),
                    ("third_party_permission", "identified external excerpt", "fictional permission record")]]})
        fixture_tool = activate(fixture_policy, "mixed-fixture")
        fixture = cli("synthetic-and-third-party", {"rows": [{"origin": "permanent synthetic fixture",
            "repository_path": "synthetic-and-excerpt.md", "sha256": "0" * 64, "classification": rights.MIXED}]},
            ["--partial"], tool=fixture_tool)
        assert {s["category"] for s in fixture["rows"][0]["rights_scopes"]} == {"original", "synthetic", "third_party_permission"}
        print(f"Rights inventory: {calls} actual CLI cases; original lost scope, multiple stable unresolved reviews, bound sources, complete challenged identities, stale evidence and mascot approvals passed")


if __name__ == "__main__":
    main()
