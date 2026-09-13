"""Checks the unsigned confirmation against its exact implementation baseline."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import unittest


PILOT = Path(__file__).resolve().parents[1]
ROOT = PILOT.parents[2]
BASELINE = "bd36402a1a9ba5cfef6ef36d1b0ba0dd999a3a74"
RESEARCH_BASELINE = "c057fb84000265b412d1b6ca3d050e7b2a1d5eca"
REVIEW_COMMIT = "7978903c969a2e6d2974c883a083c236e016ca11"
DIGEST = "02e51da9fa1bf285eec7cca8b55494c1d6a8e82b9b7e7e300a30b338ecbd404a"
MODEL_ID = "SingaporePenalCodeSection84Post2022ResearchPrototype-v1"
RECORD = PILOT / "IMPLEMENTATION-CONFORMANCE-RECORD.json"
SOURCE = Path(os.environ.get("YUHO_S84_INPUT_DIR", "/missing-s84-source"))
PACKET = Path(os.environ.get("YUHO_S84_PACKET_DIR", "/missing-s84-packet"))
CONFIRMATION = (
    "Confirmed. The implementation represented by ModelBundle digest "
    f"{DIGEST} conforms to the reviewed section 84 research structure and its "
    "documented research-prototype limitations."
)


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


class ImplementationConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        raw = RECORD.read_bytes()
        cls.record = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
        canonical = (
            json.dumps(
                cls.record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
            + b"\n"
        )
        assert raw == canonical

    def test_exact_unsigned_confirmation_and_scope(self) -> None:
        record = self.record
        self.assertEqual(
            record["schema"], "yuho.sg-section-84-implementation-conformance-record/v1"
        )
        self.assertEqual(
            record["review_status"], "implementation_conformance_confirmed_in_writing"
        )
        self.assertEqual(record["confirmation_text"], CONFIRMATION)
        self.assertEqual(record["model_id"], MODEL_ID)
        self.assertEqual(record["bundle_digest"], DIGEST)
        self.assertEqual(record["implementation_baseline_commit"], BASELINE)
        self.assertEqual(
            record["underlying_research_baseline_commit"], RESEARCH_BASELINE
        )
        self.assertEqual(record["authentication"], "unsigned")
        self.assertIs(record["digital_signature_present"], False)
        self.assertEqual(record["reviewer_identity_disclosure"], "withheld")
        self.assertEqual(
            record["scope_classification"],
            "bounded_research_prototype_subject_to_documented_limitations",
        )
        self.assertEqual(
            record["assertion_basis"], "maintainer_supplied_written_confirmation"
        )
        self.assertEqual(record["underlying_evidence_digest"], {"kind": "unavailable"})
        self.assertEqual(
            record["underlying_evidence_retention"], "external_to_repository"
        )
        self.assertNotIn("reviewer_name", record)
        self.assertNotIn("signature", record)
        self.assertNotIn("reviewed_at", record)

    def test_prior_review_reference_and_baseline_artifact_hashes(self) -> None:
        record = self.record
        prior = record["prior_qualified_review_record"]
        self.assertEqual(
            prior,
            {
                "commit": REVIEW_COMMIT,
                "path": "research/singapore/section-84-pilot/QUALIFIED-REVIEW-RECORD.json",
            },
        )
        prior_bytes = subprocess.run(
            ["git", "show", f"{REVIEW_COMMIT}:{prior['path']}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        self.assertEqual((ROOT / prior["path"]).read_bytes(), prior_bytes)
        self.assertEqual(
            json.loads(prior_bytes)["reviewed_baseline_commit"], RESEARCH_BASELINE
        )
        self.assertIn("maintainer_attested", record["qualification_basis"])
        artifacts = record["implementation_baseline_artifacts"]
        paths = [item["path"] for item in artifacts]
        self.assertEqual(paths, sorted(set(paths)))
        self.assertEqual(
            set(paths),
            {
                "docs/rewrite/SINGAPORE-SECTION-84-EXECUTABLE-RESEARCH-PROTOTYPE.md",
                "research/singapore/section-84-pilot/prototype/fixtures/CASES.json",
                "research/singapore/section-84-pilot/prototype/mapping.json",
                "research/singapore/section-84-pilot/prototype/pilot.py",
                "research/singapore/section-84-pilot/prototype/request.json",
                "research/singapore/section-84-pilot/prototype/scope.json",
            },
        )
        for item in artifacts:
            self.assertFalse(Path(item["path"]).is_absolute())
            self.assertNotIn("..", Path(item["path"]).parts)
            baseline_bytes = subprocess.run(
                ["git", "show", f"{BASELINE}:{item['path']}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            ).stdout
            self.assertEqual(hashlib.sha256(baseline_bytes).hexdigest(), item["sha256"])
        self.assertIn(
            "distinct from the ModelBundle core digest", record["artifact_hash_meaning"]
        )

    def test_exact_digest_binding_without_transfer(self) -> None:
        record = self.record
        scope = json.loads((PILOT / "prototype/scope.json").read_bytes())
        model = json.loads((PILOT / "prototype/request.json").read_bytes())
        self.assertEqual(scope["model_id"], record["model_id"])
        self.assertEqual(model["fragment"], "SuppliedProofStatus-v1")
        self.assertEqual(
            scope["digest_bound_implementation_confirmation"],
            "implementation_conformance_review_pending",
        )
        self.assertTrue(record["bundle_digest"] == DIGEST)
        different_digest = hashlib.sha256(b"rebuilt ModelBundle core").hexdigest()
        self.assertNotEqual(different_digest, DIGEST)
        self.assertFalse(record["bundle_digest"] == different_digest)
        self.assertIn(
            "any different bundle digest requires a new", record["digest_transfer_rule"]
        )

    @unittest.skipUnless(
        SOURCE.is_dir() and PACKET.is_dir(),
        "locked external source packet not configured",
    )
    def test_rebuilt_core_digest_does_not_inherit_confirmation(self) -> None:
        spec = importlib.util.spec_from_file_location(
            "s84_pilot_conformance", PILOT / "prototype/pilot.py"
        )
        assert spec and spec.loader
        pilot = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pilot)
        html, extracted = pilot.locked_inputs(SOURCE, PACKET)
        model, mapping, scope = pilot.verify_committed(extracted)
        core, _ = pilot.bundle_core(model, mapping, scope, html, extracted)
        self.assertEqual(pilot.sha(pilot.DOMAIN + pilot.canonical(core)), DIGEST)
        core["scope"]["limitations"].append("Changed limitation for binding test")
        core["scope"]["limitations"].sort()
        rebuilt_digest = pilot.sha(pilot.DOMAIN + pilot.canonical(core))
        self.assertNotEqual(rebuilt_digest, DIGEST)
        self.assertNotEqual(self.record["bundle_digest"], rebuilt_digest)

    def test_limitations_and_prohibited_claims(self) -> None:
        record = self.record
        self.assertEqual(
            record["limitations_incorporated_by_reference"],
            [
                "docs/rewrite/SINGAPORE-SECTION-84-EXECUTABLE-RESEARCH-PROTOTYPE.md",
                "research/singapore/section-84-pilot/prototype/scope.json",
            ],
        )
        for path in record["limitations_incorporated_by_reference"]:
            self.assertTrue((ROOT / path).is_file())
        non_claims = " ".join(record["non_claims"]).lower()
        for term in (
            "source authentication",
            "legal currency",
            "evidence assessment",
            "diagnosis",
            "guilt",
            "conviction",
            "acquittal",
            "sentencing",
            "fitness-to-plead",
            "court disposition",
        ):
            self.assertIn(term, non_claims)
        self.assertNotIn("review_authentication", record)
        self.assertNotIn("reviewer_verified", record)


if __name__ == "__main__":
    unittest.main()
