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
            shutil.copytree(WORKSPACE / name, clean / name)
        binary_dir = clean / "bin"
        binary_dir.mkdir()
        subprocess.run(["cabal", "v2-build", "exe:yuho-kernel", "--offline", "--jobs=1"],
                       cwd=clean, check=True)
        subprocess.run(["cabal", "v2-install", "exe:yuho-kernel", "--offline",
                        "--jobs=1", f"--installdir={binary_dir}",
                        "--overwrite-policy=always"], cwd=clean, check=True)
        binary = binary_dir / "yuho-kernel"
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
    print("clean offline build/install and T17/T49/GP13/GP39/PT03/PT66/PS31/PS33/PS45/PS65 installed launches passed")


if __name__ == "__main__":
    main()
