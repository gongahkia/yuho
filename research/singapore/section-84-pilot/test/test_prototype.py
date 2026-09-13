"""Focused offline checks for the bounded executable research prototype."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


PILOT = Path(__file__).resolve().parents[1]
PROTOTYPE = PILOT / "prototype"
spec = importlib.util.spec_from_file_location("s84_pilot", PROTOTYPE / "pilot.py")
assert spec and spec.loader
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)
SOURCE = Path(os.environ.get("YUHO_S84_INPUT_DIR", "/missing-s84-source"))
PACKET = Path(os.environ.get("YUHO_S84_PACKET_DIR", "/missing-s84-packet"))
KERNEL = Path(os.environ.get("YUHO_KERNEL_BIN", "/missing-yuho-kernel"))
VALIDATOR = Path(os.environ.get("YUHO_BUNDLE_BIN", "/missing-yuho-model-bundle"))


def kernel(raw: bytes) -> tuple[bytes, dict]:
    result = subprocess.run(
        [str(KERNEL)], input=raw + b"\n", capture_output=True, check=True
    )
    return result.stdout, json.loads(result.stdout)


def validate(directory: Path, *extra: str) -> tuple[int, dict]:
    result = subprocess.run(
        [str(VALIDATOR), "validate", str(directory), *extra],
        capture_output=True,
        check=False,
    )
    return result.returncode, json.loads(result.stdout)


def rewrite_core(directory: Path, mutate) -> None:
    path = directory / "model-bundle.json"
    core = json.loads(path.read_bytes())
    mutate(core)
    path.write_bytes(pilot.canonical(core))


@unittest.skipUnless(
    SOURCE.is_dir() and PACKET.is_dir(), "locked external source packet not configured"
)
class PrototypeArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html, cls.extracted = pilot.locked_inputs(SOURCE, PACKET)
        cls.model, cls.mapping, cls.scope = pilot.verify_committed(cls.extracted)

    def test_review_and_source_boundary(self) -> None:
        record = json.loads((PILOT / "QUALIFIED-REVIEW-RECORD.json").read_bytes())
        self.assertEqual(
            record["review_status"], "qualified_review_confirmed_in_writing"
        )
        self.assertEqual(record["authentication"], "unsigned")
        self.assertEqual(
            record["future_bundle_digest_review_status"],
            "implementation_conformance_review_pending",
        )
        self.assertEqual(
            self.scope["digest_bound_implementation_confirmation"],
            "implementation_conformance_review_pending",
        )
        self.assertEqual(self.scope["anchor_offence"], "absent")
        self.assertTrue(self.scope["technical_result_only"])

    def test_exact_model_mapping_and_spans(self) -> None:
        entries = self.mapping["leaf_mappings"]
        self.assertEqual({row["semantic_id"] for row in entries}, set(pilot.LEAF_QUOTE))
        for row in entries:
            self.assertIn(row["proposition_id"], pilot.LEAF_PROPOSITION.values())
            for item in row["supporting_spans"]:
                start, end = item["start"], item["end"]
                self.assertTrue(0 <= start < end <= len(self.extracted))
                self.extracted[start:end].decode("utf-8", errors="strict")
                self.assertEqual(item, pilot.span(self.extracted, start, end))
        self.assertEqual(
            sorted(pilot.semantic_inventory(self.model["registry"])),
            sorted(
                {row["semantic_id"] for row in entries}
                | {row["semantic_id"] for row in self.mapping["group_mappings"]}
            ),
        )
        self.assertEqual(self.model["fragment"], "SuppliedProofStatus-v1")
        self.assertFalse(self.model["registry"][0]["exceptions"])
        self.assertFalse(self.model["registry"][0]["program"]["penalties"])

    def test_fixture_regeneration_and_canonical_bytes(self) -> None:
        cases = json.loads((PROTOTYPE / "fixtures/CASES.json").read_bytes())["cases"]
        expected = [
            ("X00-unclassified", self.model, "unresolved", ""),
            *[
                (name, item, status, "")
                for name, item, status in pilot.fixtures(self.model)
            ],
            *[
                (name, item, "rejected", code)
                for name, item, code in pilot.rejected_fixtures(self.model)
            ],
        ]
        self.assertEqual(len(cases), 24)
        self.assertEqual(
            cases,
            [
                {"name": name, "status": status, "code": code}
                for name, _, status, code in expected
            ],
        )
        for name, item, _, _ in expected:
            with self.subTest(name=name):
                raw = (PROTOTYPE / "fixtures/requests" / f"{name}.json").read_bytes()
                self.assertEqual(raw, pilot.canonical(item))
                self.assertEqual(json.loads(raw), item)
                self.assertEqual(raw, pilot.canonical(json.loads(raw)))

    @unittest.skipUnless(KERNEL.is_file(), "kernel executable not configured")
    def test_synthetic_scope_guard_and_runner(self) -> None:
        for path in sorted((PROTOTYPE / "fixtures/requests").glob("X*.json")):
            with self.subTest(path=path.name):
                raw = path.read_bytes()
                self.assertEqual(
                    pilot.validate_synthetic_scenario(raw, self.model), json.loads(raw)
                )
        for path in sorted((PROTOTYPE / "fixtures/requests").glob("Y*.json")):
            with self.subTest(path=path.name):
                with self.assertRaises(ValueError):
                    pilot.validate_synthetic_scenario(path.read_bytes(), self.model)
        path = PROTOTYPE / "fixtures/requests/X01-nature.json"
        result = subprocess.run(
            [
                "python3",
                str(PROTOTYPE / "pilot.py"),
                "run-synthetic",
                "--input-dir",
                str(SOURCE),
                "--packet-dir",
                str(PACKET),
                "--request-path",
                str(path),
                "--kernel",
                str(KERNEL),
            ],
            capture_output=True,
            check=True,
        )
        self.assertEqual(
            result.stdout,
            (PROTOTYPE / "fixtures/snapshots/X01-nature.json").read_bytes(),
        )
        self.assertFalse(result.stderr)

    @unittest.skipUnless(KERNEL.is_file(), "kernel executable not configured")
    def test_direct_kernel_snapshots_and_trace(self) -> None:
        cases = json.loads((PROTOTYPE / "fixtures/CASES.json").read_bytes())["cases"]
        for case in cases:
            name = case["name"]
            with self.subTest(name=name):
                raw = (PROTOTYPE / "fixtures/requests" / f"{name}.json").read_bytes()
                output, result = kernel(raw)
                self.assertEqual(
                    output,
                    (PROTOTYPE / "fixtures/snapshots" / f"{name}.json").read_bytes(),
                )
                self.assertEqual(output, pilot.canonical(result, line=True))
                self.assertEqual(result["status"], case["status"])
                self.assertEqual(
                    result["diagnostics"][0]["code"] if result["diagnostics"] else "",
                    case["code"],
                )
                self.assertEqual(result["fragment"], pilot.FRAGMENT)
                self.assertEqual(result["selected_penalties"], [])
                self.assertTrue(
                    {
                        "guilt",
                        "conviction",
                        "acquittal",
                        "sentence",
                        "diagnosis",
                        "fitness",
                        "cpc_disposition",
                    }.isdisjoint(result)
                )
                if result["status"] == "rejected":
                    self.assertEqual(result["rules"], [])
                else:
                    trace = result["rules"][0]["trace"]
                    self.assertEqual(len(trace), 13)
                    observations = result["rules"][0]["proof_observations"]
                    self.assertEqual(len(observations), 8)
                    self.assertEqual(
                        [item["leaf_id"] for item in observations],
                        [item["id"] for item in trace if item["kind"] == "leaf"],
                    )
                    facts = json.loads(raw)["facts"]
                    for observation in observations:
                        self.assertEqual(
                            observation["proof_status"],
                            facts[observation["leaf_id"]]["proof_status"],
                        )
                        self.assertEqual(observation["burden_check"], "matched")
                        self.assertEqual(observation["standard_check"], "matched")

    @unittest.skipUnless(KERNEL.is_file(), "kernel executable not configured")
    def test_persistent_recovery_and_limits(self) -> None:
        valid = (PROTOTYPE / "fixtures/requests/X01-nature.json").read_bytes()
        malformed = b'{"protocol":'
        oversized = b" " * 1048577
        output = subprocess.run(
            [str(KERNEL)],
            input=malformed + b"\n" + valid + b"\n" + oversized + b"\n" + valid + b"\n",
            capture_output=True,
            check=True,
        ).stdout.splitlines()
        self.assertEqual(len(output), 4)
        statuses = [json.loads(line)["status"] for line in output]
        self.assertEqual(statuses, ["rejected", "satisfied", "rejected", "satisfied"])

    @unittest.skipUnless(VALIDATOR.is_file(), "bundle validator not configured")
    def test_double_bundle_build(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuho-s84-double-") as folder:
            root = Path(folder)
            first, second = root / "first", root / "second"
            digest_a = pilot.build_bundle(SOURCE, PACKET, first, VALIDATOR)
            digest_b = pilot.build_bundle(SOURCE, PACKET, second, VALIDATOR)
            self.assertEqual(digest_a, digest_b)
            names_a = sorted(
                str(path.relative_to(first))
                for path in first.rglob("*")
                if path.is_file()
            )
            names_b = sorted(
                str(path.relative_to(second))
                for path in second.rglob("*")
                if path.is_file()
            )
            self.assertEqual(names_a, names_b)
            for name in names_a:
                self.assertEqual(
                    (first / name).read_bytes(), (second / name).read_bytes()
                )
            for directory in (first, second):
                code, result = validate(directory)
                self.assertEqual(
                    (code, result["status"], result["bundle_digest"]),
                    (0, "valid", digest_a),
                )
                self.assertEqual(result["review_authentication"], "none")
                self.assertEqual(result["applicable_asserted_reviews"], [])

    @unittest.skipUnless(VALIDATOR.is_file(), "bundle validator not configured")
    def test_negative_bundle_validation_and_review_nontransfer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuho-s84-negative-") as folder:
            root = Path(folder)
            original = root / "original"
            digest = pilot.build_bundle(SOURCE, PACKET, original, VALIDATOR)
            core = json.loads((original / "model-bundle.json").read_bytes())
            artifacts = original / "artifacts/sha256"
            model_digest = core["executable_model"]["artifact_digest"]
            excerpt_digest = self.model["sources"][0]["sha256"]
            html_digest = pilot.sha(self.html)

            def case(name, mutation, expected_code):
                directory = root / name
                shutil.copytree(original, directory)
                mutation(directory)
                code, result = validate(directory)
                self.assertEqual(code, 1, name)
                self.assertEqual(result["status"], "invalid", name)
                self.assertEqual(result["diagnostics"][0]["code"], expected_code, name)

            case(
                "changed-source",
                lambda d: (d / "artifacts/sha256" / html_digest).write_bytes(
                    bytes([self.html[0] ^ 1]) + self.html[1:]
                ),
                "MBINV001",
            )
            model_bytes = (artifacts / model_digest).read_bytes()
            case(
                "changed-model",
                lambda d: (d / "artifacts/sha256" / model_digest).write_bytes(
                    bytes([model_bytes[0] ^ 1]) + model_bytes[1:]
                ),
                "MBINV001",
            )
            case(
                "missing-source",
                lambda d: (d / "artifacts/sha256" / html_digest).unlink(),
                "MBPKG001",
            )
            case(
                "missing-model",
                lambda d: (d / "artifacts/sha256" / model_digest).unlink(),
                "MBPKG001",
            )
            case(
                "incorrect-span",
                lambda d: rewrite_core(
                    d, lambda c: c["semantic_mappings"][0]["span"].update(end=999999)
                ),
                "MBINV001",
            )
            case(
                "unknown-artifact",
                lambda d: (d / "artifacts/sha256" / ("a" * 64)).write_bytes(
                    b"unexpected"
                ),
                "MBPKG001",
            )
            case(
                "extra-file",
                lambda d: (d / "unexpected").write_bytes(b"unexpected"),
                "MBPKG001",
            )

            def symlink(d):
                path = d / "artifacts/sha256" / excerpt_digest
                path.unlink()
                path.symlink_to(artifacts / excerpt_digest)

            case("symlink", symlink, "MBPKG001")
            case(
                "malformed-manifest",
                lambda d: (d / "model-bundle.json").write_bytes(b'{"schema":'),
                "MBDEC001",
            )
            case(
                "digest-mismatch",
                lambda d: rewrite_core(
                    d, lambda c: c["artifacts"][0].update(byte_length=12345)
                ),
                "MBINV001",
            )
            case(
                "scope-mismatch",
                lambda d: rewrite_core(d, lambda c: c["scope"]["semantic_ids"].pop()),
                "MBINV001",
            )

            def bad_review(d):
                review = copy.deepcopy(
                    json.loads(
                        (
                            PILOT.parents[2]
                            / "rewrite/haskell/test/model-bundle-fixtures/bundles/MB02-review"
                            / "reviews/review:1.json"
                        ).read_bytes()
                    )
                )
                review["bundle_digest"] = "c057fb84000265b412d1b6ca3d050e7b2a1d5eca"
                (d / "reviews").mkdir()
                (d / "reviews/review:1.json").write_bytes(pilot.canonical(review))

            case("baseline-is-not-bundle-digest", bad_review, "MBINV001")

            stale = root / "stale-review"
            shutil.copytree(original, stale)
            stale_review = json.loads(
                (
                    PILOT.parents[2]
                    / "rewrite/haskell/test/model-bundle-fixtures/bundles/MB02-review"
                    / "reviews/review:1.json"
                ).read_bytes()
            )
            stale_review["bundle_digest"] = "0" * 64
            stale_review["scope_digest"] = "0" * 64
            stale_review["coverage"]["scope_digest"] = "0" * 64
            (stale / "reviews").mkdir()
            (stale / "reviews/review:1.json").write_bytes(pilot.canonical(stale_review))
            code, result = validate(
                stale, "--require-asserted-review-purpose", "semantic_fidelity"
            )
            self.assertEqual(
                (code, result["status"], result["bundle_digest"]),
                (3, "policy_unmet", digest),
            )
            self.assertEqual(result["stale_reviews"], ["review:1"])

            # Invalid UTF-8 in a remapped source text must fail after hash checks.
            invalid_utf8 = root / "invalid-utf8"
            shutil.copytree(original, invalid_utf8)
            invalid_core = copy.deepcopy(core)
            old = pilot.sha(self.extracted)
            replacement = b"\xff" + self.extracted[1:]
            new = pilot.sha(replacement)
            (invalid_utf8 / "artifacts/sha256" / old).unlink()
            (invalid_utf8 / "artifacts/sha256" / new).write_bytes(replacement)
            for item in invalid_core["artifacts"]:
                if item["sha256"] == old:
                    item["sha256"] = new
            invalid_core["artifacts"].sort(key=lambda item: item["sha256"])
            for item in invalid_core["legal_sources"]:
                if item["artifact_digest"] == old:
                    item["artifact_digest"] = new
            for item in invalid_core["semantic_mappings"]:
                if item["artifact_digest"] == old:
                    item["artifact_digest"] = new
            for item in invalid_core["derivations"]:
                for key in ("child_digest", "parent_digest"):
                    if item[key] == old:
                        item[key] = new
            invalid_core["derivations"].sort(
                key=lambda item: (item["child_digest"], item["parent_digest"])
            )
            (invalid_utf8 / "model-bundle.json").write_bytes(
                pilot.canonical(invalid_core)
            )
            code, result = validate(invalid_utf8)
            self.assertEqual((code, result["status"]), (1, "invalid"))
            self.assertIn("not UTF-8", result["diagnostics"][0]["message"])

    @unittest.skipUnless(VALIDATOR.is_file(), "bundle validator not configured")
    def test_failed_build_leaves_no_destination(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuho-s84-failed-build-") as folder:
            root = Path(folder)
            source = root / "source"
            source.mkdir()
            for row in json.loads((PILOT / "SOURCE-LOCK.json").read_bytes())["sources"]:
                shutil.copy2(
                    SOURCE / row["original_filename"], source / row["original_filename"]
                )
            destination = root / "output"
            html = source / pilot.HTML_NAME
            original = html.read_bytes()
            html.write_bytes(bytes([original[0] ^ 1]) + original[1:])
            with self.assertRaisesRegex(ValueError, "source lock mismatch"):
                pilot.build_bundle(source, PACKET, destination, VALIDATOR)
            self.assertFalse(destination.exists())
            html.write_bytes(original)
            html.unlink()
            html.symlink_to(SOURCE / pilot.HTML_NAME)
            with self.assertRaisesRegex(ValueError, "expected regular file"):
                pilot.build_bundle(source, PACKET, destination, VALIDATOR)
            self.assertFalse(destination.exists())
            html.unlink()
            html.write_bytes(b"0" * (8 * 1024 * 1024 + 1))
            with self.assertRaisesRegex(ValueError, "input limit exceeded"):
                pilot.build_bundle(source, PACKET, destination, VALIDATOR)
            self.assertFalse(destination.exists())

    def test_pilot_model_identity_and_scope_reject_mutation(self) -> None:
        for key, changed in (("model_id", "other"), ("model_version", "v2")):
            with self.subTest(key=key):
                altered = copy.deepcopy(self.scope)
                altered[key] = changed
                with self.assertRaisesRegex(ValueError, "model scope differs"):
                    pilot.bundle_core(
                        self.model, self.mapping, altered, self.html, self.extracted
                    )

    def test_atomic_publish_does_not_replace_existing_directory(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuho-s84-no-replace-") as folder:
            old, new = Path(folder) / "old", Path(folder) / "new"
            old.mkdir()
            new.mkdir()
            (old / "task.txt").write_text("task")
            (new / "user.txt").write_text("user")
            with self.assertRaises(FileExistsError):
                pilot.rename_without_replace(old, new)
            self.assertEqual((new / "user.txt").read_text(), "user")
            self.assertEqual((old / "task.txt").read_text(), "task")


if __name__ == "__main__":
    unittest.main()
