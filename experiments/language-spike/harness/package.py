"""Build each frozen candidate offline from a clean copy and replay in a clean install dir."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"


def run(name: str) -> dict:
    with tempfile.TemporaryDirectory(prefix=f"yuho-{name}-package-") as tmp:
        target = Path(tmp)
        source = target / "source"
        if name == "haskell":
            shutil.copytree(ROOT / name, source, ignore=shutil.ignore_patterns("dist-newstyle"))
            command = ["cabal", "v2-build", "--offline", "--jobs=1"]
        else:
            shutil.copytree(ROOT / name, source,
                            ignore=shutil.ignore_patterns("*.cmi", "*.cmx", "*.o", "yuho-kernel-ocaml"))
            command = ["make", "all"]
        started = time.perf_counter()
        build = subprocess.run(command, cwd=source, capture_output=True, text=True, timeout=120)
        build_ms = (time.perf_counter() - started) * 1000
        build_log = (f"cwd: clean temporary copy of {name}/\ncommand: {' '.join(command)}\n"
                     f"exit: {build.returncode}\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}")
        (OUT / f"{name.upper()}-BUILD.log").write_text(build_log.rstrip() + "\n")
        if build.returncode:
            raise AssertionError(f"{name} offline build failed; see build log")
        binary = (Path(subprocess.check_output(
            ["cabal", "list-bin", "exe:yuho-kernel-haskell"], cwd=source, text=True
        ).strip()) if name == "haskell" else source / "yuho-kernel-ocaml")
        install = target / "install"
        install.mkdir()
        installed = install / "kernel"
        shutil.copy2(binary, installed)
        replay = {}
        for case in ("B01", "P02"):
            request = (ROOT / f"fixtures/requests/{case}.json").read_bytes()
            expected = (ROOT / f"fixtures/expected/{case}.json").read_bytes()
            result = subprocess.run([str(installed)], input=request, capture_output=True,
                                    cwd=install, timeout=10)
            replay[case] = result.returncode == 0 and result.stdout == expected and not result.stderr
        if not all(replay.values()):
            raise AssertionError(f"{name} clean-directory replay failed: {replay}")
        return {"build_ms": build_ms, "build_command": command, "offline": True,
                "clean_source_copy": True, "clean_install_directory": True,
                "artifact_bytes": installed.stat().st_size,
                "artifact_sha256": hashlib.sha256(installed.read_bytes()).hexdigest(),
                "replay": replay,
                "shared_libraries": subprocess.run(["ldd", str(installed)], capture_output=True,
                                                   text=True).stdout.splitlines()}


if __name__ == "__main__":
    report = {}
    for candidate in ("haskell", "ocaml"):
        print(f"clean offline build: {candidate}", flush=True)
        report[candidate] = run(candidate)
        (OUT / "PACKAGING.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("both clean packages passed", flush=True)
