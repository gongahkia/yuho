"""Serial clean-directory build/install replay using only the pinned Cabal cache."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="yuho-kernel-replay-") as temporary:
        clean = Path(temporary)
        for name in ("cabal.project", "cabal.project.freeze", "yuho-foundation.cabal"):
            shutil.copy2(WORKSPACE / name, clean / name)
        for name in ("src", "app", "test"):
            shutil.copytree(WORKSPACE / name, clean / name, symlinks=True)
        binary_dir = clean / "bin"
        binary_dir.mkdir()
        subprocess.run(["cabal", "v2-build", "exe:yuho-kernel", "exe:yuho-model-bundle",
                        "--offline", "--jobs=1"],
                       cwd=clean, check=True)
        subprocess.run(["cabal", "v2-install", "exe:yuho-kernel", "--offline",
                        "--jobs=1", f"--installdir={binary_dir}",
                        "--overwrite-policy=always"], cwd=clean, check=True)
        binary = binary_dir / "yuho-kernel"
        subprocess.run(["cabal", "v2-install", "exe:yuho-model-bundle", "--offline",
                        "--jobs=1", f"--installdir={binary_dir}",
                        "--overwrite-policy=always"], cwd=clean, check=True)
        bundle_binary = binary_dir / "yuho-model-bundle"
        bundle_fixtures = WORKSPACE / "test/model-bundle-fixtures/bundles"
        for name, expected_exit, status in (
            ("MB01-minimal", 0, "valid"),
            ("MB09-length-mismatch", 1, "invalid"),
            ("MB18-derivation-cycle", 1, "invalid"),
            ("MB31-oversize-manifest", 1, "invalid"),
        ):
            completed = subprocess.run([str(bundle_binary), "validate",
                                        str(bundle_fixtures / name)],
                                       capture_output=True, timeout=30)
            assert completed.returncode == expected_exit, (name, completed.stdout)
            assert json.loads(completed.stdout)["status"] == status, name
        unmet = subprocess.run([str(bundle_binary), "validate",
                                str(bundle_fixtures / "MB03-unmet-policy"),
                                "--require-asserted-review-purpose", "source_fidelity"],
                               capture_output=True, timeout=30)
        assert unmet.returncode == 3
        assert json.loads(unmet.stdout)["status"] == "policy_unmet"
        missing = subprocess.run([str(bundle_binary), "validate", str(clean / "absent")],
                                 capture_output=True, timeout=30)
        assert missing.returncode == 2
        assert json.loads(missing.stdout)["status"] == "io_error"
        diff_fixtures = WORKSPACE / "test/model-bundle-diff-fixtures"
        compared = subprocess.run([str(bundle_binary), "diff",
                                   str(diff_fixtures / "bundles/DX01-base"),
                                   str(diff_fixtures / "bundles/DX03-source-metadata")],
                                  capture_output=True, timeout=30)
        assert compared.returncode == 0 and not compared.stderr
        assert compared.stdout == (diff_fixtures / "snapshots/DC03-metadata.json").read_bytes()
        refused = subprocess.run([str(bundle_binary), "diff",
                                  str(bundle_fixtures / "MB08-unknown-field"),
                                  str(diff_fixtures / "bundles/DX01-base")],
                                 capture_output=True, timeout=30)
        assert refused.returncode == 1 and not refused.stdout
        assert json.loads(refused.stderr)["diagnostics"][0]["code"] == "MBDEC001"
        fixtures = WORKSPACE / "test/typed-fixtures/requests"
        for name, status, code in (("T17.json", "false", ""),
                                   ("T49.txt", "rejected", "KDEC002")):
            completed = subprocess.run([str(binary)], input=(fixtures / name).read_bytes(),
                                       capture_output=True, check=True, timeout=30)
            assert not completed.stderr, completed.stderr
            result = json.loads(completed.stdout)
            assert result["status"] == status, name
            assert (result["diagnostics"][0]["code"] if result["diagnostics"] else "") == code
            if name == "T17.json":
                assert result["rules"][0]["branches"][0]["reason"] == "defeated"
        fixtures = WORKSPACE / "test/penalty-fixtures/requests"
        for name, status, code in (("GP13.json", "true", ""),
                                   ("GP39.json", "rejected", "KDEC002")):
            completed = subprocess.run([str(binary)], input=(fixtures / name).read_bytes(),
                                       capture_output=True, check=True, timeout=30)
            assert not completed.stderr, completed.stderr
            result = json.loads(completed.stdout)
            assert result["status"] == status, name
            assert (result["diagnostics"][0]["code"] if result["diagnostics"] else "") == code
            if name == "GP13.json":
                assert [item["penalty_id"] for item in result["selected_penalties"]] == [
                    "pen:one", "pen:two"]
                assert [item["code"] for item in result["selection_warnings"]] == ["KSEL001"]
        fixtures = WORKSPACE / "test/term-fixtures/requests"
        for name, status, code in (("PT03.json", "true", ""),
                                   ("PT66.txt", "rejected", "KDEC002")):
            completed = subprocess.run([str(binary)], input=(fixtures / name).read_bytes(),
                                       capture_output=True, check=True, timeout=30)
            assert not completed.stderr, completed.stderr
            result = json.loads(completed.stdout)
            assert result["status"] == status, name
            assert (result["diagnostics"][0]["code"] if result["diagnostics"] else "") == code
            if name == "PT03.json":
                assert result["selected_penalties"][0]["term"]["minimum"] == {
                    "kind": "specified", "value": "1.20"}
        fixtures = WORKSPACE / "test/proof-fixtures/requests"
        for name, status, code in (("PS31.json", "not_satisfied", ""),
                                   ("PS33.json", "satisfied", ""),
                                   ("PS45.json", "rejected", "KINV010"),
                                   ("PS65.txt", "rejected", "KDEC002")):
            completed = subprocess.run([str(binary)], input=(fixtures / name).read_bytes(),
                                       capture_output=True, check=True, timeout=30)
            assert not completed.stderr, completed.stderr
            result = json.loads(completed.stdout)
            assert result["status"] == status, name
            assert (result["diagnostics"][0]["code"] if result["diagnostics"] else "") == code
            if name == "PS33.json":
                assert result["penalty_selection_trace"][0]["result"] == "guard_unresolved"
        fixtures = WORKSPACE / "test/presumption-fixtures/requests"
        for name, status, code in (("RD01.json", "satisfied", ""),
                                   ("RD08.json", "satisfied", ""),
                                   ("RD36.json", "satisfied", ""),
                                   ("RD46.json", "rejected", "KINV005"),
                                   ("RD59.json", "rejected", "KINV006"),
                                   ("RD73.txt", "rejected", "KDEC002")):
            completed = subprocess.run([str(binary)], input=(fixtures / name).read_bytes(),
                                       capture_output=True, check=True, timeout=30)
            assert not completed.stderr, completed.stderr
            result = json.loads(completed.stdout)
            assert result["status"] == status, name
            assert (result["diagnostics"][0]["code"] if result["diagnostics"] else "") == code
            if name == "RD36.json":
                assert [row["state"] for row in result["presumption_derivations"]] == [
                    "active", "active", "active"]
    print("clean offline build/install of kernel and bundle validator, prior launches, MB validation and change-set diff passed")


if __name__ == "__main__":
    main()
